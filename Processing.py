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
import numpy as np
try :
    import ogr
except :
    from osgeo import ogr

from Toolbox import *
from Seath import Seath
# Class group image
from Archive import Archive
from RasterSat_by_date import RasterSat_by_date
from Vhrs import Vhrs
from Slope import Slope

# Class group vector
from Sample import Sample
from Segmentation import Segmentation
from Rpg import Rpg

from collections import defaultdict
from multiprocessing import Process
from multiprocessing.managers import BaseManager, DictProxy

class Processing():
    
    """
    Main processing. This class launch the others system classes. It take into account
    CarHab classification method MOBA. 
    
    This way is broken down into 3 parts :
        - Image Processing (Search, download and processing)
        - Vector Processing (Optimal threshold, Sample processing)
        - Classification  
    
    **Main parameters**
    
    :param captor_project: Satellite captor name
    :type captor_project: str
    :param classif_year: Classification year
    :type classif_year: str
    :param nb_avalaible_images: Number download available images
    :type nb_avalaible_images: int
    :param path_folder_dpt: Main folder path
    :type path_folder_dpt: str
    :param folder_archive: Archive downloaded folder path
    :type folder_archive: str
    :param folder_processing: Processing folder name. By default : 'Traitement'
    :type folder_processing: str
    :param path_area: Study area shapefile
    :type path_area: str
    :param path_ortho: VHRS image path
    :type path_ortho: str
    :param path_mnt: MNT image path
    :type path_mnt: str
    :param path_segm: Segmentation shapefile
    :type path_segm: str
    
    **Id information to download on theia platform**
    
    :param user: Connexion Username
    :type user: str
    :param password: Connexion Password
    :type password: str
    
    **Output parameters**
    
    :param output_name_moba: Output classification shapefile 
    :type output_name_moba: str
    :param out_fieldname_carto: Output shapefile field name
    :type out_fieldname_carto: list of str
    :param out_fieldtype_carto: Output shapefile field type
    :type out_fieldtype_carto: list of str (eval ogr pointer)
    
    **Sample parameters**
    
    :param fieldname_args: Sample field names 2 by 2
    :type fieldname_args: list of str
    :param class_args: Sample class names 2 by 2
    :type class_args: list of str
    :param sample_name: List of sample name (path)
    :type sample_name: list of str
    :param list_nb_sample: Number of polygons for every sample
    :type list_nb_sample: list of int
    
    **Multi-processing parameters**
    
    :param mp: Boolean variable -> 0 or 1.
    
            - 0 means, not multi-processing
            - 1 means, launch process with multi-processing
    :type mp: int
    """
    
    def __init__(self):
        
        # Used variables
        self.captor_project = ''
        self.classif_year = ''
        self.path_folder_dpt = ''
        self.folder_archive = ''
        self.folder_processing = 'Traitement'
        self.path_area = ''
        self.path_ortho = ''
        self.path_mnt = ''
        self.path_segm = ''
        self.output_name_moba = ''
        
        # Id information to download on theia platform
        self.user = ''
        self.password = ''

        # List of output raster path
        self.raster_path = []
        self.list_band_outraster = []
        
        # Class name
        self.in_class_name = ['Non Vegetation semi-naturelle', 'Vegetation semi-naturelle',\
                         'Herbacees', 'Ligneux', \
                         'Ligneux mixtes', 'Ligneux denses',\
                         'Agriculture', 'Eboulis', \
                         'Forte phytomasse', 'Moyenne phytomasse', 'Faible phytomasse']
        # Sample field names 2 by 2
        self.fieldname_args = []
#                                'CODE_GROUP', 'CODE_GROUP',\
#                           'echant', 'echant',\
#                           'echant', 'echant']
        # Sample class names 2 by 2
        self.class_args = []
#                            '1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 14, 15, 20, 21, 22, 23, 24, 26, 28', '18',\
#                       'H','LF, LO',\
#                       'LF', 'LO']
        
        # Decision tree combination
        self.tree_direction = [[0, 6],\
                          [0, 7],\
                          [1, 3, 4],\
                          [1, 3, 5],\
                          [1, 2, 8],\
                          [1, 2, 9],\
                          [1, 2, 10]] # [['Cultures'],['Semi-naturelles', 'Herbacees', 'Forte phytomasse'], ...
                                    # ..., ['Semi-naturelles', 'Ligneux', 'Ligneux denses']]
        # Slope degrees
        self.slope_degree = 30
        
        # Output shapefile field name
        self.out_fieldname_carto = ['ID', 'AREA'] #, 'NIVEAU_1', 'NIVEAU_2', 'NIVEAU_3', 'POURC']
        # Output shapefile field type
        self.out_fieldtype_carto = [ogr.OFTString, ogr.OFTReal] #, ogr.OFTString, ogr.OFTString, ogr.OFTString, ogr.OFTReal]
        
        # List of sample name path
        self.sample_name = []
        # List of number sample
        self.list_nb_sample = []
        # Number download available images
        self.nb_avalaible_images = 0
        # Multi-processing variable
        self.mp = 1
        
        # Function followed
        self.check_download = ''
        self.decis = {}
        # Images after processing images
        self.out_ndvistats_folder_tab = defaultdict(list)
        
    def i_tree_direction(self):
        
        """
        Interface function to can extract one level or two levels of the final classification 
        """

        if len(self.out_fieldname_carto) == 3:
            self.tree_direction = [[0], [1]]
            
        if len(self.out_fieldname_carto) == 4:
            self.tree_direction = [[0, 6], [0, 7], [1, 2], [1, 3]]
        
    def i_download(self, dd):
        
        """
        Interface function to download archives on the website Theia Land. This function extract 
        the number of downloadable image with :func:`Archive.Archive.listing`.
        
        Then, this function download :func:`Archive.Archive.download` and unzip :func:`Archive.Archive.decompress` images
        in the archive folder (**folder_archive**).
        
        :param dd: Boolean variable to launch download images -> 0 or 1.
    
            - 0 means, not downloading
            - 1 means, launch downloading
        :type dd: int
        """
        
        self.folder_archive = self.captor_project + '_PoleTheia'
        self.check_download = Archive(self.captor_project, self.classif_year, self.path_area, self.path_folder_dpt, self.folder_archive)
        self.check_download.listing()
        self.nb_avalaible_images = len(self.check_download.list_archive)
        # check_download.set_list_archive_to_try(check_download.list_archive[:3])
        if dd == 1:
#             self.check_download.download_auto(self.user, self.password)
            self.check_download.download_auto(self.user, self.password)
            self.check_download.decompress()
     
    def i_img_sat(self):
        
        """
        Interface function to processing satellite images:
        
            1. Clip archive images and modify Archive class to integrate clip image path.
            With :func:`Toolbox.clip_raster` in ``Toolbox`` module.
        
            2. Search cloud's percentage :func:`RasterSat_by_date.RasterSat_by_date.pourc_cloud`, select 
            image and compute ndvi index :func:`RasterSat_by_date.RasterSat_by_date.calcul_ndvi`. If cloud's percentage is 
            greater than 40%, then not select and compute ndvi index.
        
            3. Compute temporal stats on ndvi index [min, max, std, min-max]. With :func:`Toolbox.calc_serie_stats` 
            in ``Toolbox`` module.
            
            4. Create stats ndvi raster and stats cloud raster.
            
            >>> import RasterSat_by_date
            >>> stats_test = RasterSat_by_date(class_archive, big_folder, one_date)
            >>> stats_test.create_raster(in_raster, stats_data, in_ds)
        """

        # Clip archive images and modify Archive class to integrate clip image path
        for clip in self.check_download.list_img:
            clip_index = self.check_download.list_img.index(clip)
            self.check_download.list_img[clip_index][3] = clip_raster(clip[3], self.path_area) # Multispectral images
            self.check_download.list_img[clip_index][4] = clip_raster(clip[4], self.path_area) # Cloud images
           
        # Images pre-processing
        spectral_out = []
        for date in self.check_download.single_date:
               
            check_L8 = RasterSat_by_date(self.check_download, self.folder_processing, date)
            check_L8.mosaic_by_date()
             
            # Search cloud's percentage, select image and compute ndvi index if > cl
            cl = check_L8.pourc_cloud(check_L8._one_date[3], check_L8._one_date[4])
            if cl > 0.60:
                check_L8.calcul_ndvi(check_L8._one_date[3])
                spectral_out.append(check_L8._one_date)
        
        # Compute temporal stats on ndvi index [min, max, std, min-max]
        spectral_trans = np.transpose(np.array(spectral_out, dtype=object))
        stats_name = ['Min', 'Max', 'Std', 'MaxMin']
        stats_ndvi, stats_cloud = calc_serie_stats(spectral_trans)

        # Create stats ndvi raster and stats cloud raster
        stats_L8 = RasterSat_by_date(self.check_download, self.folder_processing, [int(self.classif_year)])
        # Stats cloud raster
        out_cloud_folder = stats_L8._class_archive._folder + '/' + stats_L8._big_folder + '/' + self.classif_year + \
                           '/Cloud_number_' + self.classif_year + '.TIF'
        stats_L8.create_raster(out_cloud_folder, stats_cloud, stats_L8.raster_data(self.check_download.list_img[0][4])[1])
           
        # Stats ndvi rasters        
        for stats_index in range(len(stats_ndvi)):
            out_ndvistats_folder = stats_L8._class_archive._folder + '/' + stats_L8._big_folder + '/' + self.classif_year + \
                           '/' + stats_name[stats_index] + '_' + self.classif_year + '.TIF'
            self.out_ndvistats_folder_tab[stats_index] = out_ndvistats_folder
            stats_L8.create_raster(out_ndvistats_folder, stats_ndvi[stats_index], stats_L8.raster_data(self.check_download.list_img[0][4])[1])
        
    def i_slope(self):
        """
        Interface function to processing slope raster. From a MNT, and with a command line gdal,
        this function compute slope in degrees :func:`Slope.Slope`.
 
        """
        
        path_mnt = clip_raster(self.path_mnt, self.path_area)
        study_slope = Slope(path_mnt)
        study_slope.extract_slope()# Call this function to compute slope raster
        self.path_mnt = study_slope.out_mnt
    
    def i_vhrs(self):#, vs):  
        """
        Interface function to processing VHRS images. It create two OTB texture images :func:`Vhrs.Vhrs` : SFS Texture and Haralick Texture

        """
  
        # Create texture image
        # Clip orthography image 
        path_ortho = clip_raster(self.path_ortho, self.path_area)
        texture_irc = Vhrs(path_ortho, self.mp)
        self.out_ndvistats_folder_tab['sfs'] = texture_irc.out_sfs
        self.out_ndvistats_folder_tab['haralick'] = texture_irc.out_haralick
        
    def i_images_processing(self, vs): 
        
        """
        Interface function to launch processing VHRS images :func:`i_vhrs` and satellite images :func:`i_img_sat` in multi-processing.
        
        :param vs: Boolean variable to launch processing because of interface checkbox -> 0 or 1.
    
            - 0 means, not texture processing
            - 1 means, launch texture processing
        :type vs: int
        """
        
        # Multiprocessing
        mgr = BaseManager()
        mgr.register('defaultdict', defaultdict, DictProxy)
        mgr.start()
        self.out_ndvistats_folder_tab = mgr.defaultdict(list)
        
        p_img_sat = Process(target=self.i_img_sat)
        p_img_sat.start()
        if self.mp == 0:
            p_img_sat.join()
        
        if vs == 1:
            p_vhrs = Process(target=self.i_vhrs)#, args=(vs, ))
            p_vhrs.start()
            p_vhrs.join()
        
        if self.mp == 1:
            p_img_sat.join()
        
        # List of output raster path
        self.raster_path.append(self.out_ndvistats_folder_tab[0])
        # List of output raster band
        self.list_band_outraster.append(1)
        
        if vs == 1:
            self.raster_path.append(self.out_ndvistats_folder_tab['sfs'])
            self.list_band_outraster.append(4)
            self.raster_path.append(self.out_ndvistats_folder_tab['haralick'])
            self.list_band_outraster.append(2)
        
        # To slope, to extract scree
        if self.path_mnt != '':
            self.raster_path.append(self.path_mnt)
            self.list_band_outraster.append(1)
            
        self.raster_path.append(self.out_ndvistats_folder_tab[1])
        # example raster path tab :
        #                [path_folder_dpt + '/' + folder_processing + '/' + classif_year + '/Min_2014.TIF',\
        #                os.path.dirname(path_ortho) + '/Clip_buffer_surface_dep_18_IRCOrtho65_2m_sfs.TIF',\
        #                os.path.dirname(path_ortho) + '/Clip_buffer_surface_dep_18_IRCOrtho65_2m_haralick.TIF',\
        #                path_folder_dpt + '/' + folder_processing + '/' + classif_year + '/Max_2014.TIF']
        
        # List of output raster band
        self.list_band_outraster.append(1) #[1, 4, 2, 1]
        
        print("End of images processing !")


    def i_rpg(self, path_rpg): 
        """
        Interface function to extract mono rpg crops.
        
        :param path_rpg: Input RPG shapefile.
        :type path_rpg: str
        
        :returns: str -- variable **Rpg.vector_used**, output no duplicated crops shapefile (path).
        """
               
        # Extract mono rpg crops
        mono_sample = Rpg(path_rpg, self.path_area)
        mono_sample.mono_rpg()
        mono_sample.create_new_rpg_files()
        print('End of RPG processing')
        
        return mono_sample.vector_used
         
        
    def i_sample(self):
        """
        Interface function to compute threshold with various sample.
        
        It create samples 2 by 2 with kwargs field names and class :func:`Sample.Sample.create_sample`. 
        Then, it compute zonal statistics by polygons :func:`Vector.Sample.zonal_stats`.
        
        With zonal statistics computed, a optimal threshold is determined :func:`Seath.Seath.separability_and_threshold`.
        
        .. warning:: :func:`Seath.Seath.separability_and_threshold` does not always allow to discriminate optimal threshold. 
                    Then, this function will be launch at least ten time until it reaches a optimal threshold.
        """
        
        # Compute threshold with various sample
        i_s = 0
        while i_s < 10:
            try :
                sample_rd = {}
                for sple in range(len(self.sample_name) * 2):
                    kwargs = {}
                    kwargs['fieldname'] = self.fieldname_args[sple]
                    kwargs['class'] = self.class_args[sple]
                    sample_rd[sple] = Sample(self.sample_name[sple/2], self.path_area, self.list_nb_sample[sple/2])
                    sample_rd[sple].create_sample(**kwargs)
                    sample_rd[sple].zonal_stats((self.raster_path[sple/2], self.list_band_outraster[sple/2]))
                   
                for th_seath in range(len(self.sample_name)):
                    self.decis[th_seath] = Seath()
                    self.decis[th_seath].value_1 = sample_rd[th_seath*2].stats_dict
                    self.decis[th_seath].value_2 = sample_rd[th_seath*2 + 1].stats_dict
                    self.decis[th_seath].separability_and_threshold()
                
                i_s = 10
            except:
                i_s = i_s + 1

    def i_classifier(self): 
        """
        Interface function to launch decision tree classification with a input segmentation :func:`Segmentation.Segmentation`.
        
        This function store optimal threshold by class **Segmentation.out_threshold**. Then compute zonal statistics by polygons
        for every images in multi-processing (if **mp** = 1).

        """ 
        
        # Multiprocessing
        mgr = BaseManager()
        mgr.register('defaultdict', defaultdict, DictProxy)
        mgr.start()
        multi_process_var = [] # Multi processing variable
          
        # Extract final cartography
        out_carto = Segmentation(self.path_segm, self.path_area) 
        out_carto.output_file = self.output_name_moba
        out_carto.out_class_name = self.in_class_name
        out_carto.out_threshold = []
        for ind_th in range(len(self.sample_name)):
            out_carto.out_threshold.append(self.decis[ind_th].threshold[0])
            if '>' in self.decis[ind_th].threshold[0]:
                out_carto.out_threshold.append(self.decis[ind_th].threshold[0].replace('>', '<='))
            elif '<' in self.decis[ind_th].threshold[0]:
                out_carto.out_threshold.append(self.decis[ind_th].threshold[0].replace('<', '>='))
        #     out_carto.zonal_stats((raster_path[ind_th], list_band_outraster[ind_th]))
            multi_process_var.append([self.raster_path[ind_th], self.list_band_outraster[ind_th]])
         
        # Compute zonal stats on slope raster
        multi_process_var.append([self.raster_path[ind_th+1], self.list_band_outraster[ind_th+1]])
        out_carto.out_threshold.append('<'+str(self.slope_degree)) # To agriculture
        out_carto.out_threshold.append('>='+str(self.slope_degree)) # To scree
        # Compute zonal stats on Max NDVI raster  
        try:  
            # out_carto.zonal_stats((raster_path[ind_th+1], list_band_outraster[ind_th+1]))
            multi_process_var.append([self.raster_path[ind_th+2], self.list_band_outraster[ind_th+2]])
            # Compute stats twice, because there is 3 classes and not 2
            # out_carto.zonal_stats((raster_path[ind_th+1], list_band_outraster[ind_th+1]))
            multi_process_var.append([self.raster_path[ind_th+2], self.list_band_outraster[ind_th+2]])
        except:
            print('Not max ndvi on the 3rd floor')

        # Compute zonal stats with multi processing
        out_carto.stats_dict = mgr.defaultdict(list)
        p = []
        kwargs = {}
        for i in range(len(multi_process_var)):
            kwargs['rank'] = i
            kwargs['nb_img'] = len(multi_process_var)
            p.append(Process(target=out_carto.zonal_stats, args=(multi_process_var[i], ), kwargs=kwargs))
            p[i].start()
            
            if self.mp == 0:
                p[i].join()
        
        if self.mp == 1:       
            for i in range(len(multi_process_var)):
                p[i].join()

        # If there is more one fieldnames line edit fulled in classification tab
        if len(self.sample_name) > 2:
            # Compute the biomass and density distribution
            out_carto.compute_biomass_density()
            
        out_carto.class_tab_final = defaultdict(list)
        self.i_tree_direction()
        out_carto.decision_tree(self.tree_direction)
        
        # If there is more one fieldnames line edit fulled in classification tab
        if len(self.sample_name) > 2:     
            # Compute biomass and density scale
            out_carto.append_scale(self.in_class_name[2], 'self.stats_dict[ind_stats][3]/self.max_bio')
            out_carto.append_scale(self.in_class_name[3], 'self.stats_dict[ind_stats][2]/self.max_wood_idm')
          
        # Final cartography
        out_carto.create_cartography(self.out_fieldname_carto, self.out_fieldtype_carto)
        