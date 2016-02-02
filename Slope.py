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

import os
import subprocess

class Slope():
    
    """
    Class to compute a slope raster
    
    :param mnt: Digital Elevation Model (DEM) path
    :type mnt: str
    :param out_mnt: slope raster path
    :type out_mnt: str

    """
    
    def __init__(self, mnt):
        """
        Create a new 'Slope' instance
        """
        
        self.mnt = mnt
        self.out_mnt = ''
        
    def extract_slope(self):
        
        """
        Function to compute slope in GDAL command line.
        """
        self.out_mnt = self.mnt[:-4] + '_slope.TIF'
        if not os.path.exists(self.out_mnt):
            # Launch gdaldem command line to have slope in degrees
            process_tocall = ['gdaldem', 'slope', self.mnt, self.out_mnt]
    
            print(process_tocall)
            subprocess.call(process_tocall)
            
