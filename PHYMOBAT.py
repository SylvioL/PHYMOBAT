#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
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

"""
Interface main, PHYMOBAT (FB PHYsionomiquedes Milieux Ouverts de Basse Altitude par Télédétection)

__name__ = "PHYMOBAT 3.0"

__license__ = "GPL"

__version__ = "3.0"

__author__ = "LAVENTURE Sylvio - UMR TETIS / IRSTEA"

__date__ = "Mars 2016"
"""

import os, sys, time
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from _collections import defaultdict

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

from ui_A_propos_PHYMOBAT_window import Ui_About
from ui_Warming_study_area import Ui_Warming_study_area
from ui_Warming_forgetting import Ui_Warming_forgetting
from ui_Proxy_window import Ui_Proxy_window
from Processing import Processing

class PHYMOBAT(QMainWindow, Processing):
    """
    Interface main class. It makes to link ``ui_PHYMOBAT_tab`` and ``Processing``.
    """
    
    def __init__(self, mode = 0, parent=None):
        super(PHYMOBAT, self).__init__(parent)
        Processing.__init__(self)

        self.apropos = None # For the "About PHYMOBAT" window
        self.w_study_area = None # For the "Warming : forget study area" window
        self.w_forget = None # For the "Warming : forgetting" window
        
        self.simpli = None # For the "PHYMOBATs" window
        self.expert = None # For the "PHYMOBATe" window
        self.mode = mode # For the mode simple (0 by default) or expert (1)
        
        # To select interface's parameters        
        if self.mode == 1:
            print "Expert"
            global Ui_PHYMOBAT, _translate
            from ui_PHYMOBATe_tab import Ui_PHYMOBAT, _translate
        elif self.mode == 0:
            print "Simple"
            global Ui_PHYMOBAT, _translate
            from ui_PHYMOBATs_tab import Ui_PHYMOBAT, _translate
            
        self.initUI()
        
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
        - Connect menu bar tab (Open backup, save in a xml file, close, help, About PHYMOBAT, mode)
        - Initialize backup variable
        
        """
                    
        # Initial interface
        self.ui = Ui_PHYMOBAT()
        self.ui.setupUi(self)

        # Connect browser button to search a path
        ##########################################
        # Main folder path
        self.ui.lineEdit_principal_folder.clear()
        self.connect(self.ui.pushButton_browser_principal_folder, SIGNAL('clicked()'), self.f_path_folder_dpt)
        
        # Block other function if SpotWorldHeritage is chose
        try :
            self.ui.comboBox_captor.currentIndexChanged.connect(self.block_for_swh)
        except AttributeError:
            pass
        
        # VHRS image path
        self.ui.lineEdit_VHRS.clear()
        self.connect(self.ui.pushButton_browser_VHRS, SIGNAL('clicked()'), self.f_path_ortho)
        
        # Study area shapefile path
        self.ui.lineEdit_area_path.clear()
        self.connect(self.ui.pushButton_browser_area_path, SIGNAL('clicked()'), self.f_path_area)
        
        # Proxy
        self.connect(self.ui.proxy, SIGNAL('clicked()'), self.f_proxy)
        
        # Segmentation shapefile path
        self.ui.lineEdit_segmentation.clear()
        self.connect(self.ui.pushButton_browser_segmentation, SIGNAL('clicked()'), self.f_path_segm)
        
        # MNT image path
        self.ui.lineEdit_MNT.clear()
        self.connect(self.ui.pushButton_browser_MNT, SIGNAL('clicked()'), self.f_path_mnt)
        
        # Output classification shapefile path
        self.ui.lineEdit_output.clear()
        self.ui.pushButton_browser_output.clicked.connect(self.f_output_name_moba)
        
        # Sample shapefile path.
        # For the simply mode, RPG file sample.
        self.ui.lineEdit_sample_path.clear()
        self.ui.pushButton_browser_sample_path.clicked.connect(self.enter_sample_name)
    
        if self.mode == 0:
            # For the simply mode, grass/wooden file sample.
            self.ui.lineEdit_sample_path_2.clear()
            self.ui.pushButton_browser_sample_path_2.clicked.connect(self.enter_sample_name_hl)
            # For the simply mode, wooden file sample.
            self.ui.lineEdit_sample_path_3.clear()
            self.ui.pushButton_browser_sample_path_3.clicked.connect(self.enter_sample_name_ll)
            
        # Image path  for samples if the first processing image hasn't been launched
        try:
            self.connect(self.ui.pushButton_img_sample, SIGNAL('clicked()'), self.img_sample_name)
        except AttributeError:
            pass # Simple mode
        ##########################################

        # Connect button to add sample in the memory list
        try:
            self.connect(self.ui.pushButton_add_sample, SIGNAL('clicked()'), self.add_sample)
        except AttributeError:
            pass # Simple mode
        
        # Connect button to clear sample record. Clear in the interface and in the memory list
        try:
            self.connect(self.ui.pushButton_clear_sample, SIGNAL('clicked()'), self.clear_sample)
        except AttributeError:
            pass # Simple mode
        
        # Connect close|ok button
        self.ui.buttonBox.button(QDialogButtonBox.Close).clicked.connect(self.close_button)
        self.ui.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.ok_button)
        
        # Connect Menu bar
        self.ui.actionOuvrir.triggered.connect(self.open_backup) # Open backup
        self.ui.actionSauver.triggered.connect(self.save_backup) # Save field name on the interface
        self.ui.actionQuiter.triggered.connect(self.close_button) # Close
        self.ui.actionAide_de_PHYMOBAT.triggered.connect(self.help_tools) # Help
        self.ui.actionA_propos_de_PHYMOBAT.triggered.connect(self.about_PHYMOBA) # About PHYMOBA
        self.ui.actionMode_Simplifi.triggered.connect(self.mode_simpli) # To open the simple apply
        self.ui.actionMode_expert.triggered.connect(self.mode_expert) # To open the expert apply
        
        self.rpg_tchek = [] # To backup rpg mode
        self.img_sample = [] # To backup
        
        # Connect change line edit on sample path to extract fieldnames. For the simply mode, this
        # is with RPG sample
        self.ui.lineEdit_select_sample_fieldname_1.textChanged.connect(self.field_display_1)
        self.ui.lineEdit_select_sample_fieldname_2.textChanged.connect(self.field_display_2)
        
        # To choose the classification method
        if self.mode == 1:
            if self.ui.radioButton_rf.isChecked():
                self.ui.checkBox_classifier_1.setEnabled(False)
                self.ui.checkBox_classifier_2.setEnabled(False)
            
            self.ui.radioButton_rf.toggled.connect(self.activate_level)   
            self.ui.radioButton_s.toggled.connect(self.activate_level)
        
        if self.mode == 0:
            # Connect change line edit to grass/wooden sample
            self.ui.lineEdit_select_sample_fieldname_3.textChanged.connect(self.field_display_3)
            self.ui.lineEdit_select_sample_fieldname_4.textChanged.connect(self.field_display_4)
            self.ui.lineEdit_select_sample_fieldname_5.textChanged.connect(self.field_display_5)
            self.ui.lineEdit_select_sample_fieldname_6.textChanged.connect(self.field_display_6)
        
        # Change connect for classification checkboxes
        try:
            self.ui.checkBox_classifier_1.stateChanged.connect(self.display_one_level)
            self.ui.checkBox_classifier_2.stateChanged.connect(self.display_two_levels)
            self.ui.checkBox_classifier_3.stateChanged.connect(self.display_all_levels)
        except AttributeError:
            pass # Simple mode
        
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
        try:
            self.captor_project = self.ui.comboBox_captor.currentText()
        except AttributeError:
            self.captor_project = "Landsat"
        
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
        try:
            if self.ui.checkBox_classifier_1.isChecked() and self.ui.lineEdit_fieldname_1.text() != '':
                self.out_fieldname_carto.append("%s" % self.ui.lineEdit_fieldname_1.text())
                self.out_fieldtype_carto.append(eval("ogr.OFT%s" % self.ui.comboBox_fieldname_1.currentText()))
                
            if self.ui.checkBox_classifier_2.isChecked() and self.ui.lineEdit_fieldname_12.text() != '':
                self.out_fieldname_carto.append("%s" % self.ui.lineEdit_fieldname_12.text())
                self.out_fieldtype_carto.append(eval("ogr.OFT%s" % self.ui.comboBox_fieldname_12.currentText()))
            
                if self.ui.lineEdit_fieldname_2.text() != '':
                    self.out_fieldname_carto.append("%s" % self.ui.lineEdit_fieldname_2.text())
                    self.out_fieldtype_carto.append(eval("ogr.OFT%s" % self.ui.comboBox_fieldname_2.currentText()))
                
            if self.ui.checkBox_classifier_3.isChecked() and self.ui.lineEdit_fieldname_13.text() != '':
                self.out_fieldname_carto.append("%s" % self.ui.lineEdit_fieldname_13.text())
                self.out_fieldtype_carto.append(eval("ogr.OFT%s" % self.ui.comboBox_fieldname_13.currentText()))
            
                if self.ui.lineEdit_fieldname_23.text() != '':
                    self.out_fieldname_carto.append("%s" % self.ui.lineEdit_fieldname_23.text())
                    self.out_fieldtype_carto.append(eval("ogr.OFT%s" % self.ui.comboBox_fieldname_23.currentText()))
             
                    if self.ui.lineEdit_fieldname_3.text() != '':   
                        self.out_fieldname_carto.append("%s" % self.ui.lineEdit_fieldname_3.text())
                        self.out_fieldtype_carto.append(eval("ogr.OFT%s" % self.ui.comboBox_fieldname_3.currentText()))
            
                        if self.ui.lineEdit_fieldname_4.text() != '':    
                            self.out_fieldname_carto.append("%s" % self.ui.lineEdit_fieldname_4.text())
                            self.out_fieldtype_carto.append(eval("ogr.OFT%s" % self.ui.comboBox_fieldname_4.currentText()))
        except AttributeError:
            modes_fieldname = ["NIVEAU_1", "NIVEAU_2", "NIVEAU_3", "POURC"]
            modes_fieldtype = [eval("ogr.OFTString"), eval("ogr.OFTString"), eval("ogr.OFTString"), eval("ogr.OFTReal")]
            
            for mf in range(len(modes_fieldname)):
                
                self.out_fieldname_carto.append(modes_fieldname[mf])
                self.out_fieldtype_carto.append(modes_fieldtype[mf])
        
        # Segmentation shapefile path path by line edit
        self.path_segm = "%s" % self.ui.lineEdit_segmentation.text()
        
        # Output shapefile field name by line edit and field type by combo box
        self.output_name_moba = "%s" % self.ui.lineEdit_output.text()
        
    def set_variable(self):
        """
        Print number of available image from Theia's GeoJSON .
        """
        # self.ui.lineEdit_listing.setText(str(self.nb_avalaible_images))
        try:
            self.ui.label_listing.setText(str(self.nb_avalaible_images))
        except AttributeError:
            pass # Simple mode
        
    def f_path_folder_dpt(self):
        """
        Open a input browser box to select the main folder path by line edit.
        """
        infoldername = QFileDialog.getExistingDirectory(self, "Principal folder path", os.getcwd(), QFileDialog.ShowDirsOnly)
        self.ui.lineEdit_principal_folder.setText(str(infoldername).replace('[','').replace(']','').replace(' ',''))
    
    def block_for_swh(self):
        """
        Function to block others function when SportWorldHeritage is selected in the comboxbox captor.
        """
        ind_captor = int(self.ui.comboBox_captor.currentIndex())
        if ind_captor == 2:
            self.ui.checkBox_processing.setEnabled(False)
            self.ui.checkBox_MNT.setEnabled(False)
            self.ui.lineEdit_MNT.setEnabled(False)
            self.ui.pushButton_browser_MNT.setEnabled(False)
            self.ui.checkBox_VHRS.setEnabled(False)
            self.ui.lineEdit_VHRS.setEnabled(False)
            self.ui.pushButton_browser_VHRS.setEnabled(False)
            self.ui.tabWidget.setTabEnabled(1, False)
            self.ui.tabWidget.setTabEnabled(2, False)
        # If the user want, on the same moment, come back on other captor that SWH.
        else:
            self.ui.checkBox_processing.setEnabled(True)
            self.ui.checkBox_MNT.setEnabled(True)
            self.ui.lineEdit_MNT.setEnabled(True)
            self.ui.pushButton_browser_MNT.setEnabled(True)
            self.ui.checkBox_VHRS.setEnabled(True)
            self.ui.lineEdit_VHRS.setEnabled(True)
            self.ui.pushButton_browser_VHRS.setEnabled(True)
            self.ui.tabWidget.setTabEnabled(1, True)
            self.ui.tabWidget.setTabEnabled(2, True)
    
    def f_path_ortho(self):
        """
        Open a input browser box to select the VHRS image path by line edit.
        """
        orthofilename = QFileDialog.getOpenFileName(self, "THRS image", self.ui.lineEdit_principal_folder.text(), '*.TIF *.tif')
        self.ui.lineEdit_VHRS.setText(str(orthofilename).replace('[','').replace(']','').replace(' ',''))   
    
    def f_path_mnt(self):
        """
        Open a input browser box to select the MNT image path by line edit.
        """
        mntfilename = QFileDialog.getOpenFileName(self, "MNT image", self.ui.lineEdit_principal_folder.text(), '*.TIF *.tif')
        self.ui.lineEdit_MNT.setText(str(mntfilename).replace('[','').replace(']','').replace(' ',''))  
        
    def f_path_area(self):
        """
        Open a input browser box to select the study area shapefile path by line edit.
        """        
        areafilename = QFileDialog.getOpenFileName(self, "Area shapefile", self.ui.lineEdit_principal_folder.text(), '*.shp')
        self.ui.lineEdit_area_path.setText(str(areafilename).replace('[','').replace(']','').replace(' ',''))
        
    def f_proxy(self):   
        """
        Function to open a popup in order to enter proxy ID
        """ 
        if self.w_proxy is None:
            self.w_proxy = MyPopup_proxy_window()
        self.w_proxy.show()
        
    def f_path_segm(self):
        """
        Open a input browser box to select segmentation shapefile path path by line edit.
        """
        segmfilename = QFileDialog.getOpenFileName(self, "Segmentation shapefile", self.ui.lineEdit_principal_folder.text(), '*.shp')
        self.ui.lineEdit_segmentation.setText(str(segmfilename).replace('[','').replace(']','').replace(' ',''))
    
    def f_output_name_moba(self):
        """
        Set the output classification shapefile path by line edit.
        """
        outfilename = QFileDialog.getSaveFileName(self, "FB file", self.ui.lineEdit_principal_folder.text(), '*.shp')
        # if the user has forgotten to put .shp at the end of the output shapefile
        if outfilename[-4:] != '.shp':
            outfilename = outfilename + '.shp'
        self.ui.lineEdit_output.setText(outfilename)
        
    def enter_sample_name(self):
        """
        Open a input browser box to select the sample shapefile path by line edit. With :func:`add_sample` conditions for the expert mode.
        For the simply mode, this function is used for the RPG shapefile.
        """
        samplefilename = QFileDialog.getOpenFileName(self, "Sample shapefile", self.ui.lineEdit_principal_folder.text(), '*.shp')
        self.ui.lineEdit_sample_path.setText(str(samplefilename).replace('[','').replace(']','').replace(' ',''))
    
    def enter_sample_name_hl(self):
        """
        Open a input browser box to select the grass and wooden sample shapefile path by line edit. With :func:`add_sample` conditions 
        for the simply mode.
        """
        samplefilename_hl = QFileDialog.getOpenFileName(self, "Grass/Wooden sample shapefile", self.ui.lineEdit_principal_folder.text(), '*.shp')
        self.ui.lineEdit_sample_path_2.setText(str(samplefilename_hl).replace('[','').replace(']','').replace(' ',''))
        
    def enter_sample_name_ll(self):
        """
        Open a input browser box to select the wooden sample shapefile path by line edit. With :func:`add_sample` conditions for the simply mode.
        """
        samplefilename_ll = QFileDialog.getOpenFileName(self, "Wooden sample shapefile", self.ui.lineEdit_principal_folder.text(), '*.shp')
        self.ui.lineEdit_sample_path_3.setText(str(samplefilename_ll).replace('[','').replace(']','').replace(' ',''))
        
    def img_sample_name(self):
        """
        Open a input browser box to select the image for samples path by line edit. With :func:`add_sample` conditions.
        """
        imgsamplefilename = QFileDialog.getOpenFileName(self, "Sample image", self.ui.lineEdit_principal_folder.text(), '*.TIF')
        self.ui.lineEdit_img_sample.setText(str(imgsamplefilename).replace('[','').replace(']','').replace(' ',''))
        
    def add_sample(self):
        """
        Add sample information and location to compute optimal threshold :
        
        For the expert mode (mode=1) :
        
        - Append a sample name by line Edit. *This is a check box* ``RPG``, *if the sample is RPG file. It launch the Rpg class. And append a other sample from Rpg class*.
        - Append two existent sample field names by combobox. It will be the same. 
        - Append sample class names by line edit. One or more for every sample.
        - Append number of polygons for every samples by line edit.
        - Print in a plain text edit : sample name, two sample field names, sample class names and number of polygons.
        - *This check box* ``Image echantillonee``, *image path for samples if the first processing image hasn't been launched*.
            .. note:: This is for a image with one spectral band
        - Clear all widget field at the end.
        
        For the simply mode (mode=0):
        
        - Append a sample name by a different line Edit (a line Edit for each sample).
        - Append sample class names, existing sample fields and number of polygons (a different line Edit for each sample)
        """
        
        nb_sample = len(self.sample_name)# Compute number of samples added. Condition : max three. 
        # Study area shapefile path by line edit if no processing other
        # Because the function "Vector" need study area
        self.path_area = "%s" % self.ui.lineEdit_area_path.text()
        if self.path_area == '':
            self.forget_study_area()
        
        if self.mode == 1:
            # Expert mode
            if nb_sample < 3 and not self.ui.lineEdit_sample_path.text().isEmpty() and  \
                    not self.ui.lineEdit_select_sample_fieldname_1.text().isEmpty() and not self.ui.lineEdit_select_sample_fieldname_2.text().isEmpty() and \
                    not self.ui.lineEdit_select_sample_class_1.text().isEmpty() and not self.ui.lineEdit_select_sample_class_2.text().isEmpty() and \
                    not self.ui.lineEdit_select_sample_nb_poly.text().isEmpty() and not self.ui.lineEdit_area_path.text().isEmpty():
                
                # Append a sample name by line Edit.
                if self.ui.checkBox_RPG.isChecked():
                    # Check box, if the sample of the RPG file. It launch the Rpg class. And append a other sample from Rpg class 
                    self.sample_name.append(self.i_rpg("%s" % self.ui.lineEdit_sample_path.text()))
                    self.rpg_tchek.append(1) # To backup
                    self.ui.checkBox_RPG.setChecked(False)
                else:
                    self.sample_name.append("%s" % self.ui.lineEdit_sample_path.text())
                    self.rpg_tchek.append(0)
                
                # Append two sample field names by line edit. It must be the same.
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
                    self.ui.checkBox_img_sample.setChecked(False)
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
                
        elif self.mode == 0:
            
            # Simple mode
            # Append a sample name by line Edit.
            # For the sample of the RPG file. It launch the Rpg class. And append a other sample from Rpg class 
            self.sample_name.append(self.i_rpg("%s" % self.ui.lineEdit_sample_path.text()))
            
            # Append two sample field names by line edit. It must be the same.
            self.fieldname_args.append("%s" % self.ui.lineEdit_select_sample_fieldname_1.text())
            self.fieldname_args.append("%s" % self.ui.lineEdit_select_sample_fieldname_2.text())
            # Append sample class names by line edit. One or more for every sample
            self.class_args.append("%s" % self.ui.lineEdit_select_sample_class_1.text())
            self.class_args.append("%s" % self.ui.lineEdit_select_sample_class_2.text())
            # Append number of polygons for every samples by line edit.
            self.list_nb_sample.append("%s" % self.ui.lineEdit_select_sample_nb_poly.text())
            
            # Same process that the RPG process except the start of the RPG class.
            # To Grass/wooden
            self.sample_name.append("%s" % self.ui.lineEdit_sample_path_2.text())
            self.fieldname_args.append("%s" % self.ui.lineEdit_select_sample_fieldname_3.text())
            self.fieldname_args.append("%s" % self.ui.lineEdit_select_sample_fieldname_4.text())
            self.class_args.append("%s" % self.ui.lineEdit_select_sample_class_3.text())
            self.class_args.append("%s" % self.ui.lineEdit_select_sample_class_4.text())
            self.list_nb_sample.append("%s" % self.ui.lineEdit_select_sample_nb_poly_2.text())
            
            # To wooden
            self.sample_name.append("%s" % self.ui.lineEdit_sample_path_3.text())
            self.fieldname_args.append("%s" % self.ui.lineEdit_select_sample_fieldname_5.text())
            self.fieldname_args.append("%s" % self.ui.lineEdit_select_sample_fieldname_6.text())
            self.class_args.append("%s" % self.ui.lineEdit_select_sample_class_5.text())
            self.class_args.append("%s" % self.ui.lineEdit_select_sample_class_6.text())
            self.list_nb_sample.append("%s" % self.ui.lineEdit_select_sample_nb_poly_3.text())
            
            nb_sample = 3
    
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
        self.ui.checkBox_img_sample.setChecked(False)
        self.ui.plainTextEdit_sample.clear()
        self.ui.plainTextEdit_sample.insertPlainText(_fromUtf8("1 - Végétation non naturelle / Semi-naturelle\n"))
        self.ui.plainTextEdit_sample.insertPlainText(_fromUtf8("2 - Herbacés / Ligneux\n"))
        self.ui.plainTextEdit_sample.insertPlainText("3 - Lingeux mixtes / denses\n")
        self.ui.plainTextEdit_sample.insertPlainText("\n")
        self.ui.plainTextEdit_sample.insertPlainText("\n")
        self.ui.plainTextEdit_sample.insertPlainText("")            
        
    def field_display_1(self):
        """
        Function to display fieldname class 1 in the other fieldname class 2 when text changed.
        For the simply mode, this is RPG sample.
        """
        
        self.ui.lineEdit_select_sample_fieldname_2.setText("%s" % self.ui.lineEdit_select_sample_fieldname_1.text())
            
    def field_display_2(self):
        """
        Function to display fieldname class 2 in the other fieldname class 2 when text changed.
        For the simply mode, this is RPG sample.
        """
        
        self.ui.lineEdit_select_sample_fieldname_1.setText("%s" % self.ui.lineEdit_select_sample_fieldname_2.text())    
        
    def field_display_3(self):
        """
        For the grass/wooden sample, a function to display fieldname class 1 in the other fieldname class 2 when text changed.
        """
        
        self.ui.lineEdit_select_sample_fieldname_4.setText("%s" % self.ui.lineEdit_select_sample_fieldname_3.text())
            
    def field_display_4(self):
        """
        For the grass/wooden sample, a function to display fieldname class 2 in the other fieldname class 2 when text changed.
        """
        
        self.ui.lineEdit_select_sample_fieldname_3.setText("%s" % self.ui.lineEdit_select_sample_fieldname_4.text()) 
        
    def field_display_5(self):
        """
        For the wooden sample, a function to display fieldname class 1 in the other fieldname class 2 when text changed.
        """
        
        self.ui.lineEdit_select_sample_fieldname_6.setText("%s" % self.ui.lineEdit_select_sample_fieldname_5.text())
            
    def field_display_6(self):
        """
        For the wooden sample, a function to display fieldname class 2 in the other fieldname class 2 when text changed.
        """
        
        self.ui.lineEdit_select_sample_fieldname_5.setText("%s" % self.ui.lineEdit_select_sample_fieldname_6.text()) 
    
    def activate_level(self):
        """
        To activate the first levels with seath method. This is in pushing on the decision tree radio button.
        Else it activates the last level to random forest method.
        """
        if self.ui.radioButton_s.isChecked() and not self.ui.radioButton_rf.isChecked():
            self.ui.checkBox_classifier_1.setEnabled(True)
            self.ui.checkBox_classifier_2.setEnabled(True)
        else:
            self.ui.checkBox_classifier_1.setEnabled(False)
            self.ui.checkBox_classifier_2.setEnabled(False)
            self.ui.checkBox_classifier_3.setChecked(True)
            
        
    def display_one_level(self):
        """
        Function to display fieldnames option to classifier one level
        """
        if self.ui.checkBox_classifier_1.isChecked():
            
            # Don't checked others checkboxes
            self.ui.checkBox_classifier_2.setChecked(False)
            self.ui.checkBox_classifier_3.setChecked(False)
            
            # Display options filednames
            self.ui.label_chps_1 = QLabel(self.ui.tab_3)
            self.ui.label_chps_1.setObjectName(_fromUtf8("label_chps_1"))
            self.ui.gridLayout_2.addWidget(self.ui.label_chps_1, 10, 0, 2, 2)
            self.ui.label_chps_name_1 = QLabel(self.ui.tab_3)
            self.ui.label_chps_name_1.setObjectName(_fromUtf8("label_chps_name_1"))
            self.ui.gridLayout_2.addWidget(self.ui.label_chps_name_1, 10, 2, 1, 1)
            self.ui.label_chps_type_1 = QLabel(self.ui.tab_3)
            self.ui.label_chps_type_1.setObjectName(_fromUtf8("label_chps_type_1"))
            self.ui.gridLayout_2.addWidget(self.ui.label_chps_type_1, 11, 2, 1, 1)
            self.ui.lineEdit_fieldname_1 = QLineEdit(self.ui.tab_3)
            self.ui.lineEdit_fieldname_1.setObjectName(_fromUtf8("lineEdit_fieldname_1"))
            self.ui.gridLayout_2.addWidget(self.ui.lineEdit_fieldname_1, 10, 3, 1, 1)
            self.ui.comboBox_fieldname_1 = QComboBox(self.ui.tab_3)
            self.ui.comboBox_fieldname_1.setObjectName(_fromUtf8("comboBox_fieldname_1"))
            self.ui.gridLayout_2.addWidget(self.ui.comboBox_fieldname_1, 11, 3, 1, 1)
    
            self.ui.lineEdit_fieldname_1.setText(_translate("PHYMOBAT", "NIVEAU_1", None))
            self.ui.comboBox_fieldname_1.addItem("String")
            self.ui.comboBox_fieldname_1.addItem("Real")
    
            self.ui.label_chps_1.setText(_translate("PHYMOBAT", "    Champs\n"+" des entités", None))
            self.ui.label_chps_name_1.setText(_translate("PHYMOBAT", "Nom :", None))   
            self.ui.label_chps_type_1.setText(_translate("PHYMOBAT", "Type :", None)) 
         
        if not self.ui.checkBox_classifier_1.isChecked(): 
            # Clear options filednames
            try:
                self.ui.label_chps_1.deleteLater()
                self.ui.label_chps_name_1.deleteLater()
                self.ui.label_chps_type_1.deleteLater()  
                self.ui.lineEdit_fieldname_1.deleteLater()
                self.ui.comboBox_fieldname_1.deleteLater()
            except AttributeError:      
                pass
    
    def display_two_levels(self):
        """
        Function to display fieldnames option to classifier two first levels
        """
        
        if self.ui.checkBox_classifier_2.isChecked():
            
            # Don't checked others checkboxes
            self.ui.checkBox_classifier_1.setChecked(False)
            self.ui.checkBox_classifier_3.setChecked(False)
        
            self.ui.label_chps_2 = QLabel(self.ui.tab_3)
            self.ui.label_chps_2.setObjectName(_fromUtf8("label_chps_2"))
            self.ui.gridLayout_2.addWidget(self.ui.label_chps_2, 13, 0, 2, 2)
            self.ui.lineEdit_fieldname_12 = QLineEdit(self.ui.tab_3)
            self.ui.lineEdit_fieldname_12.setObjectName(_fromUtf8("lineEdit_fieldname_12"))
            self.ui.gridLayout_2.addWidget(self.ui.lineEdit_fieldname_12, 13, 3, 1, 1)
            self.ui.lineEdit_fieldname_2 = QLineEdit(self.ui.tab_3)
            self.ui.lineEdit_fieldname_2.setObjectName(_fromUtf8("lineEdit_fieldname_2"))
            self.ui.gridLayout_2.addWidget(self.ui.lineEdit_fieldname_2, 13, 4, 1, 1)    
            self.ui.label_chps_type_2 = QLabel(self.ui.tab_3)
            self.ui.label_chps_type_2.setObjectName(_fromUtf8("label_chps_type_2"))
            self.ui.gridLayout_2.addWidget(self.ui.label_chps_type_2, 14, 2, 1, 1)
            self.ui.comboBox_fieldname_12 = QComboBox(self.ui.tab_3)
            self.ui.comboBox_fieldname_12.setObjectName(_fromUtf8("comboBox_fieldname_12"))
            self.ui.gridLayout_2.addWidget(self.ui.comboBox_fieldname_12, 14, 3, 1, 1)
            self.ui.comboBox_fieldname_2 = QComboBox(self.ui.tab_3)
            self.ui.comboBox_fieldname_2.setObjectName(_fromUtf8("comboBox_fieldname_2"))
            self.ui.gridLayout_2.addWidget(self.ui.comboBox_fieldname_2, 14, 4, 1, 1)
            self.ui.label_chps_name_2 = QLabel(self.ui.tab_3)
            self.ui.label_chps_name_2.setObjectName(_fromUtf8("label_chps_name_2"))
            self.ui.gridLayout_2.addWidget(self.ui.label_chps_name_2, 13, 2, 1, 1)
            
            self.ui.lineEdit_fieldname_12.setText(_translate("PHYMOBAT", "NIVEAU_1", None))
            self.ui.comboBox_fieldname_12.addItem("String")
            self.ui.comboBox_fieldname_12.addItem("Real")
            self.ui.lineEdit_fieldname_2.setText(_translate("PHYMOBAT", "NIVEAU_2", None))
            self.ui.comboBox_fieldname_2.addItem("String")
            self.ui.comboBox_fieldname_2.addItem("Real")
            
            self.ui.label_chps_type_2.setText(_translate("PHYMOBAT", "Type :", None))
            self.ui.label_chps_2.setText(_translate("PHYMOBAT", "    Champs\n"+" des entités", None))
            self.ui.label_chps_name_2.setText(_translate("PHYMOBAT", "Nom :", None))
        
        if not self.ui.checkBox_classifier_2.isChecked(): 
            # Clear options filednames
            try:
                self.ui.label_chps_2.deleteLater()
                self.ui.label_chps_name_2.deleteLater()
                self.ui.label_chps_type_2.deleteLater()  
                self.ui.lineEdit_fieldname_12.deleteLater()
                self.ui.comboBox_fieldname_12.deleteLater()
                self.ui.lineEdit_fieldname_2.deleteLater()
                self.ui.comboBox_fieldname_2.deleteLater()
            except AttributeError:      
                pass
        
    def display_all_levels(self):
        """
        Function to display fieldnames option to launch complete classification
        """
        
        if self.ui.checkBox_classifier_3.isChecked():
            
            # Don't checked others checkboxes
            self.ui.checkBox_classifier_1.setChecked(False)
            self.ui.checkBox_classifier_2.setChecked(False)
        
            self.ui.label_chps_name_3 = QLabel(self.ui.tab_3)
            self.ui.label_chps_name_3.setObjectName(_fromUtf8("label_chps_name_3"))
            self.ui.gridLayout_2.addWidget(self.ui.label_chps_name_3, 16, 2, 1, 1)
            self.ui.label_chps_3 = QLabel(self.ui.tab_3)    
            self.ui.label_chps_3.setObjectName(_fromUtf8("label_chps_3"))
            self.ui.gridLayout_2.addWidget(self.ui.label_chps_3, 16, 0, 2, 2)
            self.ui.label_chps_type_3 = QLabel(self.ui.tab_3)
            self.ui.label_chps_type_3.setObjectName(_fromUtf8("label_chps_type_3"))
            self.ui.gridLayout_2.addWidget(self.ui.label_chps_type_3, 17, 2, 1, 1)
            self.ui.lineEdit_fieldname_13 = QLineEdit(self.ui.tab_3)
            self.ui.lineEdit_fieldname_13.setObjectName(_fromUtf8("lineEdit_fieldname_13"))
            self.ui.gridLayout_2.addWidget(self.ui.lineEdit_fieldname_13, 16, 3, 1, 1)
            self.ui.lineEdit_fieldname_23 = QLineEdit(self.ui.tab_3)
            self.ui.lineEdit_fieldname_23.setObjectName(_fromUtf8("lineEdit_fieldname_23"))
            self.ui.gridLayout_2.addWidget(self.ui.lineEdit_fieldname_23, 16, 4, 1, 1)
            self.ui.lineEdit_fieldname_3 = QLineEdit(self.ui.tab_3)
            self.ui.lineEdit_fieldname_3.setObjectName(_fromUtf8("lineEdit_fieldname_3"))
            self.ui.gridLayout_2.addWidget(self.ui.lineEdit_fieldname_3, 16, 5, 1, 1)
            self.ui.lineEdit_fieldname_4 = QLineEdit(self.ui.tab_3)
            self.ui.lineEdit_fieldname_4.setObjectName(_fromUtf8("lineEdit_fieldname_4"))
            self.ui.gridLayout_2.addWidget(self.ui.lineEdit_fieldname_4, 16, 6, 1, 1)
            self.ui.comboBox_fieldname_13 = QComboBox(self.ui.tab_3)
            self.ui.comboBox_fieldname_13.setObjectName(_fromUtf8("comboBox_fieldname_13"))
            self.ui.gridLayout_2.addWidget(self.ui.comboBox_fieldname_13, 17, 3, 1, 1)
            self.ui.comboBox_fieldname_23 = QComboBox(self.ui.tab_3)
            self.ui.comboBox_fieldname_23.setObjectName(_fromUtf8("comboBox_fieldname_23"))
            self.ui.gridLayout_2.addWidget(self.ui.comboBox_fieldname_23, 17, 4, 1, 1)
            self.ui.comboBox_fieldname_3 = QComboBox(self.ui.tab_3)
            self.ui.comboBox_fieldname_3.setObjectName(_fromUtf8("comboBox_fieldname_3"))
            self.ui.gridLayout_2.addWidget(self.ui.comboBox_fieldname_3, 17, 5, 1, 1)
            self.ui.comboBox_fieldname_4 = QComboBox(self.ui.tab_3)
            self.ui.comboBox_fieldname_4.setObjectName(_fromUtf8("comboBox_fieldname_4"))
            self.ui.gridLayout_2.addWidget(self.ui.comboBox_fieldname_4, 17, 6, 1, 1)
            
            self.ui.lineEdit_fieldname_13.setText(_translate("PHYMOBAT", "NIVEAU_1", None))
            self.ui.comboBox_fieldname_13.addItem("String")
            self.ui.comboBox_fieldname_13.addItem("Real")
            self.ui.lineEdit_fieldname_23.setText(_translate("PHYMOBAT", "NIVEAU_2", None))
            self.ui.comboBox_fieldname_23.addItem("String")
            self.ui.comboBox_fieldname_23.addItem("Real")
            self.ui.lineEdit_fieldname_3.setText(_translate("PHYMOBAT", "NIVEAU_3", None))
            self.ui.comboBox_fieldname_3.addItem("String")
            self.ui.comboBox_fieldname_3.addItem("Real")
            self.ui.lineEdit_fieldname_4.setText(_translate("PHYMOBAT", "POURC", None))
            self.ui.comboBox_fieldname_4.addItem("Real")  
            self.ui.comboBox_fieldname_4.addItem("String")
            
            self.ui.label_chps_3.setText(_translate("PHYMOBAT", "    Champs\n"+" des entités", None))
            self.ui.label_chps_type_3.setText(_translate("PHYMOBAT", "Type :", None))
            self.ui.label_chps_name_3.setText(_translate("PHYMOBAT", "Nom :", None))
        
        if not self.ui.checkBox_classifier_3.isChecked(): 
            # Clear options filednames
            try:
                self.ui.label_chps_3.deleteLater()
                self.ui.label_chps_name_3.deleteLater()
                self.ui.label_chps_type_3.deleteLater()  
                self.ui.lineEdit_fieldname_13.deleteLater()
                self.ui.comboBox_fieldname_13.deleteLater()
                self.ui.lineEdit_fieldname_23.deleteLater()
                self.ui.comboBox_fieldname_23.deleteLater()
                self.ui.lineEdit_fieldname_3.deleteLater()
                self.ui.comboBox_fieldname_3.deleteLater()
                self.ui.lineEdit_fieldname_4.deleteLater()
                self.ui.comboBox_fieldname_4.deleteLater()
            except AttributeError:      
                pass
            
    def ok_button(self):
        
        """
        Function to launch the processing. This function take account :
        
        - The ``Multi-processing`` check box if the processing has launched with multi process. By default, this is checked. It need a computer with minimum 12Go memory.
        - Append a few system value with :func:`get_variable`.
        - There are 3 principal check boxes :
            - to get number download available images
            - for downloading and processing on theia platform
            - to compute optimal threshold.
            - to compute slope raster
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
        ok = 1 # Variable to verify informations -> 0 not ok, 1 ok
        
        if self.mode == 1:
            # if download check box is checked only
            if not self.ui.checkBox_listing.isChecked() and self.ui.checkBox_download.isChecked():
                
                self.ui.checkBox_listing.setChecked(True)
                
    #         # if processing check box is checked only
    #         if not self.ui.checkBox_listing.isChecked() and not self.ui.checkBox_download.isChecked() and self.ui.checkBox_processing.isChecked():
    #             
    #             self.ui.checkBox_listing.setChecked(True) 
    #             self.ui.checkBox_download.setChecked(True) 
                
            # Verify raster or sample to launch a good processing classification tab
            # If not ok, there will appear a message windows to enter the miss information
    #         if self.ui.checkBox_classifier_1.isChecked():
    #             if not self.ui.checkBox_processing.isChecked() or (len(self.raster_path) < 1 and len(self.sample_name) > 0) or \
    #             len(self.sample_name) < 1:
    #                 self.forget_raster_sample()
    #                 ok = 0
    #         if self.ui.checkBox_classifier_2.isChecked():
    #             if (not self.ui.checkBox_processing.isChecked() and not self.ui.checkBox_MNT.isChecked() and \
    #             not self.ui.checkBox_VHRS.isChecked()) or (len(self.raster_path) < 2 and len(self.sample_name) > 0) or \
    #             len(self.sample_name) < 2:
    #                 self.forget_raster_sample()
    #                 ok = 0
    #         if self.ui.checkBox_classifier_3.isChecked():
    #             if (not self.ui.checkBox_processing.isChecked() and not self.ui.checkBox_MNT.isChecked() and \
    #             not self.ui.checkBox_VHRS.isChecked()) or (len(self.raster_path) != 6 and len(self.sample_name) > 0) or \
    #             len(self.sample_name) != 3:
    #                 self.forget_raster_sample() 
    #                 ok = 0
            
            if ok == 1:       
                # Compute a output slope raster 
                if self.ui.checkBox_MNT.isChecked():
                
                    self.i_slope()       
                
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
                
                # To launch the image processing without dowloading but with the images in a main folder
                # Without internet connection
                if not self.ui.checkBox_download.isChecked() and self.ui.checkBox_processing.isChecked():
                    
                    # Launch pre-processing without downloading
                    self.i_glob()
                    # Another check box to launch VHRS texture processing. If checked, vs = 1.
                    if self.ui.checkBox_VHRS.isChecked():
                        vs = 1
                    self.i_images_processing(vs) # function to launch the image processing            
                
                # To launch texture processing only
                if not self.ui.checkBox_listing.isChecked() and not self.ui.checkBox_processing.isChecked() and self.ui.checkBox_VHRS.isChecked():
                    
                    self.i_vhrs()
                
                # Compute optimal threshold  
                if self.ui.checkBox_threshold.isChecked():
                    
                    if self.ui.radioButton_rf.isChecked():
                        self.i_sample_rf()
                    elif self.ui.radioButton_s.isChecked():
                        self.i_sample()
                
                # Classification processing 
                if self.ui.radioButton_rf.isChecked():
                    
                    if self.ui.checkBox_classifier_3.isChecked():
                        
                        self.out_fieldname_carto = self.out_fieldname_carto
                        self.out_fieldtype_carto = self.out_fieldtype_carto             
                        self.i_classifier_rf()
                        self.i_validate()
                        
                elif self.ui.radioButton_s.isChecked():
                    
                    if self.ui.checkBox_classifier_1.isChecked() :         
                        
                        self.out_fieldname_carto = self.out_fieldname_carto[:3]
                        self.out_fieldtype_carto = self.out_fieldtype_carto[:3]
                        self.i_classifier_s()
                        self.i_validate()
                        
                    if self.ui.checkBox_classifier_2.isChecked() :
                        
                        self.out_fieldname_carto = self.out_fieldname_carto[:4]
                        self.out_fieldtype_carto = self.out_fieldtype_carto[:4]             
                        self.i_classifier_s()
                        self.i_validate()
                        
                    if self.ui.checkBox_classifier_3.isChecked():
                        
                        self.out_fieldname_carto = self.out_fieldname_carto
                        self.out_fieldtype_carto = self.out_fieldtype_carto             
                        self.i_classifier_s()
                        self.i_validate()
                    
        if self.mode == 0:
            
            # Compute a output slope raster 
            if self.path_mnt != '':
                self.i_slope()
            
            # Save the sample features
            self.add_sample()
            try:
                # Look at if the the images has been already downlaoded
                self.i_glob()
            except:
                # Else the processus download it
                self.i_download(1)
            
            # function to launch the image processing    
            self.i_images_processing(1)
            # To launch texture processing only
            self.i_vhrs()
            # Compute optimal threshold 
            self.i_sample_rf()
                    
            # Classification processing 
            self.out_fieldname_carto = self.out_fieldname_carto
            self.out_fieldtype_carto = self.out_fieldtype_carto 
            self.i_classifier_rf()
            self.i_validate()
            
            
#         # Clear variables after processing
#         self.clear_sample()
        self.out_fieldname_carto = ['ID', 'AREA']
        self.out_fieldtype_carto = [ogr.OFTString, ogr.OFTReal]
        # Images after processing images
        self.out_ndvistats_folder_tab = defaultdict(list)
        
        Processing.__init__(self)# Initialize variable without to close and launch again the application
        
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
        
        if in_backup != None and len(in_backup) > 0:
            # Parse the xml file if the user choose a file
            tree = ET.parse(str(in_backup))
            
            if tree.find("Multi_process").text == '1':
                self.ui.checkBox_multiprocess.setChecked(True)
            else:
                self.ui.checkBox_multiprocess.setChecked(False)
            
            pr = tree.find("Tab[@id='Processing_raster']")
            try:
                self.ui.lineEdit_principal_folder.setText(pr.find("Principal_folder").text)
            except:
                print('Not principal folder')
            if self.mode == 1:
                index_captor = self.ui.comboBox_captor.findText(pr.find("Captor").text) # To find combo box index
                self.ui.comboBox_captor.setCurrentIndex(index_captor)
            try:
                self.ui.lineEdit_year_images.setText(pr.find("Year_images").text)
            except:
                print('Not year images')
            self.ui.lineEdit_area_path.setText(pr.find("Area_path").text)
            
            if self.mode == 1:
                if pr.find("Images_available").text == '1':
                    self.ui.checkBox_listing.setChecked(True)
                else:
                    self.ui.checkBox_listing.setChecked(False)
                if pr.find("Download").text == '1':
                    self.ui.checkBox_download.setChecked(True)
                else:
                    self.ui.checkBox_download.setChecked(False)
                
            try:
                self.ui.lineEdit_user.setText(pr.find("Username").text)
                self.ui.lineEdit_password.setText(pr.find("Password").text)
            except:
                print('Not username or password Theia')
            
            self.f_proxy()
            try:
                pp = pr.find("Proxy[@id='Proxy']")
                self.w_proxy.w_proxy.lineEdit_proxy.setText(pp.find("Proxy_adress").text)
                try:
                    self.w_proxy.w_proxy.lineEdit_password_proxy.setText(pp.find("Proxy_login").text)
                except TypeError:
                    pass
                try:
                    self.w_proxy.w_proxy.lineEdit_login_proxy.setText(pp.find("Proxy_password").text)
                except TypeError:
                    pass
                self.w_proxy.id_proxy()
            except AttributeError:
                print('Not proxy')
            self.w_proxy.close_window()
                
            if self.mode == 1:
                if pr.find("Img_processing").text == '1':
                    self.ui.checkBox_processing.setChecked(True)
                else:
                    self.ui.checkBox_processing.setChecked(False)
                if pr.find("VHRS_checked").text == '1':
                    self.ui.checkBox_VHRS.setChecked(True)
                else:
                    self.ui.checkBox_VHRS.setChecked(False)    
                
            try:
                self.ui.lineEdit_VHRS.setText(pr.find("VHRS").text)
            except:
                print('Not VHRS image')
                
            if self.mode == 1:
                if pr.find("MNT_checked").text == '1':
                    self.ui.checkBox_MNT.setChecked(True)
                else:
                    self.ui.checkBox_MNT.setChecked(False)    
                
            try:
                self.ui.lineEdit_MNT.setText(pr.find("MNT").text)
            except:
                print('Not MNT')
                
            ps = tree.find("Tab[@id='Processing_sample']")  
            if self.mode == 1:
                try:
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
                                self.ui.lineEdit_img_sample.setText(sple_n.find("Img_sample").text)
                                self.ui.checkBox_img_sample.setChecked(True)
                        except:
                            print('Not sample raster only !')
                        self.add_sample()
                except:
                    print('Not sample')
            elif self.mode ==0:
                # RPG
                sple_n = ps[0]
                self.ui.lineEdit_sample_path.setText(sple_n.find("Sample_path").text)
                self.ui.lineEdit_select_sample_fieldname_1.setText(sple_n.find("Fieldname_1").text)
                self.ui.lineEdit_select_sample_fieldname_2.setText(sple_n.find("Fieldname_2").text)
                self.ui.lineEdit_select_sample_class_1.setText(sple_n.find("Classname_1").text)
                self.ui.lineEdit_select_sample_class_2.setText(sple_n.find("Classname_2").text)
                self.ui.lineEdit_select_sample_nb_poly.setText(sple_n.find("Nb_polygones").text)
                
                # To Grass/wooden
                sple_n = ps[1]
                self.ui.lineEdit_sample_path_2.setText(sple_n.find("Sample_path").text)
                self.ui.lineEdit_select_sample_fieldname_3.setText(sple_n.find("Fieldname_1").text)
                self.ui.lineEdit_select_sample_fieldname_4.setText(sple_n.find("Fieldname_2").text)
                self.ui.lineEdit_select_sample_class_3.setText(sple_n.find("Classname_1").text)
                self.ui.lineEdit_select_sample_class_4.setText(sple_n.find("Classname_2").text)
                self.ui.lineEdit_select_sample_nb_poly_2.setText(sple_n.find("Nb_polygones").text)        
                
                # To wooden
                sple_n = ps[2]
                self.ui.lineEdit_sample_path_3.setText(sple_n.find("Sample_path").text)
                self.ui.lineEdit_select_sample_fieldname_5.setText(sple_n.find("Fieldname_1").text)
                self.ui.lineEdit_select_sample_fieldname_6.setText(sple_n.find("Fieldname_2").text)
                self.ui.lineEdit_select_sample_class_5.setText(sple_n.find("Classname_1").text)
                self.ui.lineEdit_select_sample_class_6.setText(sple_n.find("Classname_2").text)
                self.ui.lineEdit_select_sample_nb_poly_3.setText(sple_n.find("Nb_polygones").text)
                    
            if self.mode == 1:
                if ps.find("Threshold_checked").text == '1':
                    self.ui.checkBox_threshold.setChecked(True)
                else:
                    self.ui.checkBox_threshold.setChecked(False) 
             
            c = tree.find("Tab[@id='Classification']")
            try:
                self.ui.lineEdit_segmentation.setText(c.find("Segmentation_path").text)
            except:
                print('Not segmentation')
            try:
                self.ui.lineEdit_output.setText(c.find("Output_path").text)
            except:
                print('Not output file')
            if self.mode == 1:
                if len(c) == 5:
                    self.ui.checkBox_classifier_1.setChecked(True)
                    self.ui.lineEdit_fieldname_1.setText(c.find("Output_fieldname_1").text)
                    index_fieldname_1 = self.ui.comboBox_fieldname_1.findText(c.find("Output_type_1").text)        
                    self.ui.comboBox_fieldname_1.setCurrentIndex(index_fieldname_1)
                elif len(c) == 7:
                    self.ui.checkBox_classifier_2.setChecked(True)
                    self.ui.lineEdit_fieldname_12.setText(c.find("Output_fieldname_1").text)
                    self.ui.lineEdit_fieldname_2.setText(c.find("Output_fieldname_2").text)
                    index_fieldname_12 = self.ui.comboBox_fieldname_12.findText(c.find("Output_type_1").text)        
                    self.ui.comboBox_fieldname_12.setCurrentIndex(index_fieldname_12)
                    index_fieldname_2 = self.ui.comboBox_fieldname_2.findText(c.find("Output_type_2").text)        
                    self.ui.comboBox_fieldname_2.setCurrentIndex(index_fieldname_2)
                elif len(c) == 11:
                    self.ui.checkBox_classifier_3.setChecked(True)
                    self.ui.lineEdit_fieldname_13.setText(c.find("Output_fieldname_1").text)
                    self.ui.lineEdit_fieldname_23.setText(c.find("Output_fieldname_2").text)
                    self.ui.lineEdit_fieldname_3.setText(c.find("Output_fieldname_3").text)
                    self.ui.lineEdit_fieldname_4.setText(c.find("Output_fieldname_4").text)
                    index_fieldname_13 = self.ui.comboBox_fieldname_13.findText(c.find("Output_type_1").text)        
                    self.ui.comboBox_fieldname_13.setCurrentIndex(index_fieldname_13)
                    index_fieldname_23 = self.ui.comboBox_fieldname_23.findText(c.find("Output_type_2").text)        
                    self.ui.comboBox_fieldname_23.setCurrentIndex(index_fieldname_23)
                    index_fieldname_3 = self.ui.comboBox_fieldname_3.findText(c.find("Output_type_3").text)        
                    self.ui.comboBox_fieldname_3.setCurrentIndex(index_fieldname_3)
                    index_fieldname_4 = self.ui.comboBox_fieldname_4.findText(c.find("Output_type_4").text)        
                    self.ui.comboBox_fieldname_4.setCurrentIndex(index_fieldname_4)
                
                # Classification mode
                if c.find("Classification_method").text == '1':
                    self.ui.radioButton_rf.setChecked(True)
                else:
                    self.ui.radioButton_s.setChecked(True)
                
            print("Load input text !")
        
    def save_backup(self):
        """
        Function to save input text in every fields. The output file must be a XML file.
        """
        
        out_backup = QFileDialog.getSaveFileName(self, "Save backup", os.getcwd(), '*.xml')
        # if the user has forgotten to put .shp at the end of the output xml
        if out_backup[-4:] != '.xml':
            out_backup = out_backup + '.xml'
        
        root = ET.Element("Data_filled")
        
        if self.ui.checkBox_multiprocess.isChecked():
            ET.SubElement(root, "Multi_process", type = "int").text = str(1)
        else:
            ET.SubElement(root, "Multi_process", type = "int").text = str(0)
        
        doc = ET.SubElement(root, "Tab", id="Processing_raster")
        ET.SubElement(doc, "Principal_folder", type = "str").text = "%s" % self.ui.lineEdit_principal_folder.text()
        if self.mode == 1:
            ET.SubElement(doc, "Captor", type = "str").text = "%s" % self.ui.comboBox_captor.currentText()
        else:
            ET.SubElement(doc, "Captor", type = "str").text = "Landsat"
        ET.SubElement(doc, "Year_images", type = "str").text = "%s" % self.ui.lineEdit_year_images.text()
        ET.SubElement(doc, "Area_path", type = "str").text = "%s" % self.ui.lineEdit_area_path.text()
        
        if self.mode == 1:
            if self.ui.checkBox_listing.isChecked():
                ET.SubElement(doc, "Images_available", type = "int").text = str(1)
            else:
                ET.SubElement(doc, "Images_available", type = "int").text = str(0)
            if self.ui.checkBox_download.isChecked():
                ET.SubElement(doc, "Download", type = "int").text = str(1)
            else:
                ET.SubElement(doc, "Download", type = "int").text = str(0)
        else:
            ET.SubElement(doc, "Images_available", type = "int").text = str(0)
            ET.SubElement(doc, "Download", type = "int").text = str(0)
            
        ET.SubElement(doc, "Username", type = "str").text = "%s" % self.ui.lineEdit_user.text()
        ET.SubElement(doc, "Password", type = "str").text = "%s" % self.ui.lineEdit_password.text()
        if self.w_proxy is None:
            sub_proxy = ET.SubElement(doc, "Proxy", id="No_proxy")
            ET.SubElement(sub_proxy, "Proxy_adress", type = "str").text = ""
            ET.SubElement(sub_proxy, "Proxy_login", type = "str").text = ""
            ET.SubElement(sub_proxy, "Proxy_password", type = "str").text = ""
        elif self.w_proxy.proxy == "":
            sub_proxy = ET.SubElement(doc, "Proxy", id="No_proxy")
            ET.SubElement(sub_proxy, "Proxy_adress", type = "str").text = ""
            ET.SubElement(sub_proxy, "Proxy_login", type = "str").text = ""
            ET.SubElement(sub_proxy, "Proxy_password", type = "str").text = ""
        else:
            sub_proxy = ET.SubElement(doc, "Proxy", id="Proxy")
            ET.SubElement(sub_proxy, "Proxy_adress", type = "str").text = "%s" % self.w_proxy.proxy
            ET.SubElement(sub_proxy, "Proxy_login", type = "str").text = "%s" % self.w_proxy.login_proxy
            ET.SubElement(sub_proxy, "Proxy_password", type = "str").text = "%s" % self.w_proxy.password_proxy
        
        if self.mode == 1:
            if self.ui.checkBox_processing.isChecked():
                ET.SubElement(doc, "Img_processing", type = "int").text = str(1)
            else:
                ET.SubElement(doc, "Img_processing", type = "int").text = str(0)
            
            if self.ui.checkBox_VHRS.isChecked():
                ET.SubElement(doc, "VHRS_checked", type = "int").text = str(1)
            else:
                ET.SubElement(doc, "VHRS_checked", type = "int").text = str(0)
        else:
            ET.SubElement(doc, "Img_processing", type = "int").text = str(1)
            ET.SubElement(doc, "VHRS_checked", type = "int").text = str(1)
            
        ET.SubElement(doc, "VHRS", type = "str").text = "%s" % self.ui.lineEdit_VHRS.text()
        
        if self.mode == 1:
            if self.ui.checkBox_MNT.isChecked():
                ET.SubElement(doc, "MNT_checked", type = "int").text = str(1)
            else:
                ET.SubElement(doc, "MNT_checked", type = "int").text = str(0)
        else:
            if "%s" % self.ui.lineEdit_MNT.text() != '':
                ET.SubElement(doc, "MNT_checked", type = "int").text = str(1)
            else:
                ET.SubElement(doc, "MNT_checked", type = "int").text = str(0)
            
        ET.SubElement(doc, "MNT", type = "str").text = "%s" % self.ui.lineEdit_MNT.text()
        
        doc = ET.SubElement(root, "Tab", id="Processing_sample")
        if self.mode == 1:
            for sa in range(len(self.sample_name)):
                sub_doc = ET.SubElement(doc, "Sample", id="Sample_" + str(sa))
                ET.SubElement(sub_doc, "Sample_path", type = "str").text = self.sample_name[sa]
                ET.SubElement(sub_doc, "Fieldname_1", type = "str").text = self.fieldname_args[2*sa]
                ET.SubElement(sub_doc, "Fieldname_2", type = "str").text = self.fieldname_args[2*sa+1]
                ET.SubElement(sub_doc, "Classname_1", type = "str").text = self.class_args[2*sa]
                ET.SubElement(sub_doc, "Classname_2", type = "str").text = self.class_args[2*sa+1]
                ET.SubElement(sub_doc, "Nb_polygones", type = "str").text = self.list_nb_sample[sa]
                ET.SubElement(sub_doc, "RPG", type = "int").text = str(self.rpg_tchek[sa])
                try:
                    # To enter a sample raster if the first tab doesn't launch before 
                    if self.img_sample[sa] == 1:
                        ET.SubElement(sub_doc, "Img_sample", type = "str").text = self.raster_path[sa]
                except:
                    print('Not sample raster only !')   
        else:
            # RPG
            sub_doc = ET.SubElement(doc, "Sample", id="Sample_0")
            ET.SubElement(sub_doc, "Sample_path", type = "str").text = "%s" % self.ui.lineEdit_sample_path.text()
            ET.SubElement(sub_doc, "Fieldname_1", type = "str").text = "%s" % self.ui.lineEdit_select_sample_fieldname_1.text()
            ET.SubElement(sub_doc, "Fieldname_2", type = "str").text = "%s" % self.ui.lineEdit_select_sample_fieldname_2.text()
            ET.SubElement(sub_doc, "Classname_1", type = "str").text = "%s" % self.ui.lineEdit_select_sample_class_1.text()
            ET.SubElement(sub_doc, "Classname_2", type = "str").text = "%s" % self.ui.lineEdit_select_sample_class_2.text()
            ET.SubElement(sub_doc, "Nb_polygones", type = "str").text = "%s" % self.ui.lineEdit_select_sample_nb_poly.text()
            ET.SubElement(sub_doc, "RPG", type = "int").text = str(1)
            
            # To Grass/wooden
            sub_doc = ET.SubElement(doc, "Sample", id="Sample_1")
            ET.SubElement(sub_doc, "Sample_path", type = "str").text = "%s" % self.ui.lineEdit_sample_path_2.text()
            ET.SubElement(sub_doc, "Fieldname_1", type = "str").text = "%s" % self.ui.lineEdit_select_sample_fieldname_3.text()
            ET.SubElement(sub_doc, "Fieldname_2", type = "str").text = "%s" % self.ui.lineEdit_select_sample_fieldname_4.text()
            ET.SubElement(sub_doc, "Classname_1", type = "str").text = "%s" % self.ui.lineEdit_select_sample_class_3.text()
            ET.SubElement(sub_doc, "Classname_2", type = "str").text = "%s" % self.ui.lineEdit_select_sample_class_4.text()
            ET.SubElement(sub_doc, "Nb_polygones", type = "str").text = "%s" % self.ui.lineEdit_select_sample_nb_poly_2.text()
            ET.SubElement(sub_doc, "RPG", type = "int").text = str(0)
            
            # To wooden  
            sub_doc = ET.SubElement(doc, "Sample", id="Sample_2")
            ET.SubElement(sub_doc, "Sample_path", type = "str").text = "%s" % self.ui.lineEdit_sample_path_3.text()
            ET.SubElement(sub_doc, "Fieldname_1", type = "str").text = "%s" % self.ui.lineEdit_select_sample_fieldname_5.text()
            ET.SubElement(sub_doc, "Fieldname_2", type = "str").text = "%s" % self.ui.lineEdit_select_sample_fieldname_6.text()
            ET.SubElement(sub_doc, "Classname_1", type = "str").text = "%s" % self.ui.lineEdit_select_sample_class_5.text()
            ET.SubElement(sub_doc, "Classname_2", type = "str").text = "%s" % self.ui.lineEdit_select_sample_class_6.text()
            ET.SubElement(sub_doc, "Nb_polygones", type = "str").text = "%s" % self.ui.lineEdit_select_sample_nb_poly_3.text()
            ET.SubElement(sub_doc, "RPG", type = "int").text = str(0) 
        
        if self.mode == 1:
            if self.ui.checkBox_threshold.isChecked():
                ET.SubElement(doc, "Threshold_checked", type = "int").text = str(1)
            else:
                ET.SubElement(doc, "Threshold_checked", type = "int").text = str(0)
        else:
            ET.SubElement(doc, "Threshold_checked", type = "int").text = str(1)
            
        doc = ET.SubElement(root, "Tab", id="Classification")
        ET.SubElement(doc, "Segmentation_path", type = "str").text = "%s" % self.ui.lineEdit_segmentation.text()
        ET.SubElement(doc, "Output_path", type = "str").text = "%s" % self.ui.lineEdit_output.text()
        
        if self.mode == 1:
                
            if self.ui.checkBox_classifier_1.isChecked():
                ET.SubElement(doc, "Output_fieldname_1", type = "str").text = "%s" % self.ui.lineEdit_fieldname_1.text()
                ET.SubElement(doc, "Output_type_1", type = "str").text = "%s" % self.ui.comboBox_fieldname_1.currentText()
             
            if self.ui.checkBox_classifier_2.isChecked():
                ET.SubElement(doc, "Output_fieldname_1", type = "str").text = "%s" % self.ui.lineEdit_fieldname_12.text()
                ET.SubElement(doc, "Output_type_1", type = "str").text = "%s" % self.ui.comboBox_fieldname_12.currentText()    
                ET.SubElement(doc, "Output_fieldname_2", type = "str").text = "%s" % self.ui.lineEdit_fieldname_2.text()
                ET.SubElement(doc, "Output_type_2", type = "str").text = "%s" % self.ui.comboBox_fieldname_2.currentText()
            
            if self.ui.checkBox_classifier_3.isChecked():
                ET.SubElement(doc, "Output_fieldname_1", type = "str").text = "%s" % self.ui.lineEdit_fieldname_13.text()
                ET.SubElement(doc, "Output_type_1", type = "str").text = "%s" % self.ui.comboBox_fieldname_13.currentText()    
                ET.SubElement(doc, "Output_fieldname_2", type = "str").text = "%s" % self.ui.lineEdit_fieldname_23.text()
                ET.SubElement(doc, "Output_type_2", type = "str").text = "%s" % self.ui.comboBox_fieldname_23.currentText()
                ET.SubElement(doc, "Output_fieldname_3", type = "str").text = "%s" % self.ui.lineEdit_fieldname_3.text()
                ET.SubElement(doc, "Output_type_3", type = "str").text = "%s" % self.ui.comboBox_fieldname_3.currentText()
                ET.SubElement(doc, "Output_fieldname_4", type = "str").text = "%s" % self.ui.lineEdit_fieldname_4.text()
                ET.SubElement(doc, "Output_type_4", type = "str").text = "%s" % self.ui.comboBox_fieldname_4.currentText()
            
            # Classification mode
            if self.ui.radioButton_rf.isChecked():
                ET.SubElement(doc, "Classification_method", type = "int").text = str(1)
            elif self.ui.radioButton_s.isChecked():
                ET.SubElement(doc, "Classification_method", type = "int").text = str(0)
        else:
            ET.SubElement(doc, "Output_fieldname_1", type = "str").text = "NIVEAU_1"
            ET.SubElement(doc, "Output_type_1", type = "str").text = "String"   
            ET.SubElement(doc, "Output_fieldname_2", type = "str").text = "NIVEAU_2"
            ET.SubElement(doc, "Output_type_2", type = "str").text = "String"
            ET.SubElement(doc, "Output_fieldname_3", type = "str").text = "NIVEAU_3"
            ET.SubElement(doc, "Output_type_3", type = "str").text = "String"
            ET.SubElement(doc, "Output_fieldname_4", type = "str").text = "POURC"
            ET.SubElement(doc, "Output_type_4", type = "str").text = "Real"
            ET.SubElement(doc, "Classification_method", type = "int").text = str(1)
            
        tree = ET.ElementTree(root)
        # Write in a xml file
        tree.write(str(out_backup), encoding="UTF-8",xml_declaration=True, pretty_print=True)
        if out_backup != '.xml':
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

        webbrowser.open('file://' + os.getcwd() + '/Documentation/methode_tuto.html#tutoriels-interface')
    
    def mode_simpli(self):
        """
        Function to open a new window in simple mode "PHYMOBATs"
        """
        if self.simpli is None:
            print "Simplify mode"
            self.close()
            self.simpli = PHYMOBAT(mode = 0)
            
        self.simpli.show()
    
    def mode_expert(self):
        """
        Function to open a new window in expert mode "PHYMOBATe"
        """
        if self.expert is None:
            print "Expert mode"
            self.close()
            self.expert = PHYMOBAT(mode = 1)
            
        self.expert.show()
        
    def forget_study_area(self):
        """
        Function to open a new window 'Alert' because user forgotten to declare study area.
        """
        if self.w_study_area is None:
            self.w_study_area = MyPopup_warming_study_area()
        self.w_study_area.show()
        
    def forget_raster_sample(self):
        """
        Function to open a new window 'Alert' because user forgotten to declare rasters or samples.
        """
        if self.w_forget is None:
            self.w_forget = MyPopup_warming_forgetting()
        self.w_forget.show()
                
    def close_button(self):
        """
        Function to close the interface.
        """
        self.close()

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
        
class MyPopup_warming_forgetting(QWidget):
    """
    Popup to display a message to tell you if you fogotten to enter a raster or a sample.
    """
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.w_forget = Ui_Warming_forgetting()
        self.w_forget.setupUi(self)
        
        self.connect(self.w_forget.pushButton_ok_forget, SIGNAL('clicked()'), self.close_window)
    
    def close_window(self):
        """
        Function to close the popup.
        """
        self.close() 
        
class MyPopup_proxy_window(QWidget):
    """
    Popup to display a message to tell you if you fogotten to enter a raster or a sample.
    """
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.w_proxy = Ui_Proxy_window()
        self.w_proxy.setupUi(self)
        
        # Proxy ID
        self.proxy = ""
        self.login_proxy = ""
        self.password_proxy = ""
        
        # Connect Apply|Close button
        self.w_proxy.buttonBox_proxy.button(QDialogButtonBox.Close).clicked.connect(self.close_window)
        self.w_proxy.buttonBox_proxy.button(QDialogButtonBox.Apply).clicked.connect(self.id_proxy)
    
    def id_proxy(self):
        """
        Function to use input proxy id
        """
        self.login_proxy = "%s" % self.w_proxy.lineEdit_login_proxy.text()
        self.password_proxy = "%s" % self.w_proxy.lineEdit_password_proxy.text()
        self.proxy = "%s" % self.w_proxy.lineEdit_proxy.text()
    
    def close_window(self):
        """
        Function to close the popup.
        """
        self.close()
        
if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    myapp = PHYMOBAT()
    myapp.show()
        
    sys.exit(app.exec_())
