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
import random
import numpy as np
from Vector import Vector
try :
    import ogr
except :
    from osgeo import ogr

class Sample(Vector):
    
    """
    Vector class inherits the super vector class properties. This class create training sample.
    
    :param vector_used: Input/Output shapefile to clip (path)
    :type vector_used: str
    :param vector_cut: Area shapefile (path)
    :type vector_cut: str
    :param nb_sample: Number of polygons for every sample
    :type nb_sample: int
    :param vector_val: Output shapefile to validate the futur classification
    :type vector_val: str
    
    :opt: Refer to the Vector class
    """
    
    def __init__(self, used, cut, nb_sample, **opt):
        """Create a new 'Sample' instance
               
        """
        Vector.__init__(self, used, cut, **opt)
        
        self._nb_sample = nb_sample
        self.vector_val = ''
    
    def create_sample(self, **kwargs):
        """
        Function to create a sample shapefile of a specific class
        
        :kwargs: **fieldname** (list of str) - Fieldname in the input shapefile (if the user want select polygons of the class names specific)
                
                **class** (list of str) - class names in the input shapefile (with fieldname index).
                Can use one or several classes like this --> example : [classname1, classname2, ...]
        """
        
        kw_field = kwargs['fieldname'] if kwargs.get('fieldname') else ''
        kw_classes = kwargs['class'] if kwargs.get('class') else ''
        
        # If the users want select polygons with a certain class name
        if kw_field and kw_classes:
            # The random sample with class name selected only
            random_sample = np.array(random.sample(self.select_random_sample(kw_field, kw_classes), int(self._nb_sample)))
        else:
            # The random sample without class name selected
            random_sample = np.array(random.sample(range(self.data_source.GetLayer().GetFeatureCount()), self._nb_sample))
            
        # Output shapefile of the sample's polygons (path)
        self.vector_used = self.vector_used[:-4] + '_' + kw_classes.replace(',','').replace(' ','') + 'rd.shp'
        # Fill and create the sample shapefile
        self.fill_sample(self.vector_used, random_sample[:len(random_sample)/2])
        # Output shapefile of the validate polygon (path)
        self.vector_val = self.vector_used[:-6] + 'val.shp'
        # Fill and create the validate polygons shapefile
        self.fill_sample(self.vector_val, random_sample[len(random_sample)/2:])
       
    def select_random_sample(self, kw_field, kw_classes):        
        """
        Function to select id with class name specific only. This function is used in :func:`create_sample`

        :param kw_field: Field name in the input shapefile
        :type kw_field: str
        :param kw_classes: Class names in the input shapefile like this --> 'classname1, classname2'
        :type kw_classes: str
        :returns: list -- variable **select_id**, List of id with a class name specific.
        """
        
        # Convert string in a list. For that, it remove
        # space and clip this string with comma (Add everywhere if the script modified
        # because the process work with a input string)
        kw_classes = kw_classes.replace(' ','').split(',')
        
        # List of class name id
        select_id = []
         
        shp_ogr = self.data_source.GetLayer()
        
        # Loop on input polygons
        in_feature = shp_ogr.SetNextByIndex(0) # Initialisation
        in_feature = shp_ogr.GetNextFeature()
        while in_feature:
            
            # if polygon is a defined class name 
            ## .replace('0','') to remove '0' in front of for example '1' (RPG -> '01')
            if in_feature.GetField(self.field_names[self.field_names.index(kw_field)]).replace('0','') in kw_classes:
                
                # Add id in the extract list
                select_id.append(in_feature.GetFID())

                in_feature.Destroy()
                
            in_feature = shp_ogr.GetNextFeature()
        return select_id
    
    def fill_sample(self, output_sample, polygon, **opt):
        
        """
        Function to fill and create the output sample shapefile. This function is used in :func:`create_sample`
        to create samples polygons and validated polygons (to the take out the precision of the classification)

        :param output_sample: Path of the output shapefile
        :type output_sample: str
        :param polygon: Identity of the selected random polygons. If this variable = 0, the processing will take all polygons 
        :type polygon: list or int      
        
        :opt: **add_fieldname** (int) - Variable to kown if add a field. By default non (0), if it have to add (1)
        
                **fieldname** (str) - Fieldname to add in the input shapefile
                
                **class** (int) - class names in integer to add in the input shapefile
        """
        
        # In option to add a integer field
        add_field = opt['add_fieldname'] if opt.get('add_fieldname') else 0
        opt_field = opt['fieldname'] if opt.get('fieldname') else ''
        opt_class = opt['class'] if opt.get('class') else 0
        
        shp_ogr = self.data_source.GetLayer()
        
        # To take all polygon
        if type(polygon) == int:
            polygon = range(shp_ogr.GetFeatureCount())
        
        # Projection
        # Import input shapefile projection
        srsObj = shp_ogr.GetSpatialRef()
        # Conversion to syntax ESRI
        srsObj.MorphToESRI() 
               
        ## Remove the output shapefile if it exists
        if os.path.exists(output_sample):
            self.data_source.GetDriver().DeleteDataSource(output_sample)
        out_ds = self.data_source.GetDriver().CreateDataSource(output_sample)
        
        if out_ds is None:
            print('Could not create file')
            sys.exit(1)
            
        #  Specific output layer
        out_layer = out_ds.CreateLayer(str(output_sample), srsObj, geom_type=ogr.wkbMultiPolygon)
        
        # Add existing fields 
        for i in range(0, len(self.field_names)):
            # use the input FieldDefn to add a field to the output
            fieldDefn = shp_ogr.GetFeature(0).GetFieldDefnRef(self.field_names[i])
            out_layer.CreateField(fieldDefn)
            
        # In Option : Add a integer field
        if add_field == 1:
            new_field = ogr.FieldDefn(opt_field, 0)
            shp_ogr.CreateField(new_field)
        
        # Feature for the ouput shapefile
        featureDefn = out_layer.GetLayerDefn()
        
        # Loop on the input elements
        # Create a existing polygons in random list    
        for cnt in polygon:
            
            # Select input polygon by id
            in_feature = shp_ogr.SetNextByIndex(cnt)
            in_feature = shp_ogr.GetNextFeature()
            
            geom = in_feature.GetGeometryRef() # Extract input geometry

            # Create a new polygon
            out_feature = ogr.Feature(featureDefn)

            # Set the polygon geometry and attribute
            out_feature.SetGeometry(geom)
            for i in range(0, len(self.field_names)):
                out_feature.SetField(self.field_names[i], in_feature.GetField(self.field_names[i]))
            # In Option : Add a integer field
            if add_field == 1:
                out_feature.SetField(opt_field, opt_class)
                
            # Append polygon to the output shapefile
            out_layer.CreateFeature(out_feature)
    
            # Destroy polygons
            out_feature.Destroy()    
            in_feature.Destroy()
            
        # Close data
        out_ds.Destroy()        