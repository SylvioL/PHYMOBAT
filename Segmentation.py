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
    import ogr, gdal
except :
    from osgeo import ogr, gdal
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
        
        self.mono_rpg_tif = ''
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
        
        shp_ogr_ds = self.data_source
        shp_ogr = self.data_source.GetLayer()
                        
        # Projection
        # Import input shapefile projection
        srsObj = shp_ogr.GetSpatialRef()
        # Conversion to syntax ESRI
        srsObj.MorphToESRI()
        
        ## Remove the output final shapefile if it exists
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
        out_fieldnames.insert(2,'RPG_CODE')
        out_fieldtype.insert(2,ogr.OFTInteger)
        for i in range(0, len(out_fieldnames)):
            fieldDefn = ogr.FieldDefn(str(out_fieldnames[i]), out_fieldtype[i])
            out_layer.CreateField(fieldDefn)
#         # Add the RPG column
#         fieldDefn = ogr.FieldDefn('RPG_CODE', ogr.OFTInteger)
#         out_layer.CreateField(fieldDefn)
#         out_fieldnames.append('RPG_CODE')
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
        
        # Extract RPG tif data and information
        self.raster_ds = gdal.Open(str(self.mono_rpg_tif), gdal.GA_ReadOnly)
        rows = self.raster_ds.RasterYSize # Rows number
        cols = self.raster_ds.RasterXSize # Columns number
        geotransform = self.raster_ds.GetGeoTransform()
        prj_wkt = self.raster_ds.GetProjectionRef()
        # Table's declaration
        data_rpg = []
        canal_rpg = self.raster_ds.GetRasterBand(1) # Select a band
        data_rpg = canal_rpg.ReadAsArray(0, 0, cols, rows).astype(np.int32)
        # Create a fictif shapefile
        out_rast = shp_ogr_ds.GetDriver().CreateDataSource(self.output_file[:-4] + '_.shp')
        out_fictif = out_rast.CreateLayer(str(self.output_file[:-4] + '_.shp'), srsObj, geom_type=ogr.wkbMultiPolygon)
        fieldDefn = ogr.FieldDefn('ID', ogr.OFTInteger)
        out_fictif.CreateField(fieldDefn)
        
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
            
            # Set the RPG column
            # Create a fictif polygon in the shapefile
            feature_fictif = ogr.Feature(out_fictif.GetLayerDefn())
            feature_fictif.SetGeometry(geom)
            feature_fictif.SetField("ID",1)
            out_fictif.CreateFeature(feature_fictif)
            
            # Create a fictif raster from a segementation polygon
            out_raster_ds = gdal.GetDriverByName('GTiff').Create(self.mono_rpg_tif[:-4] + '_.TIF', cols, rows, 1, gdal.GDT_Int32)
            out_raster_ds.SetGeoTransform(geotransform)
            out_raster_ds.SetProjection(prj_wkt)
            # Virtual rasterize the vector 
            pt_rast = gdal.RasterizeLayer(out_raster_ds, [1], out_fictif, options=["ATTRIBUTE=ID"])
            data_polygon = out_raster_ds.ReadAsArray()
            
            # Remove the feature after useful
            out_fictif.DeleteFeature(feature_fictif.GetFID())
            feature_fictif.Destroy()
            
            # Mask data value with data polygon
            poly_pxl = np.ma.masked_where(data_polygon == 0, data_rpg)
            poly_pxl.fill_value = 0
            poly_pxl.filled()
            poly_on_line = np.hstack(poly_pxl.filled())
            # Search majority and count the number of majority class
            counts = np.bincount(poly_on_line)
            
            recouv_crops_RPG = 0
            # To avoid zero's values
            if len(counts) > 1:   
                counts[0] = 0 # It need to keep zero value in the tab then it necessary to replace by 0 in count
                maj_class = np.argmax(counts)
                nbpxl_maj = counts[maj_class]
                
                area_intersect = (nbpxl_maj * geotransform[1] * geotransform[1]) / float(10000)
                area_segm = geom.GetArea() / float(10000)
                
                pourc_inter = (area_intersect / float(area_segm)) * 100
                if pourc_inter >= 85:
                    recouv_crops_RPG = maj_class
                    
            out_feature.SetField('RPG_CODE', recouv_crops_RPG)
            
            # Set the others polygons fields with the decision tree dictionnary
            for i in range(3, len(out_fieldnames)):
                # If list stopped it on the second level, complete by empty case
                if len(self.class_tab_final[in_feature.GetFID()]) < len(out_fieldnames)-3 and \
                                                    self.class_tab_final[in_feature.GetFID()] != []:
                    self.class_tab_final[in_feature.GetFID()].insert(len(self.class_tab_final[in_feature.GetFID()])-3,'') # To 3rd level
                    self.class_tab_final[in_feature.GetFID()].insert(len(self.class_tab_final[in_feature.GetFID()])-3,0) # To degree
                    
                try:
                    # To the confusion matrix, replace level ++ by level --
                    if i == len(out_fieldnames)-1:
                        if self.class_tab_final[in_feature.GetFID()][i-3] == 6:
                            # Crops to artificial vegetation
                            self.class_tab_final[in_feature.GetFID()][i-3] = 0
                        if self.class_tab_final[in_feature.GetFID()][i-3] == 2:
                            # Grassland to natural vegetation
                            self.class_tab_final[in_feature.GetFID()][i-3] = 1
                        if self.class_tab_final[in_feature.GetFID()][i-3] > 7:
                            # Phytomass to natural vegetation
                            self.class_tab_final[in_feature.GetFID()][i-3] = 1
                            
                    out_feature.SetField(str(out_fieldnames[i]), self.class_tab_final[in_feature.GetFID()][i-3])
                except:
#                     pass
                    for i in range(3, len(out_fieldnames)-3):
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
    
    def compute_biomass_density(self, method='SEATH'):
        """
        Function to compute the biomass and density distribution.
        It returns threshold of biomass level.
        
        :param method: Classification method used. It can set 'SEATH' (by default) or 'RF'
        :type method: str
        """
        
        if method == 'SEATH':
            distri = [v[1:] for k, v in self.stats_dict.items() if eval('v[0]' + self.out_threshold[1])]
            
            distri_bio = []
            distri_den = []
            for b in distri:
                if eval('b[0]' + self.out_threshold[2]) and b[len(b)-1] != float('inf') and b[len(b)-1] != float('nan') and b[len(b)-1] < 1:
                    distri_bio.append(b)
                else:
                    distri_den.append(b)
        elif method == 'RF':
            distri = [v[1:] for k, v in self.stats_dict.items() if not self.out_threshold[k] in [0,6,7]]
            
            distri_bio = []
            distri_den = []
            for b in distri:
                if self.out_threshold[distri.index(b)] in [1,2,8,9,10] and b[len(b)-1] != -10000 and b[len(b)-1] < 1:
                    distri_bio.append(b)
                else:
                    distri_den.append(b)

            # Set this variable used normally to define threshold of the classification with SEATH method
            self.out_threshold = []
        # Transpose table        
        t_distri_bio = list(map(list, zip(*distri_bio)))
        t_distri_den = list(map(list, zip(*distri_den)))
        
        # Biomass threshold
        stdmore =  (np.mean(t_distri_bio[2]) + np.std(t_distri_bio[2]))/np.max(t_distri_bio[2])
        stdless =  (np.mean(t_distri_bio[2]) - np.std(t_distri_bio[2]))/np.max(t_distri_bio[2])
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
                    # To add phytomasse
                    print ind_stats
                    print self.class_tab_final[ind_stats]
                    print self.class_tab_final[ind_stats][self.class_tab_final[ind_stats].index(eval(form))-1]
                    if self.class_tab_final[ind_stats][self.class_tab_final[ind_stats].index(eval(form))-1] == '' and \
                        self.class_tab_final[ind_stats][self.class_tab_final[ind_stats].index(eval(form))-2] != '':
                        # dict[][A.index(real_pourcent)-1] == '' and dict[][A.index(real_pourcent)-2] != ''
                        # Print phytomasse class in the tab because of self.in_class_name in the Processing class
                        if not eval(form + self.out_threshold[0]) and not eval(form + self.out_threshold[2]):
                            self.class_tab_final[ind_stats][self.class_tab_final[ind_stats].index(eval(form))-1] = self.out_class_name[9]
                            self.class_tab_final[ind_stats][len(self.class_tab_final[ind_stats])-1] = 9
                        elif eval(form + self.out_threshold[0]):
                            self.class_tab_final[ind_stats][self.class_tab_final[ind_stats].index(eval(form))-1] = self.out_class_name[8]
                            self.class_tab_final[ind_stats][len(self.class_tab_final[ind_stats])-1] = 8
                        elif eval(form + self.out_threshold[2]):
                            self.class_tab_final[ind_stats][self.class_tab_final[ind_stats].index(eval(form))-1] = self.out_class_name[10]
                            self.class_tab_final[ind_stats][len(self.class_tab_final[ind_stats])-1] = 10
                        
            except IndexError:
                pass
                
                