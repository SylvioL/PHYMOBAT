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
try :
    import ogr, gdal
except :
    from osgeo import ogr, gdal
from rasterstats import *
from collections import *

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
    """
      
    def __init__(self, used, cut):
        """Create a new 'Vector' instance
               
        """
        self.vector_cut = cut
        self.vector_used = used
        self.clip_vector()
        
        self.data_source = ''
        if self.data_source == '':
            self.vector_data()
            
        # List of field name
        self.field_names = [self.data_source.GetLayer().GetLayerDefn().GetFieldDefn(l).GetName() \
                       for l in range(self.data_source.GetLayer().GetLayerDefn().GetFieldCount())]
            
        self.stats_dict = defaultdict(list)
    
    def clip_vector(self):
        """
        Function to clip a vector with a vector
        
        """    
        
        outclip = os.path.split(self.vector_used)[0] + '/Clip_' + os.path.split(self.vector_used)[1]
        if not os.path.exists(outclip):
            print 'Clip of ' + os.path.split(self.vector_used)[1]
            # Command to clip a vector with a shapefile by OGR
            process_tocall_clip =  ['ogr2ogr', outclip, self.vector_used, '-clipsrc', self.vector_cut]
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

        
        print(os.path.split(self.vector_used)[1] + ' stats on ' + os.path.split(inraster)[1])
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
            
            
        print('End of stats on ' + os.path.split(inraster)[1])

    def rasterize_vector(self, raster_dout, attribute_r):
        """
        Function to rasterize a vector.
        
        :param raster_out: Raster path to take those informations
        :type raster_out: str
        :param attribute_r: Value field pixels for the raster out 
        :type attribute_r: str
        
        """
        
        pt_rast = gdal.RasterizeLayer(raster_dout, [1], self.data_source.GetLayer(), options=["ATTRIBUTE=" + str(attribute_r)])
        if pt_rast != 0:
            raise Exception("error rasterizing layer: %s" % pt_rast)

