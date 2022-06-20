#!/usr/bin/env python3
"""
Ageas Reborn

author: jy, nkmtmsys
"""

import os
import re
import math
import numpy as np
import pandas as pd
import ageas.lib as lib
import ageas.tool as tool
import ageas.tool.gem as gem
import ageas.tool.mex as mex
import ageas.tool.json as json
import ageas.tool.gtrd as gtrd
import ageas.tool.biogrid as biogrid
import ageas.tool.transfac as transfac
import ageas.database_setup as db_setup
from ageas.lib.deg_finder import Find
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split


class Setup:
    """
    Storage database related setting variables
    """

    def __init__(self,
                 database_path = None,
                 database_type = 'gem_files',
                 group1_path = 'CT1',
                 group2_path = 'CT2',
                 specie = 'mouse',
                 factor_name_type = 'gene_name',
                 interaction_db = 'biogrid',
                 sliding_window_size = None,
                 sliding_window_stride = None
                ):
        super(Setup, self).__init__()
        # Auto GEM folder finder
        if database_path is None:
            assert os.path.exists(group1_path) and os.path.exists(group2_path)
        elif group1_path is None or group2_path is None:
            if len(os.listdir(database_path)) != 2:
                raise DB_Error('Please specify classes for binary clf')
            else:
                group1_path = os.listdir(database_path)[0]
                group2_path = os.listdir(database_path)[1]

        # Initialization
        self.db_path = database_path
        self.type = database_type
        self.specie = specie
        self.factor_name_type = factor_name_type
        self.interaction_db = interaction_db
        self.sliding_window_size = sliding_window_size
        self.sliding_window_stride = sliding_window_stride
        # Get classes'correspond folder paths
        self.group1_path = self.__cast_path(group1_path)
        self.group2_path = self.__cast_path(group2_path)
        # Perform label encoding
        self.label_transformer = Label_Encode(group1_path, group2_path)
        self.label1 = self.label_transformer.get_label1()
        self.label2 = self.label_transformer.get_label2()

    # make path str for the input class based on data path and folder name
    def __cast_path(self, path):
        # no need to concat if path is already completed
        if self.db_path is None:
            return path
        elif path[0] == '/':
            return self.db_path + path
        else:
            return self.db_path + '/' + path



class Label_Encode:
    """
    Transform labels into ints
    """

    def __init__(self, group1_path, group2_path):
        super(Label_Encode, self).__init__()
        # Initialization
        self.encoder = LabelEncoder().fit([group1_path, group2_path])
        self.transformed_labels = self.encoder.transform(
            [group1_path, group2_path]
        )

    # Perform inverse_transform
    def getOriginLable(self, query):
        return list(self.encoder.inverse_transform(query))

    # As named
    def get_label1(self): return self.transformed_labels[0]
    def get_label2(self): return self.transformed_labels[1]



class Load_GEM:
    """
    Load in GEM data sets
    """
    def __init__(self,
                 database_info,
                 mww_thread = 0.05,
                 log2fc_thread = 0.1,
                 std_value_thread = 100,
                 std_ratio_thread = None
                ):
        super(Load_GEM, self).__init__()
        # Initialization
        self.database_info = database_info

        # Load TF databases based on specie
        specie = db_setup.get_specie_path(__name__, self.database_info.specie)

        # Load TRANSFAC databases
        self.tf_list = transfac.Reader(
            specie + 'Tranfac201803_MotifTFsF.txt',
            self.database_info.factor_name_type
        ).tfs

        # Load interaction database
        if self.database_info.interaction_db == 'gtrd':
            self.interactions = gtrd.Processor(
                specie,
                self.database_info.factor_name_type,
                path = 'wholeGene.js.gz'
            )
        elif self.database_info.interaction_db == 'biogrid':
            assert self.database_info.factor_name_type == 'gene_name'
            self.interactions = biogrid.Processor(specie_path = specie)

        # process file or folder based on database type
        if self.database_info.type == 'gem_folders':
            group1, group2 = self.__process_gem_folder(
                std_value_thread,
                std_ratio_thread
            )
        elif self.database_info.type == 'gem_files':
            group1, group2 = self.__process_gem_file(
                std_value_thread,
                std_ratio_thread
            )
        elif self.database_info.type == 'mex_folders':
            group1, group2 = self.__process_mex_folders(
                std_value_thread,
                std_ratio_thread
            )

        # Normalization
        group1 = self.size_factor_normalization(group1)
        group2 = self.size_factor_normalization(group2)

        # Distribuition Filter if threshod is specified
        if mww_thread is not None or log2fc_thread is not None:
            self.genes = Find(
                group1,
                group2,
                mww_thread = mww_thread,
                log2fc_thread = log2fc_thread
            ).degs
            self.group1 = group1.loc[group1.index.intersection(self.genes)]
            self.group2 = group2.loc[group2.index.intersection(self.genes)]
        else:
            self.genes = group1.index.union(group2.index)
            self.group1 = group1
            self.group2 = group2

    # normalize GEMs with median value
    def size_factor_normalization(self, df):
        # estimate size factor for every sample in GEM(df)
        count_per_cell = np.squeeze(np.asarray(df.sum(axis=0)))
        size_factors=count_per_cell.astype(np.float64)/np.median(count_per_cell)

        # all add 1 if size factor could be 0
        if 0 in size_factors:
            size_factors = [x+1 for x in size_factors]
            
        # divide values by size factors
        for i,j in enumerate(df):
            df[j] = df[j].div(size_factors[i])
        return df

    # Process in expression matrix file (dataframe) scenario
    def __process_gem_file(self, std_value_thread, std_ratio_thread):
        group1 = self.__read_df(
            self.database_info.group1_path,
            std_value_thread,
            std_ratio_thread
        )
        group2 = self.__read_df(
            self.database_info.group2_path,
            std_value_thread,
            std_ratio_thread
        )
        return group1, group2

    # Read in gem file
    def __read_df(self, path, std_value_thread, std_ratio_thread):
        # Decide which seperation mark to use
        if re.search(r'csv', path): sep = ','
        elif re.search(r'txt', path): sep = '\t'
        else: raise lib.Error('Unsupported File Type: ', path)
        # Decide which compression method to use
        if re.search(r'.gz', path): compression = 'gzip'
        else: compression = 'infer'
        df = pd.read_csv(
            path,
            sep = sep,
            compression = compression,
            header = 0,
            index_col = 0
        )
        return tool.STD_Filter(df, std_value_thread, std_ratio_thread)

    # Process in expression matrix file (dataframe) scenario
    def __process_mex_folders(self, std_value_thread, std_ratio_thread):
        group1 = self.__read_mex(
            self.database_info.group1_path,
            std_value_thread,
            std_ratio_thread
        )
        group2 = self.__read_mex(
            self.database_info.group2_path,
            std_value_thread,
            std_ratio_thread
        )
        return group1, group2

    # Read in gem files
    def __read_mex(self, path, std_value_thread, std_ratio_thread):
        keyword = None
        matrix_path = None
        features_path = None
        barcodes_path = None
        # get gene id type
        if self.database_info.factor_name_type == 'gene_name':
            gene_id_type = 1
        else:
            print('Under Construction')

        # check whether input path contains keyword
        if path[-1] != '/':
            ele = path.split('/')
            keyword = ele[-1]
            path = ''.join(ele[:-1])
            print('Under Construction')
            print(path, keyword)

        for ele in os.listdir(path):
            # skip files without keyword
            if keyword is not None and not re.search(keyword, ele):
                continue

            # get matrix path
            if re.search(r'matrix.mtx', ele):
                matrix_path = path + ele

            # get feature path
            elif re.search(r'genes.tsv',ele) or re.search(r'features.tsv',ele):
                features_path = path + ele

            # get barcodes path
            elif re.search(r'barcodes.tsv', ele):
                barcodes_path = path + ele

        assert matrix_path is not None
        assert features_path is not None
        assert barcodes_path is not None

        gem = mex.Reader(
            matrix_path = matrix_path,
        	features_path = features_path,
            barcodes_path = barcodes_path
        )
        gem.get_gem(gene_id_type = gene_id_type)
        return tool.STD_Filter(gem.data, std_value_thread, std_ratio_thread)

    # Process in Database scenario
    def __process_gem_folder(self, std_value_thread, std_ratio_thread):
        group1 = gem.Folder(self.database_info.group1_path).combine(
            std_value_thread = std_value_thread,
            std_ratio_thread = std_ratio_thread
        )
        group2 = gem.Folder(self.database_info.group2_path).combine(
            std_value_thread = std_value_thread,
            std_ratio_thread = std_ratio_thread
        )
        return group1, group2



class Process(object):
    """
    Seperate sample gene expression data into training sets and testing sets
    by given ratio
    Then prepare sample data to be ready for training and analysis process
    """
    def __init__(self,
                 database_info = None,
                 grnData = None,
                 train_size = 0.7,
                 ramdom_state = None,
                 fullData = None,
                 fullLabel = None,
                ):
        super(Process, self).__init__()
        # Initialization
        self.train_size = train_size
        self.random_state = ramdom_state
        self.all_grp_ids = {}
        # Go through database_info based protocol
        if fullData is None or fullLabel is None:
            self.__init_protocol(database_info, grnData)
        elif fullData is not None and fullLabel is not None:
            self.__iterating_protocool(fullData.to_numpy(), fullLabel)
        else:
            raise db_setup.Error('Preprocessor Error: case not catched')

    # Process in database mode
    def __init_protocol(self, database_info, grnData):
        # group1Result is [dataTrainC1, dataTestC1, lableTrainC1, labelTestC1]
        group1Result = self.__split_train_test(
            grnData.group1_psGRNs,
            database_info.label1
        )
        # similar with group1
        group2Result = self.__split_train_test(
            grnData.group2_psGRNs,
            database_info.label2
        )
        self.labelTrain = np.array(group1Result[2] + group2Result[2])
        self.labelTest = np.array(group1Result[3] + group2Result[3])
        self.dataTrain = []
        self.dataTest = []
        # standardize feature data
        # to make sure all training and testing samples
        # will be in same dimmension
        self.__update_train_test(
            grnData.group1_psGRNs,
            train_set = group1Result[0],
            test_set = group1Result[1]
        )
        self.__update_train_test(
            grnData.group2_psGRNs,
            train_set = group2Result[0],
            test_set = group2Result[1]
        )
        # Add zeros for position holding
        self.__append_zeros(self.dataTrain)
        self.__append_zeros(self.dataTest)
        # self.__all_grp_id_check()
        # Clear unnecessary data
        del grnData
        del database_info

    # Update training and testing set based on given expression data
    def __update_train_test(self, grns, train_set, test_set):
        for sample in grns:
            grps = grns[sample].grps
            grps_ids_copy = {ele:None for ele in grps}
            values = ''
            for id in self.all_grp_ids:
                if id in grps:
                    values += str(list(grps[id].correlations.values())[0]) + ';'
                    # Update grn_cop if id already in allIDs
                    del grps_ids_copy[id]
                else: values += '0.0;'
            for id in grps_ids_copy:
                self.all_grp_ids[id] = None
                values += str(list(grps[id].correlations.values())[0]) + ';'
            # Change every elements into float type
            values = list(map(float, values.split(';')[:-1]))
            if sample in train_set:
                self.dataTrain.append(values)
            elif sample in test_set:
                self.dataTest.append(values)

    # Makke training/testing data and lable arrays based on given full data
    def __iterating_protocool(self, fullData, fullLabel):
            data = train_test_split(
                fullData,
                fullLabel,
                train_size = self.train_size,
                random_state = self.random_state
            )
            self.dataTrain = data[0]
            self.dataTest = data[1]
            self.labelTrain = data[2]
            self.labelTest = data[3]

    # seperate files in given path into training
    # and testing sets based on ratio
    def __split_train_test(self, grnData, label):
        data_sample = []
        label_sample = []
        for sample in grnData:
            data_sample.append(sample)
            label_sample.append(label)
        return train_test_split(
            data_sample,
            label_sample,
            train_size = self.train_size,
            random_state = self.random_state
        )

    # add zeros to each preprocessed samples
    # to make sure all training and testing samples
    # will be in same dimmension
    def __append_zeros(self, dataset):
        for sample in dataset:
            if len(sample) != len(self.all_grp_ids):
                sample += [0] * (len(self.all_grp_ids) - len(sample))
                sample = np.array(sample)
        dataset = np.array(dataset)

    # Check whether allIDs have dupicate IDs or not
    # ToDo: need optimization to get unique ids
    def __all_grp_id_check(self):
        # check whether allIDs have duplicate elements
        unique = [x for i, x in enumerate([*self.all_grp_ids])
            if i == [*self.all_grp_ids].index(x)]
        if len(self.all_grp_ids) != len(unique):
            raise db_setup.Error(
                'preprocessor malfunction: duplicate ID in allIDs'
            )
        del unique

    # Calculate a close-to-square matrix size based on allIDs
    # for using 2D-input based machinle learning models (e.g. hybrid_model)
    def auto_inject_fake_grps(self):
        total = len(self.all_grp_ids)
        tar = math.sqrt(total)
        if int(tar) == tar: return
        elif int(tar) < tar:
            aim = int(tar) + 1
            fakeID = 'FAKE'
            fakeID_Num = aim*aim - total
            for i in range(fakeID_Num):
                id = fakeID + str(i)
                self.all_grp_ids[id] = None
        self.__append_zeros(self.dataTrain)
        self.__append_zeros(self.dataTest)
