#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of PHYMOBAT 2.0.
# Copyright 2016 Sylvio Laventure (IRSTEA - UMR TETIS)
# 
# PHYMOBAT 2.0 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# PHYMOBAT 2.0 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with PHYMOBAT 2.0.  If not, see <http://www.gnu.org/licenses/>.

import os, sys, math
import numpy as np
import subprocess
from sklearn.ensemble import RandomForestClassifier
try :
    import ogr, gdal
except :
    from osgeo import ogr, gdal

from Toolbox import Toolbox
from Seath import Seath
from Precision_moba import Precision_moba
# Class group image
from Archive import Archive
from RasterSat_by_date import RasterSat_by_date
from Vhrs import Vhrs
from Slope import Slope

# Class group vector
from Vector import Vector
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
        - Validation 
    
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
        
        # TODO : Change index of the classes -> Harbacées 6 / Ligneux 7 by Agriculuture 4 / Eboulis 5
        
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
        self.tree_direction = [[0],\
                          [0],\
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
        
        # Validation shapefiles information
        self.valid_shp = []
        
        # Radom Forest Model
        # Set the parameters of this random forest from the estimator 
        self.rf = RandomForestClassifier(n_estimators=500, criterion='gini', max_depth=None, min_samples_split=2, \
                                        min_samples_leaf=1, max_features='auto', \
                                        bootstrap=True, oob_score=True)
        
    def i_tree_direction(self):
        
        """
        Interface function to can extract one level or two levels of the final classification 
        """

        if len(self.out_fieldname_carto) == 3:
            self.tree_direction = [[0], [1]]
            
        if len(self.out_fieldname_carto) == 4:
            self.tree_direction = [[0], [0], [1, 2], [1, 3]]
        
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
    
    def i_glob(self):
        """
        Function to load existing images to launch the processing. 
        It need to archives. Then, to select processing images, select archives 
        
        """
        
        self.folder_archive = self.captor_project + '_PoleTheia'
        self.check_download = Archive(self.captor_project, self.classif_year, self.path_area, self.path_folder_dpt, self.folder_archive)
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
            >>> stats_test.complete_raster(stats_test.create_raster(in_raster, stats_data, in_ds), stats_data)
        """

        # Clip archive images and modify Archive class to integrate clip image path
        for clip in self.check_download.list_img:
            clip_index = self.check_download.list_img.index(clip)
            
            current_list = Toolbox()
            current_list.imag = clip[3]
            current_list.vect = self.path_area
            self.check_download.list_img[clip_index][3] = current_list.clip_raster() # Multispectral images
            
            current_list.imag = clip[4]
            self.check_download.list_img[clip_index][4] = current_list.clip_raster() # Cloud images
           
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
        stats_name = ['Min', 'Date', 'Max', 'Std', 'MaxMin']
        stats_ndvi, stats_cloud = current_list.calc_serie_stats(spectral_trans)
        
        # Create stats ndvi raster and stats cloud raster
        stats_L8 = RasterSat_by_date(self.check_download, self.folder_processing, [int(self.classif_year)])
        # Stats cloud raster
        out_cloud_folder = stats_L8._class_archive._folder + '/' + stats_L8._big_folder + '/' + self.classif_year + \
                           '/Cloud_number_' + self.classif_year + '.TIF'
        stats_L8.complete_raster(stats_L8.create_raster(out_cloud_folder, stats_cloud, \
                                                         stats_L8.raster_data(self.check_download.list_img[0][4])[1]), \
                                 stats_cloud)
        
        # Stats ndvi rasters        
        for stats_index in range(len(stats_ndvi)):
            out_ndvistats_folder = stats_L8._class_archive._folder + '/' + stats_L8._big_folder + '/' + self.classif_year + \
                           '/' + stats_name[stats_index] + '_' + self.classif_year + '.TIF'
            self.out_ndvistats_folder_tab[stats_index] = out_ndvistats_folder
            stats_L8.complete_raster(stats_L8.create_raster(out_ndvistats_folder, stats_ndvi[stats_index], \
                                                            stats_L8.raster_data(self.check_download.list_img[0][4])[1]), \
                                     stats_ndvi[stats_index])
        
    def i_slope(self):
        """
        Interface function to processing slope raster. From a MNT, and with a command line gdal,
        this function compute slope in degrees :func:`Slope.Slope`.
 
        """
        
        current_path_mnt = Toolbox()
        current_path_mnt.imag = self.path_mnt
        current_path_mnt.vect = self.path_area
        path_mnt = current_path_mnt.clip_raster()
        
        study_slope = Slope(path_mnt)
        study_slope.extract_slope()# Call this function to compute slope raster
        self.path_mnt = study_slope.out_mnt
    
    def i_vhrs(self):#, vs):
        """
        Interface function to processing VHRS images. It create two OTB texture images :func:`Vhrs.Vhrs` : SFS Texture and Haralick Texture
        
        """

        # Create texture image
        # Clip orthography image 
        current_path_ortho = Toolbox()
        current_path_ortho.imag = self.path_ortho
        current_path_ortho.vect = self.path_area
        path_ortho = current_path_ortho.clip_raster()
        
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
            
        self.raster_path.append(self.out_ndvistats_folder_tab[2])
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
        # If exists, do not create a mono rpg file
        if os.path.basename(path_rpg)[:5]!='MONO_':
            mono_sample.mono_rpg()
            mono_sample.create_new_rpg_files()
        else:
            print('MONO RPG file exists already !!!')
        print('End of RPG processing')
        
        return mono_sample.vector_used
         
    def i_sample(self):
        """
        Interface function to compute threshold with various sample. It also extract a list of validation layer (shapefile) 
        to compute the precision of the next classification :func:`i_validate`. 
        
        It create samples 2 by 2 with kwargs field names and class :func:`Sample.Sample.create_sample`. 
        Then, it compute zonal statistics by polygons :func:`Vector.Sample.zonal_stats`.
        
        With zonal statistics computed, a optimal threshold is determined :func:`Seath.Seath.separability_and_threshold` that
        will print in a text file .lg in the main folder.
        
        .. warning:: :func:`Seath.Seath.separability_and_threshold` does not always allow to discriminate optimal threshold. 
                    Then, this function will be launch at least ten time until it reaches a optimal threshold.
        """
        
        # Compute threshold with various sample
        i_s = 0
        while i_s < 10:
            try :
                self.valid_shp = []
                sample_rd = {}
                for sple in range(len(self.sample_name) * 2):
                    kwargs = {}
                    kwargs['fieldname'] = self.fieldname_args[sple]
                    kwargs['class'] = self.class_args[sple]
                    sample_rd[sple] = Sample(self.sample_name[sple/2], self.path_area, self.list_nb_sample[sple/2])
                    sample_rd[sple].create_sample(**kwargs)
                    sample_rd[sple].zonal_stats((self.raster_path[sple/2], self.list_band_outraster[sple/2]))
                    
                    # Add the validation shapefile
                    self.valid_shp.append([sample_rd[sple].vector_val, kwargs['fieldname'], kwargs['class']])
                
                # Search the optimal threshold by class 
                # Open a text file to print stats of Seath method
                file_J = self.path_folder_dpt + '/log_J.lg'
                f = open(file_J, "wb")
                for th_seath in range(len(self.sample_name)):
                    self.decis[th_seath] = Seath()
                    self.decis[th_seath].value_1 = sample_rd[th_seath*2].stats_dict
                    self.decis[th_seath].value_2 = sample_rd[th_seath*2 + 1].stats_dict
                    self.decis[th_seath].separability_and_threshold()
                    
                    # Print the J value in the text file .lg
                    f.write('For ' + str(self.sample_name[th_seath]) + ' :\n')
                    f.write('J = ' + str(self.decis[th_seath].J[0]) +'\n')
                    f.write('The class 1 ' + str(self.decis[th_seath].threshold[0]) +'\n')
                    
                f.close()    
                i_s = 20
            except:
                i_s = i_s + 1
        # Method to stop the processus if there is not found a valid threshold
        if i_s != 20:
            print 'Problem in the sample processing !!!'
            sys.exit(1)
    
    def i_sample_rf(self):
        """
        This function build a random forest trees like model to create a final classification.
        All of This using the method described in the :func:`i_validate` function and because
        of sklearn module.
        """
        
        X_rf = []
        y_rf = []
        sample_rd = {}            
        # Tricks to add all textural indexes
        rm_index = 1
        self.raster_path.remove(self.raster_path[rm_index]) # Remove SFS layer
        self.raster_path.remove(self.raster_path[rm_index]) # Remove Haralick layer
        self.list_band_outraster.remove(self.list_band_outraster[rm_index]) # Remove band of the layer
        self.list_band_outraster.remove(self.list_band_outraster[rm_index]) # Remove band of the layer
        # Add all layers in the simple index haralick
        for add_layer in range(8):
            self.raster_path.insert(add_layer+1, self.out_ndvistats_folder_tab['haralick'])
            self.list_band_outraster.insert(add_layer+1, add_layer+1)
        # Add all layers in the SFS index
        for add_layer in range(6):
            self.raster_path.insert(add_layer+1, self.out_ndvistats_folder_tab['sfs'])
            self.list_band_outraster.insert(add_layer+1, add_layer+1)
            
        # Extract value mean from polygons
        for sple in range(len(self.sample_name) * 2):
            kwargs = {}
            kwargs['fieldname'] = self.fieldname_args[sple]
            kwargs['class'] = self.class_args[sple]
            sample_rd[sple] = Sample(self.sample_name[sple/2], self.path_area, self.list_nb_sample[sple/2])
            sample_rd[sple].create_sample(**kwargs)
            
            # Add the validation shapefile
            self.valid_shp.append([sample_rd[sple].vector_val, kwargs['fieldname'], kwargs['class']])

            for lbo in range(len(self.raster_path)):
                kwargs['rank'] = lbo
                kwargs['nb_img'] = len(self.raster_path)
                sample_rd[sple].zonal_stats((self.raster_path[lbo], self.list_band_outraster[lbo]), **kwargs)
            
            # To convert the dictionnary in a list
            for key, value in sample_rd[sple].stats_dict.iteritems():
                X_rf.append([-10000 if (math.isnan(x) or math.isinf(x)) else x for x in value])
                # To set the grassland class of the RPG and PIAO (same class)            
                if sple == 2:
                    y_rf.append(1)
                elif sple == 3:
                    y_rf.append(4)
                else:
                    y_rf.append(sple)
 
        # Build a forest of trees from the samples                 
        self.rf = self.rf.fit(X_rf, y_rf)

    def i_classifier_rf(self): 
        """
        Interface function to launch random forest classification with a input segmentation :func:`Segmentation.Segmentation`.
        
        This function use the sklearn module to build the best of decision tree to extract classes.
        The optimal threshold are stored by class **rf** variable in :func:`Processing.i_sample_rf`. Then it computes zonal statistics by polygons
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
#         out_carto.out_threshold = []
        for ind_th in range(len(self.raster_path)):
            multi_process_var.append([self.raster_path[ind_th], self.list_band_outraster[ind_th]])

        # Compute zonal stats with multi processing
        exist_stats = 1 # By default, the stats file exists already
        file_stats = os.path.dirname(self.raster_path[0]) + '/Stat_raster_spectral_texture.stats' # Stats backup file
        if not os.path.exists(file_stats):
            exist_stats = 0 # The sats file doesn't exist
            # Open a stats backup to avoid computing again (Gain of time)
            f_out = open(file_stats, "wb")
        
        p = []
        kwargs = {}
        X_out_rf = [] # Variable list to compute decision tree with random forest method
        if exist_stats == 0:
            out_carto.stats_dict = mgr.defaultdict(list)
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
                    
            for key, value_seg in out_carto.stats_dict.items():
                true_value = [-10000 if (math.isnan(x) or math.isinf(x)) else x for x in value_seg]
                X_out_rf.append(true_value)
                
                # Print rasters stats value in the text file .lg
                f_out.write(str(true_value) + '\n')
            
            # Close the output file
            f_out.close()
            
        else:
            # If the stats file exists already, open this file and append in the stats_dict variable
            out_carto.stats_dict = defaultdict(list)
            with open(file_stats, "r") as f_in:
                index_in_stats=-1
                for x_in in f_in.readlines():
                    index_in_stats = index_in_stats + 1
                    out_carto.stats_dict[index_in_stats] = eval(x_in.strip('\n'))
                    X_out_rf.append(eval(x_in.strip('\n')))
        
        predicted_rf = self.rf.predict(X_out_rf)
        
        # For the higher than level 1
        if len(self.sample_name) > 2:
            # Compute the biomass and density distribution
            # Use 'out_carto.out_threshold' to konw predicted in the segmentation class
            out_carto.out_threshold = predicted_rf
            # In the compute_biomass_density function, this variable used normally to define 
            # threshold of the classification with SEATH method is initialized
            out_carto.compute_biomass_density('RF')        
        
        out_carto.class_tab_final = defaultdict(list)
        for i_polyg in range(len(predicted_rf)):
            i_final = 0
            class_final = []
            # Initialize the predicted output format
            # For example : predicted => 4, formatted => [1,3,4]
            while i_final < len(self.tree_direction):
                if self.tree_direction[i_final][len(self.tree_direction[i_final])-1] == predicted_rf[i_polyg]:
                    class_final = self.tree_direction[i_final]
                    i_final = len(self.tree_direction)
                i_final = i_final + 1
            
            if class_final == []:
                class_final = [1, 2]
            # Set the class name because of predicted output formatted         
            out_carto.class_tab_final[i_polyg] = [self.in_class_name[f] for f in class_final] + \
                                                [predicted_rf[i_polyg]] + [predicted_rf[i_polyg]]
            # For the output line with one level, add a phantom level
            # TODO : Replace constant by a variable in the condition 'while'
            while len(out_carto.class_tab_final[i_polyg]) < 5:
                out_carto.class_tab_final[i_polyg].insert(len(out_carto.class_tab_final[i_polyg])-2,'')
        
        # If there is more one fieldnames line edit fulled in classification tab
        if len(self.sample_name) > 2:     
            # Compute biomass and density scale
            out_carto.append_scale(self.in_class_name[2], 'self.stats_dict[ind_stats][3]/self.max_bio')
            out_carto.append_scale(self.in_class_name[3], 'self.stats_dict[ind_stats][2]/self.max_wood_idm')
        
        # Rasterize RPG shapefile to complete the final shapefile
        opt = {}
        opt['Remove'] = 1
        rpg_tif = Vector(self.sample_name[0], self.path_area, **opt)
        out_carto.mono_rpg_tif = rpg_tif.layer_rasterization(self.path_ortho, 'CODE_GROUP')
        
        # Final cartography
#         out_carto.mono_rpg_tif = self.sample_name[0][:-4] + '.TIF'
        out_carto.create_cartography(self.out_fieldname_carto, self.out_fieldtype_carto)

    def i_classifier_s(self): 
        """
        Interface function to launch decision tree classification with a input segmentation :func:`Segmentation.Segmentation`.
        
        This function store optimal threshold by class **Segmentation.out_threshold**. Then it computes zonal statistics by polygons
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
        if self.path_mnt != '':
            # Add class indexes
            self.tree_direction[0].append(6)
            self.tree_direction[0].append(7)
            
        # Compute zonal stats on Max NDVI raster  
        try:
            # out_carto.zonal_stats((raster_path[ind_th+1], list_band_outraster[ind_th+1]))
            multi_process_var.append([self.raster_path[ind_th+2], self.list_band_outraster[ind_th+2]])
            # Compute stats twice, because there is 3 classes and not 2
            # out_carto.zonal_stats((raster_path[ind_th+1], list_band_outraster[ind_th+1]))
            multi_process_var.append([self.raster_path[ind_th+2], self.list_band_outraster[ind_th+2]])
        except:
            print('Not MNT on the 3rd step')
            multi_process_var.append([self.raster_path[ind_th+1], self.list_band_outraster[ind_th+1]])
            multi_process_var.append([self.raster_path[ind_th+1], self.list_band_outraster[ind_th+1]])

        # Compute zonal stats with multi processing
        exist_stats = 1 # By default, the stats file exists already
        file_stats = os.path.dirname(self.raster_path[0]) + '/Stat_raster_spectral_texture.stats' # Stats backup file
        if not os.path.exists(file_stats):
            exist_stats = 0 # The sats file doesn't exist
            # Open a stats backup to avoid computing again (Gain of time)
            f_out = open(file_stats, "wb")
            
        p = []
        kwargs = {}
        X_out_rf = [] # Variable list to compute decision tree with random forest method
        if exist_stats == 0:
            out_carto.stats_dict = mgr.defaultdict(list)
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
                    
            for key, value_seg in out_carto.stats_dict.items():
                
                true_value = [-10000 if (math.isnan(x) or math.isinf(x)) else x for x in value_seg]
                # Print rasters stats value in the text file .lg
                f_out.write(str(true_value) + '\n')
            
            # Close the output file
            f_out.close()
            
        else:
            # If the stats file exists already, open this file and append in the stats_dict variable
            out_carto.stats_dict = defaultdict(list)
            with open(file_stats, "r") as f_in:
                index_in_stats=-1
                for x_in in f_in.readlines():
                    index_in_stats = index_in_stats + 1
                    out_carto.stats_dict[index_in_stats] = eval(x_in.strip('\n'))
                    X_out_rf.append(eval(x_in.strip('\n')))
        
        # For the higher than level 1 
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
        
        # Rasterize RPG shapefile to complete the final shapefile
        opt = {}
        opt['Remove'] = 1
        rpg_tif = Vector(self.sample_name[0], self.path_area, **opt)
        rpg_tif.layer_rasterization(self.path_ortho, 'CODE_GROUP')
          
        # Final cartography
        out_carto.mono_rpg_tif = self.sample_name[0][:-4] + '.TIF'
        out_carto.create_cartography(self.out_fieldname_carto, self.out_fieldtype_carto)
       
    def i_validate(self):
        """
        Interface to validate a classification. It going to rasterize the validation shapefile and the 
        classification shapefile with :func:`layer_rasterization`. Next, to compare pixel by pixel, the classification
        quality to built a confusion matrix in a csv file.
        
        """
        # Variable to convert the input classname to an individual interger
        # Only for the validate sample
        class_validate = 0
        complete_validate_shp = os.path.dirname(self.valid_shp[0][0]) + '/validate.shp'
        
        # TODO: Set this method in the Precision_moba class
        
        # Processing to rasterize the validate shapefile. 1) Merge sahpefiles 2) Rasterization
        for val in self.valid_shp:
            if class_validate != 2: 
                # Grassland to 1
                if (class_validate !=3 and len(self.out_fieldname_carto) != 4+2) or len(self.out_fieldname_carto) == 4+2:
                    # To the level 3 with woodeen to 4 and 5
                    #
                    # Self.valid_shp is a list of list. In this variable there is :
                    # [Shapefile path, fieldname classes, classnames]
                    opt = {}
                    opt['Remove'] = 1 # To overwrite 
        
                    # Create a raster to valide the classification
                    # First time, create a new shapefile with a new field integer
                    sample_val = Sample(val[0], self.path_area, 1, **opt)
                    opt['add_fieldname'] = 1 
                    opt['fieldname'] = 'CLASS_CODE'
                    opt['class'] = str(class_validate) # Add integer classes
                    # Set the new shapefile
                    val[0] = val[0][:-4] + '_.shp'
                    val[1] = opt['fieldname']
                    val[2] = opt['class']
                    # Complete the new shapefile
                    sample_val.fill_sample(val[0], 0, **opt)
                    # Second time, merge the validate shapefile
                    if class_validate == 0:
                        process_tocall_merge =  ['ogr2ogr', '-overwrite', complete_validate_shp, val[0]]
                    elif class_validate > 0:
                        process_tocall_merge =  ['ogr2ogr', '-update', '-append', complete_validate_shp, \
                                                 val[0], '-nln', os.path.basename(complete_validate_shp[:-4])]
                    subprocess.call(process_tocall_merge)
            # Increrment variable
            class_validate = self.valid_shp.index(val) + 1
        
        # Compute precision of the classification
        valid = Precision_moba(self.path_area, self.path_folder_dpt)     
        valid.complete_validation_shp = complete_validate_shp
        valid.ex_raster = self.raster_path[0]
        
        # TODO: Call the RasterSat_by_Date class here instead of the Precision_moba class
        
        valid.preprocess_to_raster_precision(self.output_name_moba, 'FBPHY_SUB') # To the classification's data
        valid.preprocess_to_raster_precision(complete_validate_shp, val[1]) # To the validation's data
        
        # Compute precision on the output classification
        valid.confus_matrix(valid.complete_img[0].raster_data(valid.img_pr[0])[0], \
                            valid.complete_img[1].raster_data(valid.img_pr[1])[0])
        