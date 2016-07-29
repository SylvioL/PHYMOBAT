#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of PHYMOBAT 1.2.
# Copyright 2016 Sylvio Laventure (IRSTEA - UMR TETIS)
# 
# PHYMOBAT 1.2 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# PHYMOBAT 1.2 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with PHYMOBAT 1.2.  If not, see <http://www.gnu.org/licenses/>.

import os, subprocess
import numpy as np

from Toolbox import *
from Vector import Vector
from RasterSat_by_date import RasterSat_by_date

from sklearn.metrics import confusion_matrix
# Get all statistics precision, recall, f_score etc ...
from sklearn.metrics import classification_report
# Precision on the matrix diagonal
from sklearn.metrics import accuracy_score
# The precision is the ratio tp / (tp + fp) where tp is the number of true positives and fp the number of false positives
from sklearn.metrics import recall_score
# The precision is the ratio tp / (tp + fp) where tp is the number of true positives and fp the number of false positives.
from sklearn.metrics import precision_score
# The F1 score can be interpreted as a weighted average of the precision and recall F1 = 2 * (precision * recall) / (precision + recall)
from sklearn.metrics import f1_score 

class Precision_moba():
    """
    Classification precision class. This class build the whole of processing to extract the precision
    of the classification from the MOBA method.
    
    :param path_cut: Study area shapefile
    :type path_cut: str
    :param path_save: Main folder path. To save precision file in txt
    :type path_save: str
    :param complete_validation_shp: Shapefile path of the validation
    :type complete_validation_shp: str
    :param ex_raster: Raster model path to the rasterization
    :type ex_raster: str
    :param img_pr: To store the rasterization path of the classification [0] and the validation [1]
    :type img_pr: list
    :param complete_img: To store info raster of the classification [0] and the validation [1]
    :type complete_img: list
    
    """
    
    def __init__(self, path_cut, path_save):
        """Create a new 'Precision' instance
        
        """
        
        self.path_cut = path_cut
        self.path_save = path_save
        
        self.complete_validation_shp = ''
        self.ex_raster = ''
        
        self.img_pr = []
        self.complete_img = []
    
    def preprocess_to_raster_precision(self, shp_pr, field_pr):
        """
        Function to extract data in pixel of vectors. For that, it need to
        save a shapefile, then rasterize it and get a final data matrix.
        
        :param shp_pr: Input shapefile path
        :type shp_pr: str 
        :param field_pr: Field name of the shapefile to rasterize
        :type field_pr: str
        """
        
        kwargs = {}
        kwargs['rm_rast'] = 1 # To remove existing raster in the clip_raster function
        opt = {}
        opt['Remove'] = 1 # To remove existing vector
        # Define vector
        vector_pr = Vector(shp_pr, self.path_cut, **opt)
        # Create the raster output path
        img_pr = vector_pr.layer_rasterization(self.ex_raster, field_pr)
        self.img_pr.append(clip_raster(img_pr, self.complete_validation_shp, **kwargs))
        
        # Call the raster class to extract the image data
        self.complete_img.append(RasterSat_by_date('', '', [0]))
    
    def confus_matrix(self, data_class, data_val):
        """
        Function to compute and save a confusion matrix, precision, recall, 
        f_scrore and overall accuracy of the classification. 
        It compute all statistics because of sklearn module.
        At the final step, it save in the principal folder.
        
        :param data_class: Classification data
        :type data_class: matrix array
        :param data_val: Validation data
        :type data_val: matrix array
        """
        
        data_class = data_class.flatten() # to convert a matrix array in list array
        data_val = data_val.flatten()
        
        # Add pixel value in a list without no data
        fb_stats_2 = [[data_class[x],data_val[x]] for x in range(len(data_val)) if data_val[x] != -10000]
        fb_stats_2 = map(list, zip(*fb_stats_2))# transpose list
        fb_stats_in = fb_stats_2[0]
        fb_stats_val = fb_stats_2[1]
        
        # Open a file (txt) to save results
        f = open(self.path_save + "/ConfusionMatrix.txt", "wb")
        
        # Compute statistics on the classification
        cm = confusion_matrix(fb_stats_val, fb_stats_in)
        f.write("Confusion Matrix :\n")
        for out in cm:
            f.write(str(out) + "\n")
        
        all_pr = classification_report(fb_stats_val, fb_stats_in)
        f.write("\n")
        f.write(all_pr)    
        
        accur = accuracy_score(fb_stats_val, fb_stats_in)
        f.write("\n")
        f.write("Accuracy : " + str(accur) + "\n")
        
        recall = recall_score(fb_stats_val, fb_stats_in)
        f.write("\n")
        f.write("Recall : " + str(recall) + "\n")
        
        pr = precision_score(fb_stats_val, fb_stats_in)
        f.write("\n")
        f.write("Precision : " + str(pr) + "\n")
        
        f_scor = f1_score(fb_stats_val, fb_stats_in)
        f.write("\n")
        f.write("F_score : " + str(f_scor) + "\n")
        
        kappa = self.cohen_kappa_score(fb_stats_val, fb_stats_in)
        f.write("\n")
        f.write("Kappa : " + str(kappa) + "\n")
        print('')
        print('')
        print('Accuracy : %f, Kappa : %f, Recall : %f, Precision : %f, F_score : %f' % (accur, kappa, recall, pr, f_scor))
        print('')
        print all_pr
        print('')
        print('Confusion matrix :')
        print cm
        
        f.close()
        
    def cohen_kappa_score(self, y1, y2, labels=None):
        """
        Ref : https://github.com/scikit-learn/scikit-learn/blob/51a765a/sklearn/metrics/classification.py#L260 
        
        Cohen's kappa: a statistic that measures inter-annotator agreement.
        This function computes Cohen's kappa [1], a score that expresses the level
        of agreement between two annotators on a classification problem. It is
        defined as
        .. math::
            \kappa = (p_o - p_e) / (1 - p_e)
        where :math:`p_o` is the empirical probability of agreement on the label
        assigned to any sample (the observed agreement ratio), and :math:`p_e` is
        the expected agreement when both annotators assign labels randomly.
        :math:`p_e` is estimated using a per-annotator empirical prior over the
        class labels [2].
        Parameters
        ----------
        y1 : array, shape = [n_samples]
            Labels assigned by the first annotator.
        y2 : array, shape = [n_samples]
            Labels assigned by the second annotator. The kappa statistic is
            symmetric, so swapping ``y1`` and ``y2`` doesn't change the value.
        labels : array, shape = [n_classes], optional
            List of labels to index the matrix. This may be used to select a
            subset of labels. If None, all labels that appear at least once in
            ``y1`` or ``y2`` are used.
        Returns
        -------
        kappa : float
            The kappa statistic, which is a number between -1 and 1. The maximum
            value means complete agreement; zero or lower means chance agreement.
        References
        ----------
        .. [1] J. Cohen (1960). "A coefficient of agreement for nominal scales".
               Educational and Psychological Measurement 20(1):37-46.
               doi:10.1177/001316446002000104.
        .. [2] R. Artstein and M. Poesio (2008). "Inter-coder agreement for
               computational linguistics". Computational Linguistic 34(4):555-596.
        """
        
        confusion = confusion_matrix(y1, y2, labels=labels)
        P = confusion / float(confusion.sum())
        p_observed = np.trace(P)
        p_expected = np.dot(P.sum(axis=0), P.sum(axis=1))
        
        return (p_observed - p_expected) / (1 - p_expected)
        