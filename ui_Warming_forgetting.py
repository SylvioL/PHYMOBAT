# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Warming_forgetting.ui'
#
# Created: Mon Jan 25 11:56:42 2016
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!
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

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Warming_forgetting(object):
    """
    Class to display a message to tell you if you fogotten to enter a raster or a sample.
    """
    
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(332, 102)
        self.gridLayout = QtGui.QGridLayout(Form)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label_forget = QtGui.QLabel(Form)
        self.label_forget.setObjectName(_fromUtf8("label_forget"))
        self.gridLayout.addWidget(self.label_forget, 0, 0, 1, 3)
        spacerItem = QtGui.QSpacerItem(93, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        self.pushButton_ok_forget = QtGui.QPushButton(Form)
        self.pushButton_ok_forget.setObjectName(_fromUtf8("pushButton_ok_forget"))
        self.gridLayout.addWidget(self.pushButton_ok_forget, 1, 1, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(104, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 1, 2, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Warming : Forgetting !", None))
        self.label_forget.setText(_translate("Form", "Vous avez coché une case pour lancer la classification.\n"
"\n"                                             
"Mais vous avez oublié de sélectionner l\'(es) image(s)\n"
"ou d\'entrer un(des) échantillon(s). Si l\'oubli n\'est pas\n"
"dans cette onglet, parcourer les autres onglets.", None))
        self.pushButton_ok_forget.setText(_translate("Form", "Ok", None))

