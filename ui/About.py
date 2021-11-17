# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'About.ui'
#
# Created: Sun Mar 24 18:20:51 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(260, 380)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QtCore.QSize(260, 380))
        Dialog.setMaximumSize(QtCore.QSize(260, 380))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/img/EBPatcher_Icon.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        Dialog.setStyleSheet(_fromUtf8("* {\n"
"    color: rgb(34, 0, 52);\n"
"    font-family: Arial;\n"
"}"))
        self.Logo = QtWidgets.QFrame(Dialog)
        self.Logo.setGeometry(QtCore.QRect(-10, 5, 280, 150))
        self.Logo.setStyleSheet(_fromUtf8("QFrame#Logo {\n"
"    background-image: url(:/img/EBPatcher_Icon.png);\n"
"    background-position: center;\n"
"    background-repeat: no-repeat;\n"
"}"))
        self.Logo.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.Logo.setFrameShadow(QtWidgets.QFrame.Plain)
        self.Logo.setObjectName(_fromUtf8("Logo"))
        self.CloseButton = QtWidgets.QPushButton(Dialog)
        self.CloseButton.setGeometry(QtCore.QRect(80, 340, 100, 30))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Arial"))
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.CloseButton.setFont(font)
        self.CloseButton.setObjectName(_fromUtf8("CloseButton"))
        self.About = QtWidgets.QLabel(Dialog)
        self.About.setGeometry(QtCore.QRect(10, 170, 240, 91))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Arial"))
        font.setPointSize(10)
        self.About.setFont(font)
        self.About.setStyleSheet(_fromUtf8(""))
        self.About.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.About.setAlignment(QtCore.Qt.AlignCenter)
        self.About.setOpenExternalLinks(True)
        self.About.setObjectName(_fromUtf8("About"))
        self.GetMore = QtWidgets.QPushButton(Dialog)
        self.GetMore.setGeometry(QtCore.QRect(50, 280, 160, 30))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Arial"))
        font.setPointSize(10)
        font.setBold(False)
        font.setUnderline(True)
        font.setWeight(50)
        self.GetMore.setFont(font)
        self.GetMore.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.GetMore.setStyleSheet(_fromUtf8("QPushButton#GetMore {\n"
"    color: rgb(65, 65, 65);\n"
"}"))
        self.GetMore.setObjectName(_fromUtf8("GetMore"))

        self.retranslateUi(Dialog)
#        QtCore.QObject.connect(self.CloseButton, QtCore.SIGNAL(_fromUtf8("clicked()")), Dialog.close)
        self.CloseButton.clicked.connect(Dialog.close)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtWidgets.QApplication.translate("Dialog", "About", None))
        self.CloseButton.setText(QtWidgets.QApplication.translate("Dialog", "Close", None))
        self.About.setText(QtWidgets.QApplication.translate("Dialog", "<html><head/><body><p><span style=\" font-size:12pt; font-weight:600;\">EarthBound Patcher</span></p><p><span style=\" font-style:italic;\">Created by Lyrositor.</span></p><p><a href=\"https://github.com/Lyrositor/EBPatcher\"><span style=\" text-decoration: underline; color:#4b4b4b;\">https://github.com/Lyrositor/EBPatcher</span></a></p></body></html>", None))
        self.GetMore.setText(QtWidgets.QApplication.translate("Dialog", "Get more patches online", None))

import res_rc
