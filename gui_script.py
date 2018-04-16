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
        self.setWindowTitle('Maya PyQt Basic Dialog Demo')
        self.shapeTypeCB = QtWidgets.QComboBox(parent=self)
        self.nameLE = QtWidgets.QLineEdit('newShape', parent=self)
        self.makeButton = QtWidgets.QPushButton("Make Shape", parent=self)
        self.descLabel = QtWidgets.QLabel("This is a description", parent=self)
        
        self.shapeTypeCB.addItems(['Sphere', 'Cube', 'Cylinder'])
        
        self.connect(self.shapeTypeCB, QtCore.SIGNAL("currentIndexChanged(int)"), self.updateDescription)
        self.connect(self.nameLE, QtCore.SIGNAL("textChanged(const QString&)"), self.updateDescription)
        self.connect(self.makeButton, QtCore.SIGNAL("clicked()"), self.makeShape)
        
        actionLayout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight)
        actionLayout.addWidget(self.shapeTypeCB)
        actionLayout.addWidget(self.nameLE)
        actionLayout.addWidget(self.makeButton)
        
        self.updateDescription()

        self.layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.TopToBottom, self)
        self.layout.addLayout(actionLayout)
        self.layout.addWidget(self.descLabel)
    
    def updateDescription(self):
        description = 'Make a %s named "%s"' % (self.shapeTypeCB.currentText(), self.nameLE.text())
        self.descLabel.setText(description)
        
    def makeShape(self):
        objType = self.shapeTypeCB.currentText()

        if objType == 'Sphere':
            cmd = cmds.polySphere
        elif objType == 'Cube':
            cmd = cmds.polyCube
        else:
            cmd = cmds.polyCylinder

        cmd(name=str(self.nameLE.text()))

BasicDialog().show()

