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

import os, sys, subprocess, glob
import numpy as np

class Toolbox():
    """
    Class used to grouped small tools to cut raster or compute statistics on a raster. 
        
    :param imag: Input image (path)
    :type imag: str
    :param vect: Extent shapefile (path)
    :type vect: str
    """
    
    def __init__(self):
        """
        Create a new 'Toolbox' instance
        """
        
        self.imag = ''
        self.vect = ''
    
    def clip_raster(self, **kwargs):
        """
        Function to clip a raster with a vector. The raster created will be in the same folder than the input raster.
        With a prefix *Clip_*.
        
        :kwargs: **rm_rast** (int) - 0 (by default) or 1. Variable to remove the output raster. 0 to keep and 1 to remove.
        
        :returns: str -- variable **outclip**, output raster clip (path).
        """    
        
        rm_rast = kwargs['rm_rast'] if kwargs.get('rm_rast') else 0
        outclip = os.path.split(str(self.imag))[0] + '/Clip_' + os.path.split(str(self.imag))[1]
        if not os.path.exists(outclip) or rm_rast == 1:
            print 'Raster clip of ' + os.path.split(str(self.imag))[1]
            # Command to clip a raster with a shapefile by Gdal
            process_tocall_clip = ['gdalwarp', '-overwrite', '-dstnodata', '-10000', '-q', '-cutline', self.vect, '-crop_to_cutline', '-of', 'GTiff', self.imag, outclip]
            # This is a trick to remove warning with the polygons that touch themselves
            try:
                r = subprocess.call(process_tocall_clip)
                if r == 1:
                    sys.exit(1)
                    
            except SystemExit:
                print("Dissolve vector cut of the validation !!!")
                vect_2 = self.vect[:-4] + '_v2.shp'
                preprocess_tocall = 'ogr2ogr -overwrite ' + vect_2 + ' ' + self.vect + ' -dialect sqlite -sql "SELECT ST_Union(geometry), * FROM ' + \
                                        os.path.basename(self.vect)[:-4] +'"'
                os.system(preprocess_tocall)
                print 'Raster clip of ' + os.path.split(str(self.imag))[1]
                process_tocall_clip = ['gdalwarp', '-overwrite', '-dstnodata', '-10000', '-q', '-cutline', vect_2, '-crop_to_cutline', '-of', 'GTiff', self.imag, outclip]
                subprocess.call(process_tocall_clip)
                for rem in glob.glob(vect_2[:-4] + '*'):
                    os.remove(rem)
                    
        return outclip
    
    def calc_serie_stats(self, table):
        """
        Function to compute stats on temporal cloud and ndvi spectral table
        Ndvi stats : min    max    std    max-min
        
        :param table: Spectral data, cloud raster and ndvi raster
        :type table: numpy.ndarray
        :returns: list of numpy.ndarray -- variable **account_stats**, list of temporal NDVI stats.
                      
                    numpy.ndarray -- variable **account_cloud**, pixel number clear on the area.
        """ 
        
        # Compute stats on these indexes
        ind = ['np.min(tab_ndvi_masked, axis=2)', 'np.max(tab_ndvi_masked, axis=2)', 'np.std(tab_ndvi_masked, axis=2)', \
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
        mask_cloud = np.ma.masked_where((stack_ndvi == -10000) | (tab_cloud != 0), tab_cloud) # Mask values -10000 and > 0(Not cloud)
    #    mask_cloud = (tab_cloud != 0) | (stack_ndvi == -10000)
        tab_ndvi_masked = np.ma.array(stack_ndvi, mask=mask_cloud.mask) # mask_cloud.mask) # Ndvi table with clear values 
                 
        # Stats on the indexes defined above
        account_stats = []
        for i in ind:
            i_stats = eval(i) # Compute stats
            i_stats.fill_value = -10000 # Substitute default fill value by -10000 
            account_stats.append(i_stats.filled()) # Add stats table with true fill value
    
        return account_stats, account_cloud
