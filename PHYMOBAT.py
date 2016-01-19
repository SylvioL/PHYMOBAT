#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
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

"""
Interface main, PHYMOBAT (FB PHYsionomiquedes Milieux Ouverts de Basse Altitude par Télédétection)

__name__ = "PHYMOBAT 1.0"
__license__ = "GPL"
__version__ = "1.0"
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

from ui_PHYMOBAT_tab import Ui_PHYMOBAT
from Processing import Processing

class PHYMOBAT(QWidget, Processing):
    """
    Interface main class. It makes to link ``ui_PHYMOBAT_tab`` and ``Processing``.
    """
    
    def __init__(self, parent=None):
        super(PHYMOBAT, self).__init__(parent)
        Processing.__init__(self)
        self.initUI()
        
    def initUI(self):
        
        """
        Get initial values from interface after a click button.
        
        There is :
        
        - Connect browser button to search a path
            * Main folder path
            * VHRS image path
            * Study area shapefile path
            * Segmentation shapefile path
            * Output classification shapefile path
            * Sample shapefile path
            * Image path for samples if the first processing image hasn't been launched
            
        - Connect button to add sample in the memory list
        - Connect button to clear sample record. Clear in the interface and in the memory list
        - Connect cancel|ok button
        
        """
        
        # Initial interface
        self.ui = Ui_PHYMOBAT()
        self.ui.setupUi(self)
        
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
        
        # Connect cancel|ok button
        self.ui.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.cancel_button)
        self.ui.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.ok_button)
    
    def get_variable(self):
        
        """
        Append a few system value like :
        
        - Satellite captor name by combo box
        - Classification year by line edit
        - Connexion username and password by line edit
        - Output shapefile field name by line edit and field type by combo box
        
        """
        
        # Satellite captor name by combo box
        self.captor_project = self.ui.comboBox_captor.currentText()
        
        # Classification year by line edit
        self.classif_year = "%s" % self.ui.lineEdit_year_images.text()
        
        # Connexion username and password by line edit
        self.user = "%s" % self.ui.lineEdit_user.text()
        self.password = "%s" % self.ui.lineEdit_password.text()
        
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
 
    def set_variable(self):
        """
        Print number of available image from Theia's GeoJSON .
        """
        self.ui.lineEdit_listing.setText(str(self.nb_avalaible_images))
        
    def f_path_folder_dpt(self):
        """
        Set the main folder path by line edit.
        """
        infoldername = QFileDialog.getExistingDirectory(self, "Principal folder path", os.getcwd(), QFileDialog.ShowDirsOnly)
        self.ui.lineEdit_principal_folder.setText(str(infoldername).replace('[','').replace(']','').replace(' ',''))
        self.path_folder_dpt = "%s" % self.ui.lineEdit_principal_folder.text()
    
    def f_path_ortho(self):
        """
        Set the VHRS image path by line edit.
        """
        orthofilename = QFileDialog.getOpenFileName(self, "THRS image", os.getcwd(), '*.TIF *.tif')
        self.ui.lineEdit_VHRS.setText(str(orthofilename).replace('[','').replace(']','').replace(' ',''))   
        self.path_ortho = "%s" % self.ui.lineEdit_VHRS.text()
        
    def f_path_area(self):
        """
        Set the study area shapefile path by line edit.
        """        
        areafilename = QFileDialog.getOpenFileName(self, "Area shapefile", os.getcwd(), '*.shp')
        self.ui.lineEdit_area_path.setText(str(areafilename).replace('[','').replace(']','').replace(' ',''))
        self.path_area = "%s" % self.ui.lineEdit_area_path.text()
        
    def f_path_segm(self):
        """
        Set segmentation shapefile path path by line edit.
        """
        segmfilename = QFileDialog.getOpenFileName(self, "Segmentation shapefile", os.getcwd(), '*.shp')
        self.ui.lineEdit_segmentation.setText(str(segmfilename).replace('[','').replace(']','').replace(' ',''))
        self.path_segm = "%s" % self.ui.lineEdit_segmentation.text()
    
    def f_output_name_moba(self):
        """
        Set the output classification shapefile path by line edit.
        """
        outfilename = QFileDialog.getSaveFileName(self, "FB file", os.getcwd(), '*.shp')
        self.ui.lineEdit_output.setText(outfilename)
        self.output_name_moba = "%s" % self.ui.lineEdit_output.text()
        
    def enter_sample_name(self):
        """
        Set the sample shapefile path by line edit. With :func:`add_sample` conditions.
        """
        samplefilename = QFileDialog.getOpenFileName(self, "Sample shapefile", os.getcwd(), '*.shp')
        self.ui.lineEdit_sample_path.setText(str(samplefilename).replace('[','').replace(']','').replace(' ',''))
        
    def img_sample_name(self):
        """
        Set the image for samples path by line edit. With :func:`add_sample` conditions.
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
        
        if not self.ui.lineEdit_sample_path.text().isEmpty() and not self.ui.lineEdit_select_sample_fieldname_1.text().isEmpty() and \
                not self.ui.lineEdit_select_sample_fieldname_2.text().isEmpty() and not self.ui.lineEdit_select_sample_class_1.text().isEmpty() and \
                not self.ui.lineEdit_select_sample_class_2.text().isEmpty() and not self.ui.lineEdit_select_sample_nb_poly.text().isEmpty() and \
                nb_sample < 3:
            
            # Append a sample name by line Edit.
            if self.ui.checkBox_RPG.isChecked():
                # Check box, if the sample is RPG file. It launch the Rpg class. And append a other sample from Rpg class 
                self.sample_name.append(self.i_rpg("%s" % self.ui.lineEdit_sample_path.text()))
            else:
                self.sample_name.append("%s" % self.ui.lineEdit_sample_path.text())
            
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

            # Clear all line edit after addition, ie after click add button.
            self.ui.lineEdit_sample_path.clear()
            self.ui.lineEdit_select_sample_fieldname_1.clear()
            self.ui.lineEdit_select_sample_fieldname_2.clear()
            self.ui.lineEdit_select_sample_class_1.clear()
            self.ui.lineEdit_select_sample_class_2.clear()
            self.ui.lineEdit_select_sample_nb_poly.clear()
    
    def clear_sample(self):
        """
        Function to clear sample record. Clear in the interface and in the memory list.
        """
        self.sample_name = []
        self.fieldname_args = []
        self.class_args = []
        self.list_nb_sample = []
        
        self.ui.lineEdit_sample_path.clear()
        self.ui.lineEdit_select_sample_fieldname_1.clear()
        self.ui.lineEdit_select_sample_fieldname_2.clear()
        self.ui.lineEdit_select_sample_class_1.clear()
        self.ui.lineEdit_select_sample_class_2.clear()
        self.ui.lineEdit_select_sample_nb_poly.clear()
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
        
        - With a check box ``Multi-processing``. If the processing will be launch with multi process. By default, this is checked.
        - Append a few system value with :func:`get_variable`.
        - There are 3 principal check boxes :
            - for downloading and processing on theia platform :
                - here there are sub check boxes : to get number download available images, launch the image downloading and processing .
            - for compute optimal threshold.
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
        
        # Compute optimal threshold  
        if self.ui.checkBox_threshold.isChecked():
              
            self.i_sample()
        
        # Classification processing 
        if self.ui.checkBox_classifier.isChecked():
             
            self.i_classifier()
        
        # Clear variables after processing
        self.clear_sample()
        self.out_fieldname_carto = ['ID', 'AREA']
        self.out_fieldtype_carto = [ogr.OFTString, ogr.OFTReal]
        # Images after processing images
        self.out_ndvistats_folder_tab = []
            
        # End of the processus
        endTime = time.time() # Tps : Terminé
        print '...........' + ' Outputted to File in ' + str(endTime - startTime) + ' secondes'
        nb_day_processing = int(time.strftime('%d', time.gmtime(endTime - startTime))) - 1
        print "That is, " + str(nb_day_processing) + ' day(s) ' + time.strftime('%Hh %Mmin%S', time.gmtime(endTime - startTime))
        
    def cancel_button(self):
        """
        Function to close the interface.
        """
        sys.exit()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myapp = PHYMOBAT()
    myapp.show()
    
    sys.exit(app.exec_())
