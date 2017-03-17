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

import os, sys
import subprocess
import numpy as np
try :
    import ogr, gdal
except :
    from osgeo import ogr, gdal
from rasterstats import *
from collections import *

from RasterSat_by_date import RasterSat_by_date

class Vector():
    """    
    Vector class to extract a area, vector data and zonal statistic (``rasterstats 0.3.2 package``)
    
    :param vector_used: Input/Output shapefile to clip (path)
    :type vector_used: str
    :param vector_cut: Area shapefile (path)
    :type vector_cut: str
    :param data_source: Input shapefile information
    :type data_source: ogr pointer
    :param stats_dict: ``Rasterstats`` results
    :type stats_dict: dict
    :param raster_ds: Raster information for a probably rasterization
    :type raster_ds: gdal pointer
    :param remove_shp: Remove shapefile or not. 0 : don't remove, 1 : remove
    :type remove_shp: int
    :opt: **Remove** (int) - For the remove_shp variable
    
    """
      
    def __init__(self, used, cut, **opt):
        """Create a new 'Vector' instance
               
        """
        self.vector_cut = cut
        self.vector_used = used
        self.remove_shp = opt['Remove'] if opt.get('Remove') else 0

        self.clip_vector()
        
        self.data_source = ''
        if self.data_source == '':
            self.vector_data()
            
        # List of field name
        self.field_names = [self.data_source.GetLayer().GetLayerDefn().GetFieldDefn(l).GetName() \
                       for l in range(self.data_source.GetLayer().GetLayerDefn().GetFieldCount())]
            
        self.stats_dict = defaultdict(list)
        self.raster_ds = None
        
        
    
    def clip_vector(self):
        """
        Function to clip a vector with a vector
        
        """    
        
        outclip = os.path.split(self.vector_used)[0] + '/Clip_' + os.path.split(self.vector_used)[1]
        if not os.path.exists(outclip) or self.remove_shp == 1:
            print 'Clip of ' + os.path.split(self.vector_used)[1]
            # Command to clip a vector with a shapefile by OGR
            process_tocall_clip =  ['ogr2ogr', '-overwrite', '-skipfailures', outclip, self.vector_used, '-clipsrc', self.vector_cut]
            subprocess.call(process_tocall_clip)
        
        # Replace input filename by output filename
        self.vector_used = outclip
        
    def vector_data(self):
        """
        Function to extract vector layer information 
        
        """  
        
        # import ogr variable
        self.data_source = ogr.GetDriverByName('ESRI Shapefile').Open(self.vector_used, 0)
        
        if self.data_source is None:
            print('Could not open file')
            sys.exit(1)
        
        print('Shapefile opening : ' + self.data_source.GetLayer().GetName())

    def close_data(self):
        """
        Function to remove allocate memory 
                
        """        
        
        # Close data sources
        self.data_source.Destroy()
        
        print('Shapefile closing : ' + self.data_source.GetLayer().GetName())
    
    def zonal_stats(self, (inraster, band), **kwargs):
        """
        Function to compute the average in every polygons for a raster
        because of package ``rasterstats`` in */usr/local/lib/python2.7/dist-packages/rasterstats-0.3.2-py2.7.egg/rasterstats/*
        
        :param (inraster,band): inraster -> Input image path, and band -> band number
        :type (inraster,band): tuple
        :kwargs: **rank** (int) - Zonal stats ranking launch
        
                **nb_img** (int) - Number images launched with zonal stats 
        """
        
        ranking = kwargs['rank'] if kwargs.get('rank') else 0
        nb_img = kwargs['nb_img'] if kwargs.get('nb_img') else 1

        print('Compute ' + os.path.split(str(self.vector_used))[1] + ' stats on ' + os.path.split(str(inraster))[1])
        stats = raster_stats(str(self.vector_used), str(inraster),  stats =['mean'], band_num=band)
        
        for i in range(len(stats)):
            temp = defaultdict(lambda : [0]*nb_img)
            for j in range(nb_img):
                try :
                    temp[0][j] = self.stats_dict[i][j]
                except IndexError:
                    pass
            temp[0][ranking] = stats[i].values()[1]
            self.stats_dict[i] = temp[0]
            
        print('End of stats on ' + os.path.split(str(inraster))[1])

    def zonal_stats_pp(self, inraster):
        """
        A zonal statistics ++ to dertermine pxl percent in every polygon
        
        :param inraster: Input image path
        :type inraster: str 
        :returns: dict -- **p_stats** : dictionnary with pxl percent in every polygon. Mainly 'Maj_count' (Majority Value) and 'Maj_count_perc' (Majority Percent)
        
        """
        
        p_stats = raster_stats(str(self.vector_used), str(inraster), stats=['count'], copy_properties=True, categorical=True)
        
        for i in range(len(p_stats)):
            percent = 0.0
            for p in p_stats[i].keys():
                if type(p) == np.float32 and p_stats[i][p]/float(p_stats[i]['count'])*100 > percent:
                    p_stats[i]['Maj_count'] = p
                    p_stats[i]['Maj_count_perc'] = p_stats[i][p]/float(p_stats[i]['count'])*100
                    percent = p_stats[i]['Maj_count_perc']
            if not 'Maj_count' in p_stats[i].keys() or not 'Maj_count_perc' in p_stats[i].keys():
                p_stats[i]['Maj_count']=0
                p_stats[i]['Maj_count_perc']=0
        
        return p_stats
                
    def layer_rasterization(self, raster_head, attribute_r, **kwargs):
        """
        Function to rasterize a vector. Define resolution, projection of the output raster with a raster head.
        And complete the gdal pointer empty properties with the layer's information of the vector and a defined field.
        If a raster has several band, in option you can choice if you want one band or more. 
        
        :param raster_head: Raster path that will look like the final raster of the rasterization
        :type raster_head: str
        :param attribute_r: Field name of the shapefile that contains class names
        :type attribute_r: str
        :kwargs: **choice_nb_b** (int) - Output image number of band. If you choice 1, take first band. If you choice 2, take two first band etc... 
        :returns: str -- **valid_raster** : output raster path from the rasterization
        
        """
        
        # Export a example of a raster out information
        # for the validation shapefile
        example_raster = RasterSat_by_date('', '', [0]) # Call the raster class
        example_raster.choice_nb_b = kwargs['choice_nb_b'] if kwargs.get('choice_nb_b') else 0
        raster_info = example_raster.raster_data(raster_head)# Extract data info
        
        # Define the validation's vector
        valid_raster = self.vector_used[:-3]+'TIF' # Name of the output raster
        if os.path.exists(str(valid_raster)):
            os.remove(valid_raster)
            
        # Create the empty raster with the same properties
        # Condition for the rasters with several bands
        if raster_info[1].RasterCount > 1:
            data_raster = raster_info[0][0]
        else:
            data_raster = raster_info[0]
        info_out = example_raster.create_raster(valid_raster, data_raster, raster_info[1])
        self.raster_ds = example_raster.out_ds
        
        # Virtual rasterize the vector 
        pt_rast = gdal.RasterizeLayer(self.raster_ds, [1], self.data_source.GetLayer(), \
                                      options=["ATTRIBUTE=" + str(attribute_r)])
        
        if pt_rast != 0:
            raise Exception("error rasterizing layer: %s" % pt_rast)
        
        new_data = self.raster_ds.ReadAsArray()
        
        self.raster_ds = None
        # Complete the raster creation
        example_raster.complete_raster(info_out, new_data)
        
        return valid_raster
        
        
        
        

