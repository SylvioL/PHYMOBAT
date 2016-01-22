#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2016 Sylvio Laventure (IRSTEA - UMR TETIS)
#
# PHYMOBAT 1.1 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# PHYMOBAT 1.1 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with PHYMOBAT 1.1.  If not, see <http://www.gnu.org/licenses/>.
from _collections import defaultdict

"""
Interface main, PHYMOBAT (FB PHYsionomiquedes Milieux Ouverts de Basse Altitude par Télédétection)

__name__ = "PHYMOBAT 1.1"
__license__ = "GPL"
__version__ = "1.1"
__author__ = "LAVENTURE Sylvio - UMR TETIS / IRSTEA"
__date__ = "Janvier 2016"
"""

import os, sys, time
from PyQt4.QtCore import *
from PyQt4.QtGui import *

try :
    import ogr
except :
    from osgeo import ogr

try:
    _fromUtf8 = QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
    
import webbrowser
import lxml.etree as ET

from ui_PHYMOBAT_tab import Ui_PHYMOBAT
from ui_A_propos_PHYMOBAT_window import Ui_About
from ui_Warming_study_area import Ui_Warming_study_area
from Processing import Processing

class PHYMOBAT(QMainWindow, Processing):
    """
    Interface main class. It makes to link ``ui_PHYMOBAT_tab`` and ``Processing``.
    """
    
    def __init__(self, parent=None):
        super(PHYMOBAT, self).__init__(parent)
        Processing.__init__(self)
        self.initUI()
        self.apropos = None # For the "About PHYMOBAT" window
        self.w_study_area = None # For the "Warming : forget study area" window
        
        self.loop_sample = 1
        
#         while self.loop_sample == 1:
#             sample_path = "%s" % self.ui.lineEdit_area_path.text()
#             if not self.ui.lineEdit_area_path.text().isEmpty() and sample_path[-4:] == '.shp':
#                 ds = ogr.GetDriverByName('ESRI Shapefile').Open(sample_path, 0)
#                 so = ds.GetLayer()
#                 dso = so.GetLayerDefn()
#                 field_names = [so.GetLayerDefn().GetFieldDefn(l).GetName() for l in range(dso.GetFieldCount())]
#                 print(field_names)
#                 self.loop_sample = 0
        
    def initUI(self):
        
        """
        Get initial values from interface after a click button.
        
        There is :
        
        - Connect browser button to search a path
            * Main folder path
            * Study area shapefile path
            * VHRS image path
            * MNT image path
            * Segmentation shapefile path
            * Output classification shapefile path
            * Sample shapefile path
            * Image path for samples if the first processing image hasn't been launched
            
        - Connect button to add sample in the memory list
        - Connect button to clear sample record. Clear in the interface and in the memory list
        - Connect close|ok button
        - Connect menu bar tab (Open backup, save in a xml file, close, help, About PHYMOBAT)
        - Initialize backup variable
        
        """
        
        # Initial interface
        self.ui = Ui_PHYMOBAT()
        self.ui.setupUi(self)
        
#         self.ui.menuMenu().addMenu('&menuMenu')
#         self.ui.lineEdit_select_sample_fieldname_1.textChanged.connect(self.valueChanged(self.ui.lineEdit_select_sample_fieldname_2.text()))
        # Connect browser button to search a path
        ##########################################
        # Main folder path
        self.ui.lineEdit_principal_folder.clear()
        self.connect(self.ui.pushButton_browser_principal_folder, SIGNAL('clicked()'), self.f_path_folder_dpt)
        
        # VHRS image path
        self.ui.lineEdit_VHRS.clear()
        self.connect(self.ui.pushButton_browser_VHRS, SIGNAL('clicked()'), self.f_path_ortho)
        
        # Study area shapefile path
        self.ui.lineEdit_area_path.clear()
        self.connect(self.ui.pushButton_browser_area_path, SIGNAL('clicked()'), self.f_path_area)
        
        # Segmentation shapefile path
        self.ui.lineEdit_segmentation.clear()
        self.connect(self.ui.pushButton_browser_segmentation, SIGNAL('clicked()'), self.f_path_segm)
        
        # MNT image path
        self.ui.lineEdit_MNT.clear()
        self.connect(self.ui.pushButton_browser_MNT, SIGNAL('clicked()'), self.f_path_mnt)
        
        # Output classification shapefile path
        self.ui.lineEdit_output.clear()
        self.ui.pushButton_browser_output.clicked.connect(self.f_output_name_moba)
        
        # Sample shapefile path
        self.ui.lineEdit_sample_path.clear()
        self.ui.pushButton_browser_sample_path.clicked.connect(self.enter_sample_name)
        
        # Image path  for samples if the first processing image hasn't been launched
        self.connect(self.ui.pushButton_img_sample, SIGNAL('clicked()'), self.img_sample_name)
        ##########################################

        # Connect button to add sample in the memory list
        self.connect(self.ui.pushButton_add_sample, SIGNAL('clicked()'), self.add_sample)
        
        # Connect button to clear sample record. Clear in the interface and in the memory list
        self.connect(self.ui.pushButton_clear_sample, SIGNAL('clicked()'), self.clear_sample)
        
        # Connect close|ok button
        self.ui.buttonBox.button(QDialogButtonBox.Close).clicked.connect(self.close_button)
        self.ui.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.ok_button)
        
        # Connect Menu bar
        self.ui.actionOuvrir.triggered.connect(self.open_backup) # Open backup
        self.ui.actionSauver.triggered.connect(self.save_backup) # Save field name on the interface
        self.ui.actionQuiter.triggered.connect(self.close_button) # Close
        self.ui.actionAide_de_PHYMOBAT.triggered.connect(self.help_tools) # Help
        self.ui.actionA_propos_de_PHYMOBAT.triggered.connect(self.about_PHYMOBA) # About PHYMOBA
        
        self.rpg_tchek = [] # To backup rpg mode
        self.img_sample = [] # To backup
        
#         while self.loop_sample == 1:
#             sample_path = "%s" % self.ui.lineEdit_area_path.text()
#             if not self.ui.lineEdit_area_path.text().isEmpty() and sample_path[-4:] == '.shp':
#                 ds = ogr.GetDriverByName('ESRI Shapefile').Open(sample_path, 0)
#                 so = ds.GetLayer()
#                 dso = so.GetLayerDefn()
#                 field_names = [so.GetLayerDefn().GetFieldDefn(l).GetName() for l in range(dso.GetFieldCount())]
#                 print(field_names)
#                 self.loop_sample = 0
        
    def get_variable(self):
        
        """
        Add a all system value like :
        
        - Main folder path by line edit
        - Satellite captor name by combo box
        - Classification year by line edit
        - Study area shapefile path by line edit
        - Connexion username and password by line edit
        - VHRS image path by line edit
        - MNT image path by line edit
        - Segmentation shapefile path path by line edit
        - Output classification shapefile path by line edit
        - Output shapefile field name by line edit and field type by combo box
        
        """
        # Main folder path by line edit.
        self.path_folder_dpt = "%s" % self.ui.lineEdit_principal_folder.text()
        
        # Satellite captor name by combo box
        self.captor_project = self.ui.comboBox_captor.currentText()
        
        # Classification year by line edit
        self.classif_year = "%s" % self.ui.lineEdit_year_images.text()
        
        # Study area shapefile path by line edit
        self.path_area = "%s" % self.ui.lineEdit_area_path.text()
        
        # Connexion username and password by line edit
        self.user = "%s" % self.ui.lineEdit_user.text()
        self.password = "%s" % self.ui.lineEdit_password.text()
        
        # VHRS image path by line edit
        self.path_ortho = "%s" % self.ui.lineEdit_VHRS.text()
        
        # MNT image path by line edit
        self.path_mnt = "%s" % self.ui.lineEdit_MNT.text()        
        
        # Output shapefile field name by line edit and field type by combo box
        if self.ui.lineEdit_fieldname_1.text() != '':
            self.out_fieldname_carto.append("%s" % self.ui.lineEdit_fieldname_1.text())
            self.out_fieldtype_carto.append(eval("%s" % self.ui.comboBox_fieldname_1.currentText()))
        
        if self.ui.lineEdit_fieldname_2.text() != '':
            self.out_fieldname_carto.append("%s" % self.ui.lineEdit_fieldname_2.text())
            self.out_fieldtype_carto.append(eval("%s" % self.ui.comboBox_fieldname_2.currentText()))
         
        if self.ui.lineEdit_fieldname_3.text() != '':   
            self.out_fieldname_carto.append("%s" % self.ui.lineEdit_fieldname_3.text())
            self.out_fieldtype_carto.append(eval("%s" % self.ui.comboBox_fieldname_3.currentText()))
        
        if self.ui.lineEdit_fieldname_4.text() != '':    
            self.out_fieldname_carto.append("%s" % self.ui.lineEdit_fieldname_4.text())
            self.out_fieldtype_carto.append(eval("%s" % self.ui.comboBox_fieldname_4.currentText()))
            
        # Segmentation shapefile path path by line edit
        self.path_segm = "%s" % self.ui.lineEdit_segmentation.text()
        
        # Output shapefile field name by line edit and field type by combo box
        self.output_name_moba = "%s" % self.ui.lineEdit_output.text()
        
 
    def set_variable(self):
        """
        Print number of available image from Theia's GeoJSON .
        """
        # self.ui.lineEdit_listing.setText(str(self.nb_avalaible_images))
        self.ui.label_listing.setText(str(self.nb_avalaible_images))
        
    def f_path_folder_dpt(self):
        """
        Open a input browser box to select the main folder path by line edit.
        """
        infoldername = QFileDialog.getExistingDirectory(self, "Principal folder path", os.getcwd(), QFileDialog.ShowDirsOnly)
        self.ui.lineEdit_principal_folder.setText(str(infoldername).replace('[','').replace(']','').replace(' ',''))
    
    def f_path_ortho(self):
        """
        Open a input browser box to select the VHRS image path by line edit.
        """
        orthofilename = QFileDialog.getOpenFileName(self, "THRS image", os.getcwd(), '*.TIF *.tif')
        self.ui.lineEdit_VHRS.setText(str(orthofilename).replace('[','').replace(']','').replace(' ',''))   
    
    def f_path_mnt(self):
        """
        Open a input browser box to select the MNT image path by line edit.
        """
        mntfilename = QFileDialog.getOpenFileName(self, "MNT image", os.getcwd(), '*.TIF *.tif')
        self.ui.lineEdit_MNT.setText(str(mntfilename).replace('[','').replace(']','').replace(' ',''))  
        
    def f_path_area(self):
        """
        Open a input browser box to select the study area shapefile path by line edit.
        """        
        areafilename = QFileDialog.getOpenFileName(self, "Area shapefile", os.getcwd(), '*.shp')
        self.ui.lineEdit_area_path.setText(str(areafilename).replace('[','').replace(']','').replace(' ',''))
        
    def f_path_segm(self):
        """
        Open a input browser box to select segmentation shapefile path path by line edit.
        """
        segmfilename = QFileDialog.getOpenFileName(self, "Segmentation shapefile", os.getcwd(), '*.shp')
        self.ui.lineEdit_segmentation.setText(str(segmfilename).replace('[','').replace(']','').replace(' ',''))
    
    def f_output_name_moba(self):
        """
        Set the output classification shapefile path by line edit.
        """
        outfilename = QFileDialog.getSaveFileName(self, "FB file", os.getcwd(), '*.shp')
        self.ui.lineEdit_output.setText(outfilename)
        
    def enter_sample_name(self):
        """
        Open a input browser box to select the sample shapefile path by line edit. With :func:`add_sample` conditions.
        """
        samplefilename = QFileDialog.getOpenFileName(self, "Sample shapefile", os.getcwd(), '*.shp')
        self.ui.lineEdit_sample_path.setText(str(samplefilename).replace('[','').replace(']','').replace(' ',''))
        
    def img_sample_name(self):
        """
        Open a input browser box to select the image for samples path by line edit. With :func:`add_sample` conditions.
        """
        imgsamplefilename = QFileDialog.getOpenFileName(self, "Sample image", os.getcwd(), '*.TIF')
        self.ui.lineEdit_img_sample.setText(str(imgsamplefilename).replace('[','').replace(']','').replace(' ',''))
        
    def add_sample(self):
        """
        Add sample information and location to compute optimal threshold :
        
        - Append a sample name by line Edit. *This is a check box* ``RPG``, *if the sample is RPG file. It launch the Rpg class. And append a other sample from Rpg class*.
        - Append two sample field names by line edit. It will be the same.
        - Append sample class names by line edit. One or more for every sample.
        - Append number of polygons for every samples by line edit.
        - Print in a plain text edit : sample name, two sample field names, sample class names and number of polygons.
        - *This check box* ``Image echantillonee``, *image path for samples if the first processing image hasn't been launched*.
            .. note:: This is for a image with one spectral band
        - Clear all line edit at the end.
        """
        
        nb_sample = len(self.sample_name)# Compute number of samples added. Condition : max three. 
        # Study area shapefile path by line edit if no processing other
        # Because the function "Vector" need study area
        self.path_area = "%s" % self.ui.lineEdit_area_path.text()
        if self.path_area == '':
            self.forget_study_area()
        
        if not self.ui.lineEdit_sample_path.text().isEmpty() and not self.ui.lineEdit_select_sample_fieldname_1.text().isEmpty() and \
                not self.ui.lineEdit_select_sample_fieldname_2.text().isEmpty() and not self.ui.lineEdit_select_sample_class_1.text().isEmpty() and \
                not self.ui.lineEdit_select_sample_class_2.text().isEmpty() and not self.ui.lineEdit_select_sample_nb_poly.text().isEmpty() and \
                nb_sample < 3 and not self.ui.lineEdit_area_path.text().isEmpty():
            
            # Append a sample name by line Edit.
            if self.ui.checkBox_RPG.isChecked():
                # Check box, if the sample is RPG file. It launch the Rpg class. And append a other sample from Rpg class 
                self.sample_name.append(self.i_rpg("%s" % self.ui.lineEdit_sample_path.text()))
                self.rpg_tchek.append(1) 
            else:
                self.sample_name.append("%s" % self.ui.lineEdit_sample_path.text())
                self.rpg_tchek.append(0)
            
            # Append two sample field names by line edit. It will be the same.
            self.fieldname_args.append("%s" % self.ui.lineEdit_select_sample_fieldname_1.text())
            self.fieldname_args.append("%s" % self.ui.lineEdit_select_sample_fieldname_2.text())
            # Append sample class names by line edit. One or more for every sample
            self.class_args.append("%s" % self.ui.lineEdit_select_sample_class_1.text())
            self.class_args.append("%s" % self.ui.lineEdit_select_sample_class_2.text())
            # Append number of polygons for every samples by line edit.
            self.list_nb_sample.append("%s" % self.ui.lineEdit_select_sample_nb_poly.text())
            
            nb_sample = len(self.sample_name) # Number of samples added
            # Print in a plain text edit : sample name, two sample field names, sample class names and number of polygons.
            cursor = self.ui.plainTextEdit_sample.textCursor()
            cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
            self.ui.plainTextEdit_sample.setTextCursor(cursor)
            self.ui.plainTextEdit_sample.insertPlainText(str(self.sample_name[nb_sample-1]) + "\n")
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor)
            self.ui.plainTextEdit_sample.setTextCursor(cursor)
            self.ui.plainTextEdit_sample.insertPlainText(str(self.fieldname_args[(nb_sample-1)*2]) + '    ' + str(self.fieldname_args[((nb_sample-1)*2)+1]) + "\n")
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor)
            self.ui.plainTextEdit_sample.setTextCursor(cursor)
            self.ui.plainTextEdit_sample.insertPlainText(str(self.class_args[(nb_sample-1)*2]) + '    ' + str(self.class_args[(nb_sample-1)*2+1]) + "\n")
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor)
            self.ui.plainTextEdit_sample.setTextCursor(cursor)
            self.ui.plainTextEdit_sample.insertPlainText(str(self.list_nb_sample[nb_sample-1]) + "\n")
            
            # Check box, image path for samples if the first processing image hasn't been launched
            # Warming : This is for a image with one spectral band
            if self.ui.checkBox_img_sample.isChecked():
                self.raster_path.append("%s" % self.ui.lineEdit_img_sample.text())
                self.list_band_outraster.append(1)
                self.ui.lineEdit_img_sample.clear()
                self.img_sample.append(1)
            else: # To backup
                self.img_sample.append(0)

            # Clear all line edit after addition, ie after click add button.
            self.ui.lineEdit_sample_path.clear()
            self.ui.lineEdit_select_sample_fieldname_1.clear()
            self.ui.lineEdit_select_sample_fieldname_2.clear()
            self.ui.lineEdit_select_sample_class_1.clear()
            self.ui.lineEdit_select_sample_class_2.clear()
            self.ui.lineEdit_select_sample_nb_poly.clear()
            self.ui.checkBox_RPG.setChecked(False)
    
    def clear_sample(self):
        """
        Function to clear sample record. Clear in the interface and in the memory list.
        """
        self.sample_name = []
        self.fieldname_args = []
        self.class_args = []
        self.list_nb_sample = []
        self.rpg_tchek = []
        self.img_sample = []
        
        self.ui.lineEdit_sample_path.clear()
        self.ui.lineEdit_select_sample_fieldname_1.clear()
        self.ui.lineEdit_select_sample_fieldname_2.clear()
        self.ui.lineEdit_select_sample_class_1.clear()
        self.ui.lineEdit_select_sample_class_2.clear()
        self.ui.lineEdit_select_sample_nb_poly.clear()
        self.ui.checkBox_RPG.setChecked(False)
        self.ui.lineEdit_img_sample.clear()
        self.ui.plainTextEdit_sample.clear()
        self.ui.plainTextEdit_sample.insertPlainText(_fromUtf8("1 - Végétation non naturelle / Semi-naturelle\n"))
        self.ui.plainTextEdit_sample.insertPlainText(_fromUtf8("2 - Herbacés / Ligneux\n"))
        self.ui.plainTextEdit_sample.insertPlainText("3 - Lingeux mixtes / denses\n")
        self.ui.plainTextEdit_sample.insertPlainText("\n")
        self.ui.plainTextEdit_sample.insertPlainText("\n")
        self.ui.plainTextEdit_sample.insertPlainText("")
        
    def ok_button(self):
        
        """
        Function to launch the processing. This function take account :
        
        - The ``Multi-processing`` chack box if the processing has launched with multi process. By default, this is checked. It need a computer with minimum 12Go memory.
        - Append a few system value with :func:`get_variable`.
        - There are 3 principal check boxes :
            - to get number download available images
            - for downloading and processing on theia platform
            - for compute optimal threshold.
            - for computer slope raster
            - for classification processing.
        """
        
        # Start the processus
        startTime = time.time()
        
        # To know if the processing must be launch on several thread
        if self.ui.checkBox_multiprocess.isChecked():
            self.mp = 1
        else:
            self.mp = 0
        
        self.get_variable() # Append a few system value
        vs = 0 # Variable to launch VHRS texture processing
        dd = 0 # Variable to launch image downloading 
        
        # Compute a output slope raster 
        if self.ui.checkBox_MNT.isChecked():
        
            self.i_slope()
        
        # if download check box is checked only
        if not self.ui.checkBox_listing.isChecked() and self.ui.checkBox_download.isChecked():
            
            self.ui.checkBox_listing.setChecked(True)     
            
        # if processing check box is checked only
        if not self.ui.checkBox_listing.isChecked() and not self.ui.checkBox_download.isChecked() and self.ui.checkBox_processing.isChecked():
            
            self.ui.checkBox_listing.setChecked(True) 
            self.ui.checkBox_download.setChecked(True)    
               
        # Downloading and processing on theia platform
        # A check box to get number download available images
        if self.ui.checkBox_listing.isChecked():
            
            if self.ui.checkBox_download.isChecked():
                # To launch the downloading
                dd = 1
              
            self.i_download(dd) # Launch image listing and downloading if dd = 1
            self.set_variable() # to write in the line edit about number download available images
            
            # Check box to launch the image processing
            if self.ui.checkBox_processing.isChecked():
                # Another check box to launch VHRS texture processing. If checked, vs = 1.
                if self.ui.checkBox_VHRS.isChecked():
                    vs = 1
                self.i_images_processing(vs) # function to launch the image processing            
        
        # To launch texture processing only
        if not self.ui.checkBox_listing.isChecked() and self.ui.checkBox_VHRS.isChecked():
            
            self.i_vhrs()
        
        # Compute optimal threshold  
        if self.ui.checkBox_threshold.isChecked():
              
            self.i_sample()
        
        # Classification processing 
        if self.ui.checkBox_classifier.isChecked():
             
            self.i_classifier()
        
#         # Clear variables after processing
#         self.clear_sample()
        self.out_fieldname_carto = ['ID', 'AREA']
        self.out_fieldtype_carto = [ogr.OFTString, ogr.OFTReal]
        # Images after processing images
        self.out_ndvistats_folder_tab = defaultdict(list)
            
        # End of the processus
        endTime = time.time() # Tps : Terminé
        print '...........' + ' Outputted to File in ' + str(endTime - startTime) + ' secondes'
        nb_day_processing = int(time.strftime('%d', time.gmtime(endTime - startTime))) - 1
        print "That is, " + str(nb_day_processing) + ' day(s) ' + time.strftime('%Hh %Mmin%S', time.gmtime(endTime - startTime))
    
    def open_backup(self):
        """
        Function to load input text in every fields. The input file must be a XML file.
        """
        
        in_backup = QFileDialog.getOpenFileName(self, "Open backup", os.getcwd(), '*.xml')
        
        # Parse the xml file
        tree = ET.parse(str(in_backup))
               
        pr = tree.find("Tab[@id='Processing_raster']")
        self.ui.lineEdit_principal_folder.setText(pr.find("Principal_folder").text)
        index_captor = self.ui.comboBox_captor.findText(pr.find("Captor").text) # To find combo box index
        self.ui.comboBox_captor.setCurrentIndex(index_captor)
        self.ui.lineEdit_year_images.setText(pr.find("Year_images").text)
        self.ui.lineEdit_area_path.setText(pr.find("Area_path").text)
        self.ui.lineEdit_user.setText(pr.find("Username").text)
        self.ui.lineEdit_password.setText(pr.find("Password").text)
        self.ui.lineEdit_VHRS.setText(pr.find("VHRS").text)
        self.ui.lineEdit_MNT.setText(pr.find("MNT").text)
        
        ps = tree.find("Tab[@id='Processing_sample']")  
        for sple_n in ps.iter("Sample"):
            self.ui.lineEdit_sample_path.setText(sple_n.find("Sample_path").text)
            self.ui.lineEdit_select_sample_fieldname_1.setText(sple_n.find("Fieldname_1").text)
            self.ui.lineEdit_select_sample_fieldname_2.setText(sple_n.find("Fieldname_2").text)
            self.ui.lineEdit_select_sample_class_1.setText(sple_n.find("Classname_1").text)
            self.ui.lineEdit_select_sample_class_2.setText(sple_n.find("Classname_2").text)
            self.ui.lineEdit_select_sample_nb_poly.setText(sple_n.find("Nb_polygones").text)
            # Launch rpg method if the box is checked and if the shapefile hasn't go through rpg method (with prefix MONO_)
            if sple_n.find("RPG").text == '1' and os.path.split(sple_n.find("Sample_path").text)[1][:5] != 'MONO_':
                self.ui.checkBox_RPG.setChecked(True)
            try:
                if sple_n.find("Img_sample").text != "":
                    self.ui.lineEdit_img_sample.setText(sple_n.find("img_sample").text)
                    self.ui.checkBox_img_sample.setChecked(True)
            except:
                print('Not sample raster only !')
            self.add_sample()
         
        c = tree.find("Tab[@id='Classification']")
        self.ui.lineEdit_segmentation.setText(c.find("Segmentation_path").text)
        self.ui.lineEdit_output.setText(c.find("Output_path").text)
        self.ui.lineEdit_fieldname_1.setText(c.find("Output_fieldname_1").text)
        self.ui.lineEdit_fieldname_2.setText(c.find("Output_fieldname_2").text)
        self.ui.lineEdit_fieldname_3.setText(c.find("Output_fieldname_3").text)
        self.ui.lineEdit_fieldname_4.setText(c.find("Output_fieldname_4").text)
        index_fieldname_1 = self.ui.comboBox_fieldname_1.findText(c.find("Output_type_1").text)        
        self.ui.comboBox_fieldname_1.setCurrentIndex(index_fieldname_1)
        index_fieldname_2 = self.ui.comboBox_fieldname_2.findText(c.find("Output_type_2").text)        
        self.ui.comboBox_fieldname_2.setCurrentIndex(index_fieldname_2)
        index_fieldname_3 = self.ui.comboBox_fieldname_3.findText(c.find("Output_type_3").text)        
        self.ui.comboBox_fieldname_3.setCurrentIndex(index_fieldname_3)
        index_fieldname_4 = self.ui.comboBox_fieldname_4.findText(c.find("Output_type_4").text)        
        self.ui.comboBox_fieldname_4.setCurrentIndex(index_fieldname_4)
        print("Load input text !")
        
    def save_backup(self):
        """
        Function to save input text in every fields. The output file must be a XML file.
        """
        
        out_backup = QFileDialog.getSaveFileName(self, "Save backup", os.getcwd(), '*.xml')
        
        root = ET.Element("Data_filled")
        
        doc = ET.SubElement(root, "Tab", id="Processing_raster")
        ET.SubElement(doc, "Principal_folder", type = "str").text = "%s" % self.ui.lineEdit_principal_folder.text()
        ET.SubElement(doc, "Captor", type = "str").text = "%s" % self.ui.comboBox_captor.currentText()
        ET.SubElement(doc, "Year_images", type = "str").text = "%s" % self.ui.lineEdit_year_images.text()
        ET.SubElement(doc, "Area_path", type = "str").text = "%s" % self.ui.lineEdit_area_path.text()
        ET.SubElement(doc, "Username", type = "str").text = "%s" % self.ui.lineEdit_user.text()
        ET.SubElement(doc, "Password", type = "str").text = "%s" % self.ui.lineEdit_password.text()
        ET.SubElement(doc, "VHRS", type = "str").text = "%s" % self.ui.lineEdit_VHRS.text()
        ET.SubElement(doc, "MNT", type = "str").text = "%s" % self.ui.lineEdit_MNT.text()
        
        doc = ET.SubElement(root, "Tab", id="Processing_sample")
        for sa in range(len(self.sample_name)):
            sub_doc = ET.SubElement(doc, "Sample", id="Sample_" + str(sa))
            ET.SubElement(sub_doc, "Sample_path", type = "list").text = self.sample_name[sa]
            ET.SubElement(sub_doc, "Fieldname_1", type = "list").text = self.fieldname_args[2*sa]
            ET.SubElement(sub_doc, "Fieldname_2", type = "list").text = self.fieldname_args[2*sa+1]
            ET.SubElement(sub_doc, "Classname_1", type = "list").text = self.class_args[2*sa]
            ET.SubElement(sub_doc, "Classname_2", type = "list").text = self.class_args[2*sa+1]
            ET.SubElement(sub_doc, "Nb_polygones", type = "list").text = self.list_nb_sample[sa]
            ET.SubElement(sub_doc, "RPG", type = "list").text = str(self.rpg_tchek[sa])
            try:
                # To enter a sample raster if the first tab doesn't launch before 
                if self.img_sample[sa] == 1:
                    ET.SubElement(sub_doc, "Img_sample", type = "list").text = self.raster_path[sa]
            except:
                print('Not sample raster only !')
            
        doc = ET.SubElement(root, "Tab", id="Classification")
        ET.SubElement(doc, "Segmentation_path", type = "str").text = "%s" % self.ui.lineEdit_segmentation.text()
        ET.SubElement(doc, "Output_path", type = "str").text = "%s" % self.ui.lineEdit_output.text()
        ET.SubElement(doc, "Output_fieldname_1", type = "str").text = "%s" % self.ui.lineEdit_fieldname_1.text()
        ET.SubElement(doc, "Output_fieldname_2", type = "str").text = "%s" % self.ui.lineEdit_fieldname_2.text()
        ET.SubElement(doc, "Output_fieldname_3", type = "str").text = "%s" % self.ui.lineEdit_fieldname_3.text()
        ET.SubElement(doc, "Output_fieldname_4", type = "str").text = "%s" % self.ui.lineEdit_fieldname_4.text()
        ET.SubElement(doc, "Output_type_1", type = "str").text = "%s" % self.ui.comboBox_fieldname_1.currentText()
        ET.SubElement(doc, "Output_type_2", type = "str").text = "%s" % self.ui.comboBox_fieldname_2.currentText()
        ET.SubElement(doc, "Output_type_3", type = "str").text = "%s" % self.ui.comboBox_fieldname_3.currentText()
        ET.SubElement(doc, "Output_type_4", type = "str").text = "%s" % self.ui.comboBox_fieldname_4.currentText()
#         
        tree = ET.ElementTree(root)
        # Write in a xml file
        tree.write(str(out_backup), pretty_print=True)
        print("Save input text !")
        
    def about_PHYMOBA(self):
        """
        Function to open a new window "About PHYMOBAT"
        """
        if self.apropos is None:
            self.apropos = MyPopup_about()
        self.apropos.show()
        
    def help_tools(self):
        """
        Function to open html help
        """

        webbrowser.open('file://' + os.getcwd() + '/Doc_Sphinx/sortie/methode_tuto.html#tutoriels-interface')
        
    def forget_study_area(self):
        """
        Function to open a new window 'Alert' because user forgotten to declare study area.
        """
        if self.w_study_area is None:
            self.w_study_area = MyPopup_warming_study_area()
        self.w_study_area.show()
        
    def close_button(self):
        """
        Function to close the interface.
        """
        sys.exit()

class MyPopup_about(QWidget):
    """
    Popup to display "About PHYMOBAT". In this windows, it prints informations on the processing, license
    and version.
    """
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.prop = Ui_About()
        self.prop.setupUi(self)
        
        self.connect(self.prop.close_newWindow, SIGNAL('clicked()'), self.close_window)
    
    def close_window(self):
        """
        Function to close the "A propos PHYMOBAT".
        """
        self.close()
        
class MyPopup_warming_study_area(QWidget):
    """
    Popup to display a message to say there isn't declared study area file.
    """
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.w_study_a = Ui_Warming_study_area()
        self.w_study_a.setupUi(self)
        
        self.connect(self.w_study_a.pushButton_ok_window_warning_study_area, SIGNAL('clicked()'), self.close_window)
    
    def close_window(self):
        """
        Function to close the popup.
        """
        self.close()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myapp = PHYMOBAT()
    myapp.show()
    
#     sys.exit(app.exec_())
