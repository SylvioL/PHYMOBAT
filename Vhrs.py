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

import os
import subprocess
from multiprocessing import Process

class Vhrs():
    
    """
    Class to compute Haralick and SFS textures because of OTB application in command line
    
    :param imag: The input image path to compute texture image
    :type imag: str
    :param out_sfs/out_haralick: Output path
    :type out_sfs/out_haralick: str
    :param mp: Boolean variable -> 0 or 1.
    
            - 0 means, not multi-processing
            - 1 means, launch process with multi-processing
    :type mp: int
    """
    
    def __init__(self, imag, mp):
        """Create a new 'Texture' instance
        
        """
        
        self._imag = imag
        self.mp = mp
        
        print('SFS image')
        self.out_sfs = self._imag[:-4] + '_sfs.TIF'
        if not os.path.exists(self.out_sfs):
            print('SFS image don\'t exists !')
            p_sfs = Process(target=self.sfs_texture_extraction)
            p_sfs.start()
            if mp == 0:
                p_sfs.join()
#             self.sfs_texture_extraction()
            
        print('Haralick image')
        self.out_haralick = self._imag[:-4] + '_haralick.TIF'
        if not os.path.exists(self.out_haralick):
            print('Haralick image don\'t exists !')
            p_har = Process(target=self.haralick_texture_extraction, args=('simple', ))
            p_har.start()
            if mp == 0:
                p_har.join()
#             self.haralick_texture_extraction('simple')
        
        if mp == 1:
            if not os.path.exists(self.out_sfs) and not os.path.exists(self.out_haralick):
                p_sfs.join()
                p_har.join()
        
    def sfs_texture_extraction(self):
        
        """
        Function to compute SFS texture image with OTB command line.
            :Example: otbcli_SFSTextureExtraction -in qb_RoadExtract.tif -channel 1 -parameters.spethre 50.0 -parameters.spathre 100 -out SFSTextures.tif
            
            - OTB help :
                * in : Input Image
                * channel : Selected Channel
                * parameters : Texture feature parameters. This group of parameters allows to define SFS texture parameters. The available texture features are SFS’Length, SFS’Width, SFS’PSI, SFS’W-Mean, SFS’Ratio and SFS’SD. They are provided in this exact order in the output image.
                    - parameters.spethre : Spectral Threshold
                    - parameters.spathre : Spatial Threshold
                    - parameters.nbdir : Number of Direction
                    - parameters.alpha : Alpha
                    - parameters.maxcons : Ratio Maximum Consideration Number
                * out : Feature Output Image
                
            Source : http://otbcb.readthedocs.org/en/latest/Applications/app_SFSTextureExtraction.html
        """
              
        process_tocall = ['otbcli_SFSTextureExtraction', '-in', self._imag, '-channel', '2', '-parameters.spethre', '50.0', \
                          '-parameters.spathre', '100', '-out', self.out_sfs]
        
        print(process_tocall)
        subprocess.call(process_tocall) 
        
    def haralick_texture_extraction(self, texture_choice):
        
        """
        Function to compute Haralick texture image with OTB command line.
            :Example: otbcli_HaralickTextureExtraction -in qb_RoadExtract.tif -channel 2 -parameters.xrad 3 -parameters.yrad 3 -texture simple -out HaralickTextures.tif
            
            - OTB help :
                * in : Input Image
                * channel : Selected Channel
                * Texture feature parameters : This group of parameters allows to define texture parameters.
                    - X Radius : X Radius
                    - Y Radius : Y Radius
                    - X Offset : X Offset
                    - Y Offset : Y Offset
                * Image Minimum : Image Minimum
                * Image Maximum : Image Maximum
                * Histogram number of bin : Histogram number of bin 
                * Texture Set Selection Choice of The Texture Set Available choices are :
                    - Simple Haralick Texture Features: This group of parameters defines the 8 local Haralick texture feature output image. The image channels are: Energy, Entropy, Correlation, Inverse Difference Moment, Inertia, Cluster Shade, Cluster Prominence and Haralick Correlation
                    - Advanced Texture Features: This group of parameters defines the 9 advanced texture feature output image. The image channels are: Mean, Variance, Sum Average, Sum Variance, Sum Entropy, Difference of Entropies, Difference of Variances, IC1 and IC2
                    - Higher Order Texture Features: This group of parameters defines the 11 higher order texture feature output image. The image channels are: Short Run Emphasis, Long Run Emphasis, Grey-Level Nonuniformity, Run Length Nonuniformity, Run Percentage, Low Grey-Level Run Emphasis, High Grey-Level Run Emphasis, Short Run Low Grey-Level Emphasis, Short Run High Grey-Level Emphasis, Long Run Low Grey-Level Emphasis and Long Run High Grey-Level Emphasis
                * out : Feature Output Image 
                
            Source : http://otbcb.readthedocs.org/en/latest/Applications/app_HaralickTextureExtraction.html
        
        :param texture_choice: Order texture choice -> Simple / Advanced / Higher
        :type texture_choice: str
        """
        
        process_tocall =  ['otbcli_HaralickTextureExtraction', '-in', self._imag, '-channel', '2', '-parameters.xrad', '3', \
                           '-parameters.yrad', '3', '-texture', texture_choice, '-out', self.out_haralick]
        
        print(process_tocall)
        subprocess.call(process_tocall) 
        