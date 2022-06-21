### [API Refences](https://nkmtmsys.github.io/Ageas/tutorial)


# Launch()
Launch AGEAS as a single object.
<pre>
ageas.Launch(
    model_config_path:str = None,
    mute_unit:bool = True,
    protocol:str = 'solo',
    unit_num:int = 2,
    warning_filter:str = 'ignore',
    correlation_thread:float = 0.2,
    database_path:str = None,
    database_type:str = 'gem_files',
    factor_name_type:str = 'gene_name',
    group1_path:str = None,
    group2_path:str = None,
    interaction_database:str = 'gtrd',
    log2fc_thread:float = None,
    meta_load_path:str = None,
    mww_p_val_thread:float = 0.05,
    prediction_thread = 'auto',
    psgrn_load_path:str = None,
    specie:str = 'mouse',
    sliding_window_size:int = 10,
    sliding_window_stride:int = None,
    std_value_thread:float = 1.0,
    std_ratio_thread:float = None,
    clf_keep_ratio:float = 0.5,
    clf_accuracy_thread:float = 0.8,
    cpu_mode:bool = False,
    feature_dropout_ratio:float = 0.1,
    feature_select_iteration:int = 1,
    impact_depth:int = 3,
    top_grp_amount:int = 100,
    grp_changing_thread:float = 0.05,
    link_step_allowrance:int = 1,
    model_select_iteration:int = 2,
    outlier_thread:float = 3.0,
    stabilize_patient:int = 3,
    stabilize_iteration:int = 10,
    max_train_size:float = 0.95,
    z_score_extract_thread:float = 0.0,
)
</pre>


## **Args**

+ **_model_config_path_**: Default = None
    <sub>
    Path to load model config file which will be used to initialize classifiers
    </sub>

+ **_mute_unit_**: Default = True
    <sub>
    The studying specie which will determine set of dependent database using for analysis. Only mouse and human are supported now.
    </sub>

+ **_protocol_**: Default = 'solo'
    <sub>
    AGEAS unit launching protocol.

    Supporting:
    - 'solo': All units will run separately
    - 'multi': All units will run parallelly by multithreading
    </sub>

+ **_unit_num_**: Default = 2
    <sub>
    Number of AGEAS units to launch.
    </sub>

+ **_warning_filter_**: Default = 'ignore'
    <sub>
    How warnings should be filtered.

    For other options, please check 'The Warnings Filter' section [here](https://docs.python.org/3/library/warnings.html#warning-filter)
    </sub>


## **Methods**


### **save_reports()**

Save data and reports in given folder

  + **Args**

    + **_folder_path_**: Default = None
        <sub>
        Folder path to save all files.
        </sub>

    + **_save_unit_reports_**: Default = False
        <sub>
        Whether save key GRPs extracted by each AGEAS
        </sub>



## **Example**
<pre>
import ageas
result = ageas.Launch(
  group1_path = 'test/ips.csv',
  group2_path = 'test/mef.csv',
)
result.save_reports(
	folder_path = 'easy_test.report',
	save_unit_reports = True
)
</pre>