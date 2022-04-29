#!/usr/bin/env python3
"""
Ageas Reborn
Scikit-Learn Support Vector Machine based classifier
related classes and functions

author: jy, nkmtmsys
"""


import difflib
import itertools
import ageas.classifier as classifier
from sklearn import svm



class SVM(classifier.Sklearn_Template):
    """
    Build up SVM classifier based on given parameters
    Note:
    kerenl = {‘linear’, ‘poly’, ‘rbf’, ‘sigmoid’, ‘precomputed’}
    https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html
    """
    # Set clf to default level
    def initial(self): self.clf = svm.SVC(**self.param)



class Make(classifier.Make_Template):
    """
    Analysis the performances of SVM based approaches
    with different hyperparameters
    Find the top settings to build SVM
    """

    # Perform classifier training process for given times
    # and keep given ratio of top performing classifiers
    def train(self, dataSets, keepRatio, keepThread):
        for id in self.configs['Config']:
            # Initialize SVM model
            candidate = SVM(self.configs['Config'][id])
            candidate.train(dataSets.dataTrain, dataSets.labelTrain)
            # Check performance
            testResult = candidate.clf.predict(dataSets.dataTest)
            accuracy = difflib.SequenceMatcher(None,
                testResult, dataSets.labelTest).ratio()
            self.models.append([candidate, id, accuracy])
        self.models.sort(key = lambda x:x[-1], reverse = True)
        self._filter_models(keepRatio, keepThread)
