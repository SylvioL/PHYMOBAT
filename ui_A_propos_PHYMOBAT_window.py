# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'A_propos_PHYMOBAT_window.ui'
#
# Created: Tue Jan 19 15:19:31 2016
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!
#
# This file is part of PHYMOBAT 1.1.
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

class Ui_About(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("A propos de PHYMOBAT"))
        Form.resize(507, 578)
        self.gridLayout = QtGui.QGridLayout(Form)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(Form)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 3)
        spacerItem = QtGui.QSpacerItem(193, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        self.close_newWindow = QtGui.QPushButton(Form)
        self.close_newWindow.setObjectName(_fromUtf8("close_newWindow"))
        self.gridLayout.addWidget(self.close_newWindow, 1, 1, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(193, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 1, 2, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.label.setText(_translate("Form", "              A propos de PHYMOBAT\n"
"              -------------------------------------\n"
"\n"
"L\'interface utilisateur PHYMOBAT (FB PHYsionomique des Milieux Ouverts \n"
"de Basse Altitude par Télédétection)\n"
"\n"
"Cet outil répond à un objectif du programme CarHab (Cartographie des \n"
"Habitats naturels) à savoir : réaliser pour les milieux ouverts de basse \n"
"altitude (MOBA) un “fond blanc physionomique”, c’est-à-dire d’une carte \n"
"physionomique de ces milieux à l’aide des techniques de télédétection.\n"
"\n"
"__name__ = \"PHYMOBAT 1.1\"\n"
"__version__ = \"1.1\"\n"
"__author__ = \"LAVENTURE Sylvio - UMR TETIS / IRSTEA\"\n"
"__date__ = \"Janvier 2016\"\n"
"__license__ = \"GPL\"\n"
"\n"
"Copyright 2016 Sylvio Laventure (IRSTEA - UMR TETIS)\n"
"\n"
"PHYMOBAT 1.1 is free software: you can redistribute it and/or modify\n"
"it under the terms of the GNU General Public License as published by\n"
"the Free Software Foundation, either version 3 of the License, or\n"
"(at your option) any later version.\n"
" \n"
"PHYMOBAT 1.1 is distributed in the hope that it will be useful,\n"
"but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
"MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n"
"GNU General Public License for more details.\n"
"\n"
"You should have received a copy of the GNU General Public License\n"
"along with PHYMOBAT 1.1.  If not, see <http://www.gnu.org/licenses/>.", None))
        self.close_newWindow.setText(_translate("Form", "Fermer", None))

