# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Proxy_window.ui'
#
# Created: Thu Mar  9 14:54:35 2017
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

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

class Ui_Proxy_window(object):
    
    """
    Class to display “Proxy window”. In this windows, there is 3 lines edit to fill (proxy server, login and password).
    """
    
    def setupUi(self, Proxy_window):
        Proxy_window.setObjectName(_fromUtf8("Proxy_window"))
        Proxy_window.resize(344, 144)
        Proxy_window.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.gridLayout = QtGui.QGridLayout(Proxy_window)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label_proxy = QtGui.QLabel(Proxy_window)
        self.label_proxy.setObjectName(_fromUtf8("label_proxy"))
        self.gridLayout.addWidget(self.label_proxy, 0, 0, 1, 1)
        self.lineEdit_proxy = QtGui.QLineEdit(Proxy_window)
        self.lineEdit_proxy.setInputMask(_fromUtf8(""))
        self.lineEdit_proxy.setText(_fromUtf8(""))
        self.lineEdit_proxy.setFrame(True)
        self.lineEdit_proxy.setObjectName(_fromUtf8("lineEdit_proxy"))
        self.gridLayout.addWidget(self.lineEdit_proxy, 0, 2, 1, 1)
        self.label_login_proxy = QtGui.QLabel(Proxy_window)
        self.label_login_proxy.setObjectName(_fromUtf8("label_login_proxy"))
        self.gridLayout.addWidget(self.label_login_proxy, 1, 0, 1, 2)
        self.lineEdit_login_proxy = QtGui.QLineEdit(Proxy_window)
        self.lineEdit_login_proxy.setObjectName(_fromUtf8("lineEdit_login_proxy"))
        self.gridLayout.addWidget(self.lineEdit_login_proxy, 1, 2, 1, 1)
        self.label_password_proxy = QtGui.QLabel(Proxy_window)
        self.label_password_proxy.setObjectName(_fromUtf8("label_password_proxy"))
        self.gridLayout.addWidget(self.label_password_proxy, 2, 0, 1, 2)
        self.lineEdit_password_proxy = QtGui.QLineEdit(Proxy_window)
        self.lineEdit_password_proxy.setObjectName(_fromUtf8("lineEdit_password_proxy"))
        self.gridLayout.addWidget(self.lineEdit_password_proxy, 2, 2, 1, 1)
        self.buttonBox_proxy = QtGui.QDialogButtonBox(Proxy_window)
        self.buttonBox_proxy.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Close)
        self.buttonBox_proxy.setCenterButtons(False)
        self.buttonBox_proxy.setObjectName(_fromUtf8("buttonBox_proxy"))
        self.gridLayout.addWidget(self.buttonBox_proxy, 3, 1, 1, 2)

        self.retranslateUi(Proxy_window)
        QtCore.QMetaObject.connectSlotsByName(Proxy_window)

    def retranslateUi(self, Proxy_window):
        Proxy_window.setWindowTitle(_translate("Proxy_window", "Proxy", None))
        self.label_proxy.setText(_translate("Proxy_window", "Proxy :", None))
        self.lineEdit_proxy.setPlaceholderText(_translate("Proxy_window", "http://proxy.truc.fr:8050", None))
        self.label_login_proxy.setText(_translate("Proxy_window", "Login :", None))
        self.label_password_proxy.setText(_translate("Proxy_window", "Password :", None))

