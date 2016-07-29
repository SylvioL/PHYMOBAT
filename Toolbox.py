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

def clip_raster(imag, vect, **kwargs):
    """
    Function to clip a raster with a vector. The raster created will be in the same folder than the input raster.
    With a prefix *Clip_*.
    
    :param imag: Input image (path)
    :type imag: str
    :param vect: Extent shapefile (path)
    :type vect: str
    :kwargs: **rm_rast** (int) - 0 (by default) or 1. Variable to remove the output raster. 0 to keep and 1 to remove.
    
    :returns: str -- variable **outclip**, output raster clip (path).
    """    
    
    rm_rast = kwargs['rm_rast'] if kwargs.get('rm_rast') else 0
    outclip = os.path.split(str(imag))[0] + '/Clip_' + os.path.split(str(imag))[1]
    if not os.path.exists(outclip) or rm_rast == 1:
        print 'Raster clip of ' + os.path.split(str(imag))[1]
        # Command to clip a raster with a shapefile by Gdal
        process_tocall_clip = ['gdalwarp', '-overwrite', '-dstnodata', '-10000', '-q', '-cutline', vect, '-crop_to_cutline', '-of', 'GTiff', imag, outclip]
        subprocess.call(process_tocall_clip)
    
    return outclip

def calc_serie_stats(table):
    """
    Function to compute stats on temporal cloud and ndvi spectral table
    Ndvi stats : min    max    std    max-min
    
    :param table: Spectral data, cloud raster and ndvi raster
    :type table: numpy.ndarray
    :returns: list of numpy.ndarray -- variable **account_stats**, list of temporal NDVI stats.
                  
                numpy.ndarray -- variable **account_cloud**, pixel number clear on the area.
    """ 
    
    # Compute stats on these indexes
    ind = ['np.min(tab_ndvi_masked, axis=2)', 'np.max(tab_ndvi_masked, axis=2)', 'np.max(tab_ndvi_masked, axis=2)', \
           'np.max(tab_ndvi_masked, axis=2)-np.min(tab_ndvi_masked, axis=2)'] # [Min, Max, Std, Max-Min]
           
    # For the cloud map 
    # In the input table the cloud floor is the 5th
    tab_cloud = np.dstack(table[5]) # Stack cloud table (dimension : 12*X*Y to X*Y*12)
    
    cloud_true = (tab_cloud == 0) # if tab_cloud = 0 then True else False / Mask cloud
    account_cloud = np.sum(cloud_true, axis=2) # Account to tab_cloud if != 0 => Sum of True. (Dimension X*Y)
    
    # For the ndvi stats
    # In the input table the ndvi floor is the 7th
    stack_ndvi = np.dstack(table[7]) # Like cloud table, stack ndvi table
#     mask_ndvi = np.ma.masked_equal(stack_ndvi, -10000, copy=True) # Mask values -10000
    mask_cloud = np.ma.masked_where((stack_ndvi == -10000) | (tab_cloud != 0), tab_cloud)# Mask values -10000 and > 0(Not cloud)
#    mask_cloud = (tab_cloud != 0) | (stack_ndvi == -10000)
    tab_ndvi_masked = np.ma.array(stack_ndvi, mask=mask_cloud.mask)#mask_cloud.mask) # Ndvi table with clear values 
             
    # Stats on the indexes defined above
    account_stats = []
    for i in ind:
        i_stats = eval(i) # Compute stats
        i_stats.fill_value = -10000 # Substitute default fill value by -10000 
        account_stats.append(i_stats.filled()) # Add stats table with true fill value

    return account_stats, account_cloud

def cohen_kappa_score(y1, y2, labels=None):
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

def confus_matrix(data_class, data_val):
    """
    Function to compute ans save matrix confusion, precision, recall, 
    f_scrore and overall accuracy of the classification. 
    It compute all statistics because of 
    """
    
    data_class = data_class.flatten() # to convert a matrix array in list array
    data_val = data_val.flatten()
    
    # Add pixel value in a list without no data
    fb_stats_2 = [[data_class[x],data_val[x]] for x in range(len(data_val)) if data_val[x] != -10000]
    fb_stats_2 = map(list, zip(*fb_stats_2))# transpose list
    fb_stats_in = fb_stats_2[0]
    fb_stats_val = fb_stats_2[1]
    
    # Open a file (txt) to save results
    f = open("ConfusionMatrix.txt", "wb")
    
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
    
    kappa = cohen_kappa_score(fb_stats_val, fb_stats_in)
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
    
    