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

import sys, os
import numpy as np
from Vector import Vector
try :
    import ogr
except :
    from osgeo import ogr
from collections import *

class Rpg(Vector):
    
    """
    Vector class inherits the super vector class properties. This class create a new RPG shapefile
    with mono-crops. It needs a basic RPG shapefile and a basic RPG CSV file *(...-GROUPES-CULTURE...)* in :func:`mono_rpg`.
    
    :param vector_used: Input/Output shapefile to clip (path)
    :type vector_used: str
    :param vector_cut: Area shapefile (path)
    :type vector_cut: str
    :param rm_dupli: Rpg table with no duplicated crops group
    :type rm_dupli: dict
    :param head_in_read: List of rgp header
    :type head_in_read: list of str
    :param min_size: Minimum size to extract a rpg polygons
    :type min_size: float
    """
    
    def __init__(self, used, cut):
        """Create a new 'Rpg' instance
        """
        Vector.__init__(self, used, cut)
        
        self.rm_dupli = defaultdict(list)
        self.head_in_read = []
        self.min_size = 1
    
    def create_new_rpg_files(self):
        """
        Function to create new rpg shapefile with **rm_dpli** variable. The output shapefile
        will be create in the same folder than the input shapefile with prefix *MONO_*.

        """
        ## The output shapefile if it exists
        self.vector_used = os.path.split(self.vector_used)[0] + '/' + 'MONO_' + os.path.split(self.vector_used)[1].split('-')[2]

        if not os.path.exists(self.vector_used):
            
            shp_ogr = self.data_source.GetLayer()
            
            # Projection
            # Import input shapefile projection
            srsObj = shp_ogr.GetSpatialRef()
            # Conversion to syntax ESRI
            srsObj.MorphToESRI()
            
            # Create output file
            out_ds = self.data_source.GetDriver().CreateDataSource(self.vector_used)
            
            if out_ds is None:
                print('Could not create file')
                sys.exit(1)
                
            #  Specific output layer
            out_layer = out_ds.CreateLayer(str(self.vector_used), srsObj, geom_type=ogr.wkbMultiPolygon)
            
            # Add existing fields 
            for i in range(0, len(self.head_in_read)):
                fieldDefn = ogr.FieldDefn(self.head_in_read[i], ogr.OFTString)
                out_layer.CreateField(fieldDefn)
            
            # Feature for the ouput shapefile
            featureDefn = out_layer.GetLayerDefn()
            
            in_feature = shp_ogr.SetNextByIndex(0) # Polygons initialisation
            in_feature = shp_ogr.GetNextFeature()
            # Loop on input polygons to create a output polygons
            while in_feature:
                
                id_rpg = str(in_feature.GetField(self.field_names[0]))
                # Create a existing polygons in modified rpg list  
                # with minimum size greater than or equal to 1 ha
                try:
                    if self.rm_dupli[id_rpg] and float(self.rm_dupli[id_rpg][2].replace(',','.')) >= self.min_size:
                        # Add .replace(',','.') if the input RPG contains comma instead of point
                    
                        geom = in_feature.GetGeometryRef() # Extract input geometry
            
                        # Create a new polygon
                        out_feature = ogr.Feature(featureDefn)
                    
                        # Set the polygon geometry and attribute
                        out_feature.SetGeometry(geom)
                        for i in range(0, len(self.head_in_read)):
                            out_feature.SetField(self.head_in_read[i], self.rm_dupli[id_rpg][i])
                            
                        # Append polygon to the output shapefile
                        out_layer.CreateFeature(out_feature)
                        
                        # Destroy polygons
                        out_feature.Destroy()    
                        in_feature.Destroy()
                except:
                    pass
                
                # Next polygon
                in_feature = shp_ogr.GetNextFeature()
            
            # Close data
            out_ds.Destroy()  
       
    def mono_rpg(self):        
        """
        Function to extract no duplicated crops.
        
        """
        
        # Table from the RPG input shapefile name
        file_tab = os.path.split(self.vector_used)[1].split('-')[len(os.path.split(self.vector_used)[1].split('-'))-1].split('_')
        # Define the input csv file from RPG input shapefile
        myfile = os.path.split(self.vector_used)[0] + '/' + file_tab[0] + '-' + file_tab[1] + '-GROUPES-CULTURE_' + file_tab[2] +\
                                                                '_' + file_tab[3][:-3] + 'csv'
        my_file = open(myfile, "r")

        in_read = []
        for l in my_file.readlines(): 
            in_read.append(l.split("\n")[0].split(";"))
        
        # Fields name
        for y in in_read[0]:
            if len(y) < 11: # Field names shapefile has to be < 10 charaters
                self.head_in_read.append(y)
            else:
                self.head_in_read.append(y[:10])
        body_in_read = map(list, zip(*in_read[1:])) # Transpose table [[e,e,e],[a,a,a]] -> [[e,a],[e,a],[e,a]]
        
#         self.rm_dupli = [[x, body_in_read[1][body_in_read[0].index(x)], body_in_read[2][body_in_read[0].index(x)]] \
#                                 for x in body_in_read[0] if body_in_read[0].count(x) == 1]
        for x in body_in_read[0]:
            if body_in_read[0].count(x) == 1:
                self.rm_dupli[x] = [x, body_in_read[1][body_in_read[0].index(x)], body_in_read[2][body_in_read[0].index(x)]]
                