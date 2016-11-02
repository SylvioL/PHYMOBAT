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
import math, subprocess
try :
    import gdal
except :
    from osgeo import gdal

import numpy as np

class RasterSat_by_date():
    """
    Satellite image  processing's class. This class include several processes to group images by date, mosaic images by date,
    extract images information, compute ndvi, compute cloud pourcent and create new rasters.
    
    :param class_archive: Archive class name with every information on downloaded images
    :type class_archive: class
    :param big_folder: Image processing folder
    :type big_folder: str
    :param one_date: [year, month, day] ...
            This variable is modified in the function :func:`mosaic_by_date()`. 
            To append mosaic image path, mosaic cloud image path, cloud pixel value table, mosaic ndvi image path and ndvi pixel value table.
    :type one_date: list of str
    
    """  
    def __init__(self, class_archive, big_folder, one_date):
        """Create a new 'Landsat_by_date' instance
        
        """
        
        self._class_archive = class_archive
        self._big_folder = big_folder
        self._one_date = one_date        
        # Verify list of list of str
        if one_date == []:
            print "Enter dates to mosaic images like [[str(year), str(month), str(day)], [str(year), str(month), str(day)], ...]"
            sys.exit(1)
        else:
            self._one_date = one_date
        
        self.out_ds = None
           
    def group_by_date(self, d_uni):
        """
        Function to extract images on a single date
        
        :param d_uni: [year, month, day]
        :type d_uni: list of str
        
        :returns: list of str -- variable **group** = [year, month, day, multispectral image path, cloud image path]
        """
         
        # Group of images with the same date
        group = []
         
        # Take images with the same date
        for d_dup in self._class_archive.list_img:
            if d_dup[:3] == d_uni:
                group.append(d_dup)
         
        return group
    
    def vrt_translate_gdal(self, vrt_translate, src_data, dst_data):
        """
        Function to launch gdal tools in command line. With ``gdalbuildvrt`` and ``gdal_translate``.
        This function is used :func:`mosaic_by_date` to mosaic image by date.
        
        :param vrt_translate: ``vrt`` or ``translate``
        :type vrt_translate: str
        :param src_data: Data source. Several data for vrt process and one data (vrt data) for gdal_translate
        :type src_data: list (process ``vrt``) or str (process ``translate``)  
        :param dst_data: Output path
        :type dst_data: str
        """
        
        if os.path.exists(dst_data):
            os.remove(dst_data)
        
        # Select process
        if vrt_translate == 'vrt':
            # Verify input data
            if type(src_data) is not np.ndarray:
                print 'VRT file ! The data source should be composed of several data. A list minimal of 2 dimensions'
                sys.exit(1)
                
            print 'Build VRT file'
            if not os.path.exists(dst_data):
                process_tocall = ['gdalbuildvrt', '-srcnodata', '-10000', dst_data]
                
            # Copy rasters
            for cp_image in src_data:
                process_tocall.append(cp_image)
                
        elif vrt_translate == 'translate':
            # Verify input data
            try :
                src_data = str(src_data)
            except:# if type(src_data) is not str:
                print 'Geotiff file ! The data source should be composed of path file. A character string !'
                sys.exit(1)
                
            print 'Build Geotiff file'
            if not os.path.exists(dst_data):
                process_tocall = ['gdal_translate', '-a_nodata', '-10000', src_data, dst_data]
            
        # Launch vrt process
        subprocess.call(process_tocall)
        
    def mosaic_by_date(self):
        """
        Function to merge images of the same date in a image group :func:`group_by_date`.
        """
        
        # Create the processing images folder if not exists
        if not os.path.exists(self._class_archive._folder + '/' + self._big_folder):
            os.mkdir(self._class_archive._folder + '/' + self._big_folder)
            
        # Matrix multi images for a single date 
        group = self.group_by_date(self._one_date) # Every images [year, month, day, multispectral image, cloud image]
        group_ = np.transpose(np.array(group)) # Transpose matrix to extract path of images
        
        # Create a folder with images year if it doesn't exist
        index_repertory_img = self._one_date[0]
        if not os.path.exists(self._class_archive._folder + '/' + self._big_folder + '/' + index_repertory_img):
            os.mkdir(self._class_archive._folder + '/' + self._big_folder + '/' + index_repertory_img)
        
        index_repertory_img = index_repertory_img + '/'
        # Create a folder with images date if it doesn't exist
        for d_ in self._one_date:
            index_repertory_img = index_repertory_img + d_
        
        if not os.path.exists(self._class_archive._folder + '/' + self._big_folder + '/' + index_repertory_img):
            os.mkdir(self._class_archive._folder + '/' + self._big_folder + '/' + index_repertory_img)
        
        # Build VRT file with data images required
        vrt_out = self._class_archive._folder + '/' + self._big_folder + '/' + index_repertory_img + '/' \
                    + self._class_archive._captor + index_repertory_img.split("/")[1] + '.VRT' # Multispectral VRT outfile
        if not os.path.exists(vrt_out):
            self.vrt_translate_gdal('vrt', group_[3], vrt_out)
        
        vrtcloud_out = self._class_archive._folder + '/' + self._big_folder + '/' + index_repertory_img + '/' \
                    + self._class_archive._captor + index_repertory_img.split("/")[1] + '_' + group_[4][0][-7:-4] + '.VRT' # Cloud TIF outfile
        if not os.path.exists(vrtcloud_out):
            self.vrt_translate_gdal('vrt', group_[4], vrtcloud_out)
        
        # Build Geotiff file with data images required
        gtif_out = vrt_out[:-4] + '.TIF' # Multispectral VRT outfile
        if not os.path.exists(gtif_out):
            self.vrt_translate_gdal('translate', vrt_out, gtif_out)
        self._one_date.append(gtif_out)
        
        gtifcloud_out = vrtcloud_out[:-4] + '.TIF' # Cloud TIF outfile
        if not os.path.exists(gtifcloud_out):
            self.vrt_translate_gdal('translate', vrtcloud_out, gtifcloud_out)
        self._one_date.append(gtifcloud_out)
    
    def raster_data(self, img):
        """
        Function to extract raster information.
        Return table of pixel values and raster information like line number, pixel size, ... (gdal pointer)
        
        :param img: Raster path
        :type img: str

        :returns: numpy.array -- variable **data**, Pixel value matrix of a raster.
                  
                  gdal pointer -- variable **_in_ds**, Raster information.
        """
        
        # Load Gdal's drivers
        gdal.AllRegister()
        
        # Loading input raster
        print 'Loading input raster :', os.path.split(str(img))[1][:-4]
        in_ds = gdal.Open(str(img), gdal.GA_ReadOnly)
        
        # if it doesn't exist
        if in_ds is None:
            print('could not open ')
            sys.exit(1)
        
        # Information on the input raster    
        nbband = in_ds.RasterCount # Spectral band number
        rows = in_ds.RasterYSize # Rows number
        cols = in_ds.RasterXSize # Columns number
        
        # Table's declaration 
        data = [] #np.float32([[0]*cols for i in xrange(rows)])
        for band in range(nbband):
            
            canal = in_ds.GetRasterBand(band + 1) # Select a band
            if nbband == 1:
                data = canal.ReadAsArray(0, 0, cols, rows).astype(np.float32) # Assign pixel values at the data
            else:
                data.append(canal.ReadAsArray(0, 0, cols, rows).astype(np.float32))
#             print('Copie des pixels du raster ! Bande :',  (band + 1))
        
        ###################################
        # Close input raster
        _in_ds = in_ds
        in_ds = None
        
        return data, _in_ds
    
    def pourc_cloud(self, img_spec, img_cloud):
        """
        Return clear pixel percentage on the image **img_spec** because of a cloud image **img_cloud**.
        
        :param img_spec: Spectral image path
        :type img_spec: str
        :param img_cloud: Cloud image path
        :type img_cloud: str
        
        :returns: float -- variable **nb0**, clear pixel percentage.
        :Example:
        
        >>> import RasterSat_by_date
        >>> Landsat_test = RasterSat_by_date(class_archive, big_folder, one_date)
        >>> nb0_test = Landsat_test.pourc_cloud(Landsat_test._one_date[3], Landsat_test._one_date[4])
        >>> nb0_test
        98
        """
        
        # Extract raster's information
        data_spec, info_spec = self.raster_data(img_spec)
        data_cloud, info_cloud = self.raster_data(img_cloud)
        self._one_date.append(data_cloud) # Add cloud pixel value table
        
        # Extent of the images
        mask_spec = np.in1d(data_spec[0], [-10000, math.isnan], invert=True) # ex : array([ True,  True,  True,  True, False,  True,  True,  True,  True], dtype=bool) -> False where there is -10000 ou NaN
        
        # Print area account of the pixel size 'info_spec.GetGeoTransform()'
        print 'Area = ' + str(float((np.sum(mask_spec)  * info_spec.GetGeoTransform()[1] * abs(info_spec.GetGeoTransform()[-1]) )/10000)) + 'ha' 
        
        # Cloud mask
        mask_cloud = np.in1d(data_cloud, 0) # This is the same opposite False where there is 0
        cloud = np.choose(mask_cloud, (False, mask_spec)) #  If True in cloud mask, it take spectral image else False
        dist = np.sum(cloud) # Sum of True. True is cloud
        
        # Computer cloud's percentage with dist (sum of cloud) by sum of the image's extent
        try :
            nb0 = float(dist)/(np.sum(mask_spec))
            print('For ' + os.path.split(str(img_spec))[1][:-4] + ', cloudy cover ' + str(100 - round(nb0*100, 2)) + "%")
        except ZeroDivisionError:
            nb0 = 0
            print("The raster isn\'t in the area !")
        
        return nb0
    
    def calcul_ndvi(self, img_spec):
        """
        Computer NDVI index for a Landsat image.
        
        NDVI = band4 - band3 / band4 + band3
        
        :param img_spec: Spectral image path
        :type img_spec: str

        """
        
        # Extract raster's information
        data, in_ds = self.raster_data(img_spec)
        
        # Computer NDVI
        mask = np.greater(data[0], -10000)
        ndvi = np.choose(mask, (-10000, eval('(data[4]-data[3])') / eval('(data[4]+data[3])'))) # If True, -10000 (NaN) else compute mathematical operation
        
        # Outfile name
        img_ndvi = img_spec[:-4] + '_ndvi.TIF'
        self._one_date.append(img_ndvi) # Add ndvi image path
        self._one_date.append(ndvi) # Add ndvi pixel value table
        self.create_raster(img_ndvi, ndvi, in_ds)
        
    def create_raster(self, out_raster, data, in_ds):
        """
        Create a raster empty with the input raster property
        
        :param out_raster: Output image path
        :type out_raster: str
        :param data: Pixel value matrix. Matrix size equal to that of a raster.
        :type data: numpy.array
        :param in_ds: Raster information
        :type in_ds: gdal pointer
        
        :returns: gdal pointer -- variable **out_ds**, Raster out information.
                  
                  int -- variable **nbband**, Band number of the out layer. 
                  
                  int -- variable **e**, Index to know if the raster exists. If it doesn't exists e = 0 else e = 1 (by default).
        """
        
#         if os.path.exists(str(out_raster)):
#             os.remove(str(out_raster))
        e = 1 # Raster out exists by default 
        # Verify if the processing take input band or one spectral band    
        if data.ndim == 2:
            nbband = 1
        else:
            nbband = in_ds.RasterCount 
            
        driver = gdal.GetDriverByName('GTiff')  
        if not os.path.exists(str(out_raster)):
            e = 0    
            # Create outfile
            self.out_ds = driver.Create(str(out_raster), in_ds.RasterXSize, in_ds.RasterYSize, nbband, gdal.GDT_Float32)
            if self.out_ds is None:
                print 'Could not create ' + os.path.split(str(out_raster))[1]
                sys.exit(1)
                
            # Get extent coordinates and raster resolution
            transform = in_ds.GetGeoTransform()
            # print transform
            
            minX = transform[0]
            maxY = transform[3]
            pixelWidth = transform[1]
            pixelHeight = transform[5]
            
            geotransform = [minX, pixelWidth, 0, maxY, 0, pixelHeight]
            
            # Record projection
            def_projection = in_ds.GetProjection() 

            # Set the geo-traking and outfile projection
            self.out_ds.SetGeoTransform(geotransform)
            self.out_ds.SetProjection(def_projection)
        
        else:
            
            self.out_ds = gdal.Open(str(out_raster), gdal.GA_ReadOnly)
            
        return nbband, e
    
    def complete_raster(self, (nbband, e), data): 
        """
        This function complete the function above :func:`create_raster()`. It 
        fills the raster table and close the layer.
        
        :param out_ds: Raster out information
        :type out_ds: gdal pointer
        :param nbband: Band number of the out layer
        :type nbband: int
        :param e: Index to know if the raster existed. If it didn't exist e = 0.
        :type e: int
        :param data: Pixel value matrix. Matrix size equal to that of a raster.
        :type data: numpy.array
        """
        
        # The e index to verify if the layer existed already because of the 
        # function :func:`create_raster()`
        if e == 0 :   
            p = 0 # Increment for the number band
            while p < nbband:
                #Incrementation
                p = p + 1
            
                print "Copy on the band ", p
      
                # Loading spectral band of outfile
                out_band = self.out_ds.GetRasterBand(p) 
                # write the data
                if data.ndim == 2:
                    out_band.WriteArray(data, 0, 0)
                else:
                    out_band.WriteArray(data[p-1], 0, 0)
                
                # Closing and statistics on output raster
                out_band.FlushCache()
                out_band.SetNoDataValue(-10000)
                out_band.GetStatistics(-1, 1) 
                out_band = None    
            
        # Close open data
        self.out_ds = None

            