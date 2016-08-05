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

import sys, os, math
import numpy as np
from Vector import Vector
try :
    import ogr
except :
    from osgeo import ogr
from collections import *

class Segmentation(Vector):
    
    """
    Vector class inherits the super vector class properties. This class create the final shapefile : Cartography 
    on a input segmentation by decision tree.
    
    The output classname are (**out_class_name** variable):
        - Vegetation non naturelle
        - Vegetation semi-naturelle
        - Herbacees
        - Ligneux
        - Ligneux mixtes
        - Ligneux denses
        - Forte phytomasse
        - Moyenne phytomasse
        - Faible phytomasse
    
    :param vector_used: Input/Output shapefile to clip (path)
    :type vector_used: str
    :param vector_cut: Area shapefile (path)
    :type vector_cut: str
    :param output_file: Output shapefile cartography. This path is the same than the segmentation path.
    :type output_file: str
    :param out_class_name: List of output class name
    :type out_class_name: list of str
    :param out_threshold: List of output threshold
    :type out_threshold: list of str
    :param max_...: Biomass and density (IDM, SFS index) maximum
    :type max_...: float
    :param class_tab_final: Final decision tree table
    :type class_tab_final: dict
    """
    
    def __init__(self, used, cut):
        """Create a new 'Clustering' instance
        
        """
        Vector.__init__(self, used, cut)
        
        self.output_file =  'Final_classification.shp'
        
        self.out_class_name = []
        self.out_threshold = []
        
        self.class_tab_final = defaultdict(list)
      
        self.max_wood_idm = 0
        self.max_wood_sfs = 0
        self.max_bio = 0
    
    def create_cartography(self, out_fieldnames, out_fieldtype):
        """
        Function to create a output shapefile. In this output file,
        there is the final cartography. With output defined field names
        and field type in the main process.

        :param out_fieldnames: List of output field names
        :type out_fieldnames: list of str
        :param out_fieldtype: List of outpu field type
        :type out_fieldtype: list of str
        """
        
        shp_ogr = self.data_source.GetLayer()
        
        # Projection
        # Import input shapefile projection
        srsObj = shp_ogr.GetSpatialRef()
        # Conversion to syntax ESRI
        srsObj.MorphToESRI()
            
        ## Remove the output shapefile if it exists
        self.vector_used = self.output_file
        if os.path.exists(self.vector_used):
            self.data_source.GetDriver().DeleteDataSource(self.vector_used)
        out_ds = self.data_source.GetDriver().CreateDataSource(self.vector_used)
        
        if out_ds is None:
            print('Could not create file')
            sys.exit(1)
            
        #  Specific output layer
        out_layer = out_ds.CreateLayer(str(self.vector_used), srsObj, geom_type=ogr.wkbMultiPolygon)
        
        # Add new fields
        for i in range(0, len(out_fieldnames)):
            fieldDefn = ogr.FieldDefn(str(out_fieldnames[i]), out_fieldtype[i])
            out_layer.CreateField(fieldDefn)
        # Add 2 fields to convert class string in code to confusion matrix
        fieldDefn = ogr.FieldDefn('FBPHY_CODE', ogr.OFTInteger)
        out_layer.CreateField(fieldDefn)
        out_fieldnames.append('FBPHY_CODE')
        fieldDefn = ogr.FieldDefn('FBPHY_SUB', ogr.OFTInteger)
        out_layer.CreateField(fieldDefn)
        out_fieldnames.append('FBPHY_SUB')
        
        # Feature for the ouput shapefile
        featureDefn = out_layer.GetLayerDefn()
        
        in_feature = shp_ogr.SetNextByIndex(0) # Polygons initialisation
        in_feature = shp_ogr.GetNextFeature()
        # Loop on input polygons
        while in_feature:
            
            geom = in_feature.GetGeometryRef() # Extract input geometry

            # Create a new polygon
            out_feature = ogr.Feature(featureDefn)
        
            # Set the polygon geometry and attribute
            out_feature.SetGeometry(geom)
            # Set the existing ID 
            out_feature.SetField(out_fieldnames[0], in_feature.GetField(self.field_names[2]))
            # Set the area
            out_feature.SetField(out_fieldnames[1], geom.GetArea()/10000)
            # Set the others polygons fields with the decision tree dictionnary
            for i in range(2, len(out_fieldnames)):
                # If list stopped it on the second level, complete by empty case
                if len(self.class_tab_final[in_feature.GetFID()]) < len(out_fieldnames)-2 and \
                                                    self.class_tab_final[in_feature.GetFID()] != []:
                    self.class_tab_final[in_feature.GetFID()].insert(len(self.class_tab_final[in_feature.GetFID()])-2,'') # To 3rd level
                    self.class_tab_final[in_feature.GetFID()].insert(len(self.class_tab_final[in_feature.GetFID()])-2,0) # To degree
                 
                try:
                    # To the confusion matrix, replace level ++ by level --
                    if i == len(out_fieldnames)-1:
                        if self.class_tab_final[in_feature.GetFID()][i-2] == 6:
                            # Crops to artificial vegetation
                            self.class_tab_final[in_feature.GetFID()][i-2] = 0
                        if self.class_tab_final[in_feature.GetFID()][i-2] == 2:
                            # Grassland to natural vegetation
                            self.class_tab_final[in_feature.GetFID()][i-2] = 1
                        if self.class_tab_final[in_feature.GetFID()][i-2] > 7:
                            # Phytomass to natural vegetation
                            self.class_tab_final[in_feature.GetFID()][i-2] = 1
                            
                    out_feature.SetField(str(out_fieldnames[i]), self.class_tab_final[in_feature.GetFID()][i-2])
                except:
#                     pass
                    for i in range(2, len(out_fieldnames)-2):
                        out_feature.SetField(str(out_fieldnames[i]), 'Undefined')
                    out_feature.SetField('FBPHY_CODE', 255)
                    out_feature.SetField('FBPHY_SUB', 255)
#                     sys.exit(1)
            # Append polygon to the output shapefile
            out_layer.CreateFeature(out_feature)
    
            # Destroy polygons
            out_feature.Destroy()    
            in_feature.Destroy()
            
            # Next polygon
            in_feature = shp_ogr.GetNextFeature()
            
        # Close data
        out_ds.Destroy() 

    def decision_tree(self, combin_tree):
        """
        Function to build the decision tree. Taking account output threshold and input 
        class name.
        
        :param combin_tree: Decision tree combination
        :type combin_tree: list of number class name
            
        """
        
        # Combination tree on a sentence. Every sentence will be in a table.
        cond_tab = []
        for ct in combin_tree:
            cond_a = '' # Condition Term
            c = 0
            while c < len(ct):  
                # Loop on tree combinaison                    
                if self.out_threshold[ct[c]] =='':
                    # For interval condition
                    cond_a = cond_a + 'self.stats_dict[ind_stats][' + str(ct[c]/2) + ']' +\
                             self.out_threshold[ct[c]-1].replace('>', '<=') + \
                             ' and self.stats_dict[ind_stats][' + str(ct[c]/2) + ']' +\
                             self.out_threshold[ct[c]+1].replace('<', '>=') + ' and '
                else:
                    cond_a = cond_a + 'self.stats_dict[ind_stats][' + str(ct[c]/2) + ']' +\
                            self.out_threshold[ct[c]] + ' and '
                c = c + 1
            cond_tab.append(cond_a[:-5]) # Remove the last 'and'

        # Loop on every value 
        for ind_stats in range(len(self.stats_dict)):
            # Loop on decision tree combination.
            for cond in cond_tab:
                # Add class name in the output table
                try:
                    if eval(cond):
                        self.class_tab_final[ind_stats] = [self.out_class_name[s] \
                                                           for s in combin_tree[cond_tab.index(cond)]] + \
                                                           [combin_tree[cond_tab.index(cond)][len(combin_tree[cond_tab.index(cond)])-1]] + \
                                                           [combin_tree[cond_tab.index(cond)][len(combin_tree[cond_tab.index(cond)])-1]]
                except NameError:
                    # If there is 'nan' in the table statistics
                    if eval(cond.replace('nan','-10000')):# If there is 'nan' in the table statistics
                        self.class_tab_final[ind_stats] = [self.out_class_name[s] \
                                                           for s in combin_tree[cond_tab.index(cond)]] + \
                                                           [combin_tree[cond_tab.index(cond)][len(combin_tree[cond_tab.index(cond)])-1]] + \
                                                           [combin_tree[cond_tab.index(cond)][len(combin_tree[cond_tab.index(cond)])-1]]
    
    def compute_biomass_density(self):
        """
        Function to compute the biomass and density distribution.
        It returns threshold of biomass level.
        
        """
        
        distri = [v[1:] for k, v in self.stats_dict.items() if eval('v[0]' + self.out_threshold[1])]
        
        distri_bio = []
        distri_den = []
        for b in distri:
            if eval('b[0]' + self.out_threshold[2]) and b[len(b)-1] != float('inf') and b[len(b)-1] != float('nan') and b[len(b)-1] < 1:
                distri_bio.append(b)
            else:
                distri_den.append(b)
        # Tranpose table        
        t_distri_bio = list(map(list, zip(*distri_bio)))
        t_distri_den = list(map(list, zip(*distri_den)))
        
        # Biomass threshold
        stdmore =  np.mean(t_distri_bio[2]) + np.std(t_distri_bio[2])
        stdless =  np.mean(t_distri_bio[2]) - np.std(t_distri_bio[2])
        self.out_threshold.append('>'+str(stdmore))
        self.out_threshold.append('')
        self.out_threshold.append('<'+str(stdless))
        
        # Compute density and biomass maximum
        self.max_wood_idm = np.max(t_distri_den[1])
        self.max_wood_sfs = np.max(t_distri_den[0])
        self.max_bio = np.max(t_distri_bio[2])
        
    def append_scale(self, select_class, form):
        """
        Function to complete the 'class_tab_final' list with density and biomass information. This list will be used to build
        the final shapefile.
        
        :param select_class: Class name to add degree
        :type select_class: str
        :param form: Formula to add degree
        :type form: str
        
        """
        
        for ind_stats in range(len(self.stats_dict)):
            # Only valid on the second level
            try:
                if self.class_tab_final[ind_stats][1] == select_class:
                    self.class_tab_final[ind_stats].insert(len(self.class_tab_final[ind_stats])-2,eval(form))
            except IndexError:
                pass
                
                