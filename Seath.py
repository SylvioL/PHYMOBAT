#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of PHYMOBAT 1.0.
# Copyright 2016 Sylvio Laventure (IRSTEA - UMR TETIS)
# 
# PHYMOBAT 1.0 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# PHYMOBAT 1.0 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with PHYMOBAT 1.0.  If not, see <http://www.gnu.org/licenses/>.

import numpy, math, sys
import numpy as np # sort, ...
from collections import * # defaultdict

class Seath():
    """
    Get the optimal threshold and Bhattacharyya distance for a separability between two classes

    Source article : SEaTH–A new tool for automated feature extraction in the context of object-based image analysis S. Nussbaum et al.
    
    Source Info : Kenji Ose (IRSTEA) et Nathalie St-Geours (IRSTEA) 
    
    :param value_1: List of index mean by polygons (sample 1)
    :type value_1: list
    :param value_2: List of index mean by polygons (sample 2)
    :type value_2: list
    :param threshold: Optimal threshold under this form *>0.56*
    :type threshold: str
    :param J: Jeffries-Matusita distance (measure separability between 2 classes on a 0 to 2 scale)
    :type J: list
    :Example:
    
    >>> import Seath
    >>> a = Seath()
    >>> a.value_1 = b[0].stats_dict
    >>> a.value_2 = b[1].stats_dict
    >>> a.separability_and_threshold()
    >>> a.threshold[0]
    '>0.56'
    >>> a.J[0]
    1.86523428
    
    """
    def __init__(self):
        """Create a new 'Seath' instance

        """
        
        self.value_1 = []
        self.value_2 = []
        
        self.threshold = []
        self.J = []
        
    def separability_and_threshold(self, **kwargs):
        """
        Function to extract the optimal threshold for a separability between two classes
        
        :kwargs: **index** (str) - The processing will prints the string

        """
        
        ind = kwargs['index'] if kwargs.get('index') else 'the index'
        
        field_class = [self.value_1, self.value_2]
        indict = defaultdict(list)
        
        for i in range(len(field_class)):
            for f in field_class[i].items():
                if math.isnan(f[1][0]) == False: # if math.isnan(Terrain[i][f][0]) == False:#
                    indict[i].append(f[1][0]) # Indict[Nommark[i]].append(Terrain[i][f][0])#
                    
        ### Compute Bhattacharyya distance ###
        ###############################
        
        # Compute mean and variance
        m = defaultdict(list) # Average
        v = defaultdict(list) # Variance
        p = defaultdict(list) # Likelihood
        C = defaultdict(list) # Transpose classes
        
        B = [] # Bhattacharyya distance
        # Optimal threshold
        seuil1 = []
        seuil2 = []
        seuil = []
        
        for mark in range(len(field_class)):
            C[mark] = np.array(indict[mark]).transpose()
            m[mark].append(np.mean(C[mark]))
            v[mark].append(np.var(C[mark]))
            p[mark].append(1 / float(len(C[mark])))
        
        print "m : ", m
        print "v : ", v
        
        # Mean, standard deviation and likelihood initialisation phase for 2 classes 
        m1 = m[0]
        m2 = m[1]
        v1 = v[0]
        v2 = v[1]
        p1 = p[0]
        p2 = p[1]
        
        for i in range(len(m[0])):
            B.append(( (1/float(8)) * ( (m1[i] - m2[i])**2 ) * (2 / ( v1[i] + v2[i] )) ) + ( (1/float(2)) * np.log( ( v1[i] + v2[i] ) / ( 2 * np.sqrt(v1[i] * v2[i]) ) ) ))
            self.J.append(2 * ( 1 - np.exp( -B[i] ) ))
            
            ### Optimal threshold calculation ###
            ######################
            # Bayes theorem solution
            A = np.log( np.sqrt( v1[i] / v2[i] ) * ( p2[i] / p1[i] ))
            D = np.sqrt( v1[i] * v2[i] ) * np.sqrt( ( m1[i] - m2[i] )**2 + 2 * A * ( v1[i] -  v2[i] ) )
            seuil1.append(( 1 / ( v1[i] - v2[i] ) ) * ( m2[i] * v1[i] - m1[i] * v2[i] + D ))
            seuil2.append(( 1 / ( v1[i] - v2[i] ) ) * ( m2[i] * v1[i] - m1[i] * v2[i] - D ))
            
            # Optimal threshold
            # Logical condition depending on article figure 2
            if ( seuil1[i] > m2[i] and seuil1[i] < m1[i] ) or ( seuil1[i] > m1[i] and seuil1[i] < m2[i] ) :
                print "Valid  threshold !"
            else:
                seuil1[i] = ""
            
            if ( seuil2[i] > m2[i] and seuil2[i] < m1[i] ) or ( seuil2[i] > m1[i] and seuil2[i] < m2[i] ) :
                print "Valid  threshold !"
            else:
                seuil2[i] = ""
        
            # Final condition
            if ( seuil1[i] == "" and seuil2[i] == "" ) or ( seuil1[i] != "" and seuil2[i] != "" ):
                seuil.append("")
            elif ( seuil1[i] != "" and seuil2[i] == "" ):
                seuil.append(seuil1[i])
            elif ( seuil1[i] == "" and seuil2[i] != "" ):
                seuil.append(seuil2[i])
        
        print("Bhattacharyya distance ", B)
        print("J : ", self.J)
        print("Threshold 1 : ", seuil1)
        print("Threshold 2 : ", seuil2)
        print("Optimal threshold :", seuil)
        
        for i in range(len(seuil)):
            if seuil[i] != "" and m1[i] > m2[i]:
                print('For ' + ind  + ', the class 1 > ' + str(seuil[i]))
                self.threshold.append('<' + str(seuil[i]))
            elif seuil[i] != "" and m1[i] < m2[i]:
                print('For ' + ind  + ', the class 1 < ' + str(seuil[i]))
                self.threshold.append('>' + str(seuil[i]))
            else:
                print('For ' + ind  + ', not discrimination !')
                sys.exit(1)
#                 self.threshold.append('')