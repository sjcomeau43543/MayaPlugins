import maya.cmds as cmds

import maya.OpenMayaUI as mui
from PySide2 import QtCore, QtGui, QtWidgets
import shiboken2

def getMayaWindow():
    ptr = mui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget)

class BasicDialog(QtWidgets.QDialog):
    def __init__(self, parent=getMayaWindow()):
        super(BasicDialog, self).__init__(parent)
        self.setWindowTitle('blah')
        self.shapeTypeCB = QtGui.QComboBox(parent=self)
        self.nameLE = QtGui.QLineEdit('newShape', parent=self)
        self.makeButton = QtGui.QPushButton("Make Shape", parent=self)
        self.descLabel = QtGui.QLabel("This is a description", parent=self)

BasicDialog().show()

