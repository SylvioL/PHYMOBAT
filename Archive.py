#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of PHYMOBAT 3.0.
# Copyright 2016 Sylvio Laventure (IRSTEA - UMR TETIS)
#
# PHYMOBAT 3.0 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# PHYMOBAT 3.0 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with PHYMOBAT 3.0.  If not, see <http://www.gnu.org/licenses/>.

import os, sys, glob, re, shutil, time
import math, subprocess, json, urllib2
import tarfile, zipfile

try :
    import ogr
except :
    from osgeo import ogr

import UserDict
import numpy as np
from lxml import etree
from collections import defaultdict

from RasterSat_by_date import RasterSat_by_date

class Archive():
    """
    Class to list, download and unpack Theia image archive because of a shapefile (box).
    This shapefile get extent of the area.
            
    :param captor: Name of the satellite (ex: Landsat or SpotWorldHeritage ...). 
                                
                            Name used to the url on website Theia Land
    :type captor: str
    :param list_year: Processing's year (string for one year)
    :type list_year: list of str
    :param box: Path of the study area
    :type box: str
    :param folder: Path of the source folder
    :type folder: str
    :param repertory: Name of the archive's folder
    :type repertory: str
    """
    
    def __init__(self, captor, list_year, box, folder, repertory, proxy_enabled):
        """Create a new 'Archive' instance
        
        """
        self._captor = captor
        self._list_year = list_year.split(";")
        self._box = box
        self._folder = folder
        self._repertory = repertory
        self._proxy_enabled = proxy_enabled
        
        # Archive's list (two dimensions) :
        # 1. List of the website path archives
        # 2. List of the local path archives
        self.list_archive = []
        self.server = '' # Host
        self.resto =''
        # Info from Theia-land website or Olivier Hagolle blog
        if self._captor == 'SENTINEL2':
            self.server = 'https://theia.cnes.fr/atdistrib'
            self.resto = 'resto2'
            self.token_type = 'text'
        else:
            self.server = 'https://theia-landsat.cnes.fr'
            self.resto = 'resto'
            self.token_type = 'json'
        self.url = '' # str : complete website JSON database
        
        self.list_img = [] # List (dim 5) to get year, month, day, path of multispectral's images and path of cloud's images
        self.single_date = [] # date list without duplication
        
    def __str__(self) :
        return 'Year\'s list : ', self._list_year
    
    def set_list_archive_to_try(self, few_list_archive):
        """
        Test function to download a few archives
        
        :param few_list_archive: [archive_download, out_archive]
                    
                    with :
        
                    * archive_dowload : Archives downloaded
                    
                    * out_archive : Output archives path
                    
        :type few_list_archive: list dimension 2
        """
        
        _few_list_archive = np.array(few_list_archive)
        # Verify list informations
        if _few_list_archive.ndim < 2: 
            print 'Few information in the list'
        else:
            self.list_archive = few_list_archive
        
    def utm_to_latlng(self, zone, easting, northing, northernHemisphere=True):
        """
        Function to convert UTM to geographic coordinates 
        
        :param zone: UTM zone
        :type zone: int
        :param easting: Coordinates UTM in x
        :type easting: float
        :param northing: Coordinates UTM in y
        :type northing: float
        :param northernHemisphere: North hemisphere or not
        :type northernHemisphere: boolean
        
        :returns: tuple -- integer on the **longitude** and **latitude**
        
        Source : http://www.ibm.com/developerworks/java/library/j-coordconvert/index.html
        
        """
        
        if not northernHemisphere:
            northing = 10000000 - northing
        
        a = 6378137
        e = 0.081819191
        e1sq = 0.006739497
        k0 = 0.9996
        
        arc = northing / k0
        mu = arc / (a * (1 - math.pow(e, 2) / 4.0 - 3 * math.pow(e, 4) / 64.0 - 5 * math.pow(e, 6) / 256.0))
        
        ei = (1 - math.pow((1 - e * e), (1 / 2.0))) / (1 + math.pow((1 - e * e), (1 / 2.0)))
        
        ca = 3 * ei / 2 - 27 * math.pow(ei, 3) / 32.0
        
        cb = 21 * math.pow(ei, 2) / 16 - 55 * math.pow(ei, 4) / 32
        cc = 151 * math.pow(ei, 3) / 96
        cd = 1097 * math.pow(ei, 4) / 512
        phi1 = mu + ca * math.sin(2 * mu) + cb * math.sin(4 * mu) + cc * math.sin(6 * mu) + cd * math.sin(8 * mu)
        
        n0 = a / math.pow((1 - math.pow((e * math.sin(phi1)), 2)), (1 / 2.0))
        
        r0 = a * (1 - e * e) / math.pow((1 - math.pow((e * math.sin(phi1)), 2)), (3 / 2.0))
        fact1 = n0 * math.tan(phi1) / r0
        
        _a1 = 500000 - easting
        dd0 = _a1 / (n0 * k0)
        fact2 = dd0 * dd0 / 2
        
        t0 = math.pow(math.tan(phi1), 2)
        Q0 = e1sq * math.pow(math.cos(phi1), 2)
        fact3 = (5 + 3 * t0 + 10 * Q0 - 4 * Q0 * Q0 - 9 * e1sq) * math.pow(dd0, 4) / 24
        
        fact4 = (61 + 90 * t0 + 298 * Q0 + 45 * t0 * t0 - 252 * e1sq - 3 * Q0 * Q0) * math.pow(dd0, 6) / 720
        
        lof1 = _a1 / (n0 * k0)
        lof2 = (1 + 2 * t0 + Q0) * math.pow(dd0, 3) / 6.0
        lof3 = (5 - 2 * Q0 + 28 * t0 - 3 * math.pow(Q0, 2) + 8 * e1sq + 24 * math.pow(t0, 2)) * math.pow(dd0, 5) / 120
        _a2 = (lof1 - lof2 + lof3) / math.cos(phi1)
        _a3 = _a2 * 180 / math.pi
        
        latitude = 180 * (phi1 - fact1 * (fact2 + fact3 + fact4)) / math.pi
        
        if not northernHemisphere:
            latitude = -latitude
        
        longitude = ((zone > 0) and (6 * zone - 183.0) or 3.0) - _a3
        
        return (longitude, latitude)

    def coord_box_dd(self):
        """
        Function to get area's coordinates of shapefile

        :returns: str -- **area_coord_corner** : Area coordinates corner
        
                    --> Left bottom on x, Left bottom on y, Right top on x, Right top on y
        :Example:
        
        >>> import Archive
        >>> test = Archive(captor, list_year, box, folder, repertory, proxy_enabled) 
        >>> coor_test = test.coord_box_dd()
        >>> coor_test
        '45.52, 2.25, 46.71, 3.27'
        """
        
        # Processus to convert the UTM shapefile in decimal degrees shapefile with ogr2ogr in command line 
        utm_outfile = os.path.split(self._box)[0] + '/UTM_' + os.path.split(self._box)[1]
        if os.path.exists(utm_outfile):
            os.remove(utm_outfile)
        
        process_tocall = ['ogr2ogr', '-f', 'Esri Shapefile', '-t_srs', 'EPSG:32631', utm_outfile, self._box]
        subprocess.call(process_tocall)
        
        # To get shapefile extent
        # Avec import ogr
        driver = ogr.GetDriverByName('ESRI Shapefile')
        # Open shapefile
        data_source = driver.Open(utm_outfile, 0)
        
        if data_source is None:
            print 'Could not open file'
            sys.exit(1)
        
        shp_ogr = data_source.GetLayer()
        # Extent
        extent_ = shp_ogr.GetExtent() # (xMin, xMax, yMin, yMax)
        
        ## Close source data
        data_source.Destroy()
        
        # Coordinates min in decimal degrees
        LL_min = self.utm_to_latlng(31, extent_[0],  extent_[2], northernHemisphere=True)
        
        # Coordinates max in decimal degrees
        LL_max = self.utm_to_latlng(31, extent_[1],  extent_[3], northernHemisphere=True)
                                            
        # AdressUrl = 'http://spirit.cnes.fr/resto/Landsat/?format=html&lang=fr&q=2013&box=' + str(LL_Min[0]) + ',' + str(LL_Min[1]) + ',' + str(LL_Max[0]) + ',' + str(LL_Max[1])
        area_coord_corner = str(LL_min[0]) + ',' + str(LL_min[1]) + ',' + str(LL_max[0]) + ',' + str(LL_max[1])
        return area_coord_corner
    
    def listing(self):
        """
        Function to list available archive on plateform Theia Land, and on the area

        """
        
        # Loop on the years
        print "Images availables"
        for year in self._list_year:
            
            first_date = year.split(',')[0]
            # Tricks to put whether a year or a date (year-month-day)
            try:
                end_date = year.split(',')[1]
                print "=============== " + str(first_date) + " to " + str(end_date) + " ==============="
                self.url = self.server + '/' + self.resto + '/api/collections/' + self._captor + '/search.json?lang=fr&_pretty=true&completionDate=' + str(end_date) + '&box=' + self.coord_box_dd() + '&maxRecord=500&startDate=' + str(first_date)

            except IndexError:
                print "=============== " + str(first_date) + " ==============="
                self.url = self.server + '/' + self.resto + '/api/collections/' + self._captor + '/search.json?lang=fr&_pretty=true&q=' + str(year) + '&box=' + self.coord_box_dd() + '&maxRecord=500'

            print self.url
            # Link to connect in the database JSON of the Theia plateform
#             self.url = r'https://theia.cnes.fr/resto/api/collections/' + self._captor + '/search.json?lang=fr&_pretty=true&q=' + str(year) + '&box=' + self.coord_box_dd() + '&maxRecord=500'
            # Temporary link
#             if self._captor == 'SENTINEL2':
#                 self.url = r'https://theia.cnes.fr/atdistrib/resto2/api/collections/'
#             else:
#                 self.url = r'https://theia-landsat.cnes.fr/resto/api/collections/'
            
            # Initialisation variable for a next page 
            # There is a next page, next = 1
            # There isn't next page, next = 0
            next_ = 1
            if not os.path.exists(self._folder + '/' + self._repertory):
                os.mkdir(self._folder + '/' + self._repertory)
                
            # To know path to download images
            while next_ == 1:
                
                try :
                    request_headers = {"User-Agent": "Firefox/48.0"}
                    req = urllib2.Request(str(self.url), headers = request_headers) # Connexion in the database
                    data = urllib2.urlopen(req).read() # Read in the database
                    
                    new_data = re.sub("null", "'null'", data) # Remove "null" because Python don't like
                    new_data = re.sub("false", "False", new_data) # Remove "false" and replace by False (Python know False with a capital letter F)
                    
                    # Transform the data in dictionary
                    data_Dict = defaultdict(list)
                    data_Dict = UserDict.UserDict(eval(new_data))    
                    
                    # Select archives to download
                    for d in range(len(data_Dict['features'])):
                        name_archive = data_Dict['features'][d]['properties']['productIdentifier']    
                        feature_id = data_Dict["features"][d]['id']
                        link_archive = data_Dict['features'][d]['properties']['services']['download']['url'].replace("\\", "")
                        url_archive = link_archive.replace(self.resto, "rocket/#")
                        archive_download = url_archive.replace("/download", "") # Path to download
                        out_archive = self._folder + '/' + self._repertory + '/' + name_archive + '.tgz' # Name after download
                        self.list_archive.append([archive_download, out_archive, feature_id])  
                    
                    # Verify if there is another page (next)
                    if data_Dict['properties']['links'][len(data_Dict['properties']['links'])-1]['title'] == 'suivant':
                        self.url = data_Dict['properties']['links'][len(data_Dict['properties']['links'])-1]['href'].replace("\\", "")
                    else:
                        next_ = 0
                except:
                    print "Error connexion or error variable !"
                    sys.exit(1)

        print "There is " + str(len(self.list_archive)) + " images to download !"

    def download_auto(self, user_theia, password_theia):
        """
        Function to download images archive automatically on Theia land data center.
        Source : https://github.com/olivierhagolle/theia_download
        
        :param user_theia: Username Theia Land data center
        :type user_theia: str
        :param password_theia: Password Theia Land data center
        :type password_theia: str
        
        """
        #=====================
        # Proxy
        #=====================
        curl_proxy = ""
        try:
            if self._proxy_enabled.proxy != '':
                curl_proxy = str("-x %s" % (self._proxy_enabled.proxy))
                if self._proxy_enabled.login_proxy != '' and self._proxy_enabled.password_proxy != '':
                    curl_proxy = curl_proxy + str(" --proxy-user %s:%s" % (self._proxy_enabled.login_proxy, self._proxy_enabled.password_proxy))
        except AttributeError:
            pass
        
        #============================================================
        # get a token to be allowed to bypass the authentification.
        # The token is only valid for two hours. If your connection is slow
        # or if you are downloading lots of products
        #=============================================================
        if os.path.exists('token.json'):
            os.remove('token.json')
#         get_token='curl -k -s -X POST --data-urlencode "ident=%s" --data-urlencode "pass=%s" https://theia.cnes.fr/services/authenticate/>token.json'%(curl_proxy,user_theia, password_theia)
        get_token='curl -k -s -X POST %s --data-urlencode "ident=%s" --data-urlencode "pass=%s" %s/services/authenticate/>token.json'%(curl_proxy, user_theia, password_theia, self.server)
        os.system(get_token)
        
        with open('token.json') as data_file: 
            try:
                if self.token_type == "json":
                    token_json = json.load(data_file)
                    token = token_json["access_token"]
                elif self.token_type=="text":
                    token=data_file.readline()
            except :
                print "Authentification is probably wrong"
                sys.exit(-1)

        #====================
        # Download
        #====================  
        # Loop on list archive to download images  
        for d in range(len(self.list_archive)):
            # Download if not exist
            if not os.path.exists(self.list_archive[d][1]):
                 
                print str(round(100*float(d)/len(self.list_archive),2)) + "%" # Print loading bar
                print os.path.split(str(self.list_archive[d][1]))[1]
                
#                 get_product='curl -o %s -k -H "Authorization: Bearer %s" https://theia.cnes.fr/resto/collections/Landsat/%s/download/?issuerId=theia'%(curl_proxy,self.list_archive[d][1], token, self.list_archive[d][2])
                get_product='curl %s -o %s -k -H "Authorization: Bearer %s" %s/%s/collections/%s/%s/download/?issuerId=theia'%(curl_proxy, self.list_archive[d][1], token, self.server, self.resto, self._captor, self.list_archive[d][2])
                print get_product
                os.system(get_product)
                
        os.remove('token.json')
        print "100%"
        print "END OF DOWNLOAD !"   
        
    def decompress(self):
        """
        Function to unpack archives and store informations of the images (date, path, ...)
        """
        
        print "Unpack archives"
        
        for annee in self._list_year:
            
            first_date = annee.split(',')[0]
            # Tricks to put whether a year or a date (year-month-day)
            try:
                end_date = annee.split(',')[1]
                print "=============== " + str(first_date) + " to " + str(end_date) + " ==============="
            except IndexError:
                print "=============== " + str(first_date) + " ==============="
            
            img_in_glob = []
            img_in_glob = glob.glob(str(self._folder) + '/'+ str(self._repertory) + '/*gz')
            
            if img_in_glob == []:
                print "There isn't tgzfile in the folder"
                sys.exit()
            else:
                # Create a folder "Unpack"
                folder_unpack = self._folder + '/' + self._repertory + '/Unpack'
                
                if os.path.isdir(folder_unpack):
                    print('The folder already exists')
            #        shutil.rmtree(FolderOut) # Remove the folder that it contains if exists ...
                else:
                    process_tocall = ['mkdir', folder_unpack]
                    subprocess.call(process_tocall)
                
                for img in img_in_glob:
                    
                    # Unpack the archives if they aren't again!
                    if self._captor == 'Landsat':
                        out_folder_unpack = folder_unpack + '/' + os.path.split(img)[1][:len(os.path.split(img)[1])-4]
                        if not os.path.exists(out_folder_unpack):
                            print 'Unpack :'+os.path.split(img)[1]   
                            tfile = tarfile.open(img, 'r:gz')
                            tfile.extractall(str(folder_unpack))
                    
                        # On xmlfile, extract dates, path of images, cloud's images
                        xmlfile = etree.parse(str(out_folder_unpack) + '/' + os.path.split(img)[1][:len(os.path.split(img)[1])-4] + '.xml')
                        
                        # Date images
                        # Exemple : '2015-09-27 10:41:25.956749'
                        # To get year, month and day ---> .split(' ')[0].split('-')
                        di = xmlfile.xpath("/METADATA/HEADER/DATE_PDV")[0].text.split(' ')[0].split('-')
                        # Multispectral images
                        hi = out_folder_unpack + '/' + xmlfile.xpath("/METADATA/FILES/ORTHO_SURF_CORR_ENV")[0].text
                        # Cloud images
                        # Cloud's path not exists in xmlfile, then replace 'SAT' by 'NUA'
                        ci = out_folder_unpack + '/' + xmlfile.xpath("/METADATA/FILES/MASK_SATURATION")[0].text.replace('_SAT', '_NUA')
                    
                    elif self._captor == 'SENTINEL2':
                        
                        tzip = zipfile.ZipFile(img)
                        # Extract band 2 (Blue), 3 (Green), 4 (Red), and 8 (NIR) at surface reflectance 10m, XML file, Cloud mask at 10m
                        extent_img = ['_SRE_B2.tif', '_SRE_B3.tif', '_SRE_B4.tif', '_SRE_B8.tif', '_MTD_ALL.xml', '_CLM_R1.tif']
                        zip_img = tzip.namelist() # Images list in the archive 
                        zip_folder = zip_img[0].split('/')[0]
                        out_folder_unpack = folder_unpack + '/' + zip_folder
                        
                        print 'Unpack :' + os.path.split(zip_folder)[1]
                        extraction_img = []
                        for e in extent_img:
                            z_out = [f for f in zip_img if e in f][0]
                            extraction_img.append(folder_unpack + '/' + str(z_out))
                            if not os.path.exists(folder_unpack + '/' + str(z_out)):
                                print('Extract :%s' %(z_out))
                                tzip.extract(str(z_out), str(folder_unpack))
                                                 
                        # On xmlfile, extract dates, path of images, cloud's images
                        xmlfile = etree.parse(str(extraction_img[4]))
                        # Date images
                        di = xmlfile.xpath("/Muscate_Metadata_Document/Product_Characteristics/ACQUISITION_DATE")[0].text.split('T')[0].split('-')
                        # Multispectral images
                        hi = out_folder_unpack + '/' + xmlfile.xpath("/Muscate_Metadata_Document/Product_Characteristics/PRODUCT_ID")[0].text + '.tif'
                        if not os.path.exists(hi):
                            # For Sentinel2 from Theia plateform, we need to make a stack layer for rasters
                            # There is a function that make this in RasterSat_by_date class
                            stack_img = RasterSat_by_date('', '', [0])
                            input_stack = extraction_img[:4]
                            input_stack.insert(0,'-separate')
                            stack_img.vrt_translate_gdal('vrt', input_stack, hi[:-4] + '.VRT')
                            stack_img.vrt_translate_gdal('translate', hi[:-4] + '.VRT', hi)
                        # Cloud images
                        ci = out_folder_unpack + '/' + xmlfile.xpath("/Muscate_Metadata_Document/Product_Organisation/Muscate_Product/Mask_List/Mask/Mask_File_List/MASK_FILE")[2].text
                       
                    self.list_img.append([di[0], di[1], di[2], str(hi), str(ci)])
                    
                    # Create a list with dates without duplicates
                    if not di in self.single_date:
                        self.single_date.append(di)
    
        print "End of unpack archives"
    
