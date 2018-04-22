# Imports
import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.cmds as cmds
import maya.OpenMayaUI as mui
from PySide2 import QtCore, QtGui, QtWidgets
import PySide2 as pys2
import shiboken2

# Global variables
nodeName = "CVGKNode"
nodeId = OpenMaya.MTypeId(0x100fff)

ikhandles = ['LeftArmShoulder', 'LeftArmElbow', 'LeftArmHand', 'LeftArmFinger1', 'Thesearejustexamples']
selectedIK = []

# get a UI window to put our data in
def getMayaWindow():
    ptr = mui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget)

# Contentes of the popup
class BasicDialog(QtWidgets.QDialog):
    def __init__(self, parent=getMayaWindow()):
        cmds.GetIKHandles()
        cmds.createNode("CVGKNode")

        super(BasicDialog, self).__init__(parent)
        self.setWindowTitle('Maya PyQt Basic Dialog Demo')

        self.makeUI()
        self.show()

    def makeUI(self):
        layout = QtWidgets.QVBoxLayout()

        # add the update ik handles button
        updateBtn = QtWidgets.QPushButton('Update List', parent=self)
        updateBtn.clicked.connect(self.updateList)
        layout.addWidget(updateBtn)

        # Add all the ikhandles that were loaded
        for i in range(len(ikhandles)):
            print ikhandles[i]

            newcheckbox = QtWidgets.QCheckBox(ikhandles[i], parent=self)
            newcheckbox.setObjectName(ikhandles[i])
            newcheckbox.stateChanged.connect(self.submitToList)
            layout.addStretch()
            layout.addWidget(newcheckbox)

        self.setLayout(layout)

    def updateList(self):
        cmds.GetIKHandles()
        self.makeUI()
        self.show()

    def submitToList(self):
        print('----------------------------------------------------')
        print('submit to list')

        checkbox = self.sender()
        print(dir(checkbox))

        selectedIK.append(checkbox)
        print(selectedIK)
        print('----------------------------------------------------')


#Getes all the IK Handles in the scene
class GetIKHandles(OpenMayaMPx.MPxCommand):

	activeEffector = OpenMaya.MObject()
	activeHandle = OpenMaya.MObject()

	def __init__(self):
		OpenMayaMPx.MPxCommand.__init__(self)

	def doIt(self,*args):
	    ikhandles = []

	    print "Getting IK Handles"

        d = OpenMaya.MItDependencyNodes()
        mFnDependencyNode = OpenMaya.MFnDependencyNode()
        while(not d.isDone()):
            mObj = d.thisNode()
            if mObj.apiTypeStr() == 'kIkHandle':
                m = OpenMaya.MFnDependencyNode(mObj)
                print m.name()
                ikhandles.append(m.name())
                print ikhandles

            d.next()

#IK-FK Blend
class CVG(OpenMayaMPx.MPxNode):
	idCallback = []
	joint1 = OpenMaya.MObject()
	joint2 = OpenMaya.MObject()
	joint3 = OpenMaya.MObject()

	activeEffector = OpenMaya.MObject()
	activeHandle = OpenMaya.MObject()
	activePoleVector = OpenMaya.MObject()
	activePoleVectorControl = OpenMaya.MObject()

	def __init__(self):
		OpenMayaMPx.MPxNode.__init__(self)
		# Callbacks
		self.idCallback.append(OpenMaya.MEventMessage.addEventCallback("SelectionChanged",self.callbackFunc))
		self.idCallback.append(OpenMaya.MDGMessage.addNodeRemovedCallback(self.remove,"dependNode"))

	def callbackFunc(self,*args):
	    # Gets active selection in the scene
	    mSel = OpenMaya.MSelectionList()
	    OpenMaya.MGlobal.getActiveSelectionList(mSel)
	    mItSelectionList = OpenMaya.MItSelectionList(mSel,OpenMaya.MFn.kDagNode)
	    mode = "fk"

	    mFnDependencyNode = OpenMaya.MFnDependencyNode()

	    # Find IK effector
	    while(not mItSelectionList.isDone()):
	        mObj = OpenMaya.MObject()
	        mItSelectionList.getDependNode(mObj)
	        # If effector was selected, make mode ik
	        if mObj.apiTypeStr() == "kIkEffector":
	            self.activeEffector = mObj
	            mode = "ik"
	            break
	        # If control curve was selected, also make mode ik
	        if self.activePoleVectorControl.apiTypeStr() != "kInvalid":
	            if OpenMaya.MFnDependencyNode(mObj).name() == OpenMaya.MFnDependencyNode(self.activePoleVectorControl).name():
	                mode = "ik"
	                break
	        mFnDependencyNode.setObject(mObj)
	        mPlugArray_joint = OpenMaya.MPlugArray()
	        mFnDependencyNode.getConnections(mPlugArray_joint)
	        # If effector is connected to what was selected, make mode ik
	        for i in xrange(mPlugArray_joint.length()):
	            mPlug_joint = mPlugArray_joint[i]
	            mPlugArray2 = OpenMaya.MPlugArray()
	            mPlug_joint.connectedTo(mPlugArray2,True,True)
	            mPlug2 = mPlugArray2[0]
	            if mPlug2.node().apiTypeStr() == "kIkEffector":
	                self.activeEffector = mPlug2.node()
	                mode = "ik"
	                break

	            mItSelectionList.next()

	        # Find IK Handle
	        if self.activeEffector.apiTypeStr() == "kIkEffector":
	            mFnDependencyNode.setObject(self.activeEffector)
	            mPlugArray_effector = OpenMaya.MPlugArray()
	            mFnDependencyNode.getConnections(mPlugArray_effector)
	            for i in xrange(mPlugArray_effector.length()):
	                mPlug_effector = mPlugArray_effector[i]
	                mPlugArray2 = OpenMaya.MPlugArray()
	                mPlug_effector.connectedTo(mPlugArray2,True,True)
	                mPlug2 = mPlugArray2[0]
	                if mPlug2.node().apiTypeStr() == "kIkHandle":
	                    self.activeHandle = mPlug2.node()

	                    break

	            # If IK handle was found, find ik blend plug to make it unkeyable and hidden
	            if self.activeHandle.apiTypeStr() == "kIkHandle":
	                mFnDependNodeHandle = OpenMaya.MFnDependencyNode(self.activeHandle)
	                mPlug_blendAttr = mFnDependNodeHandle.findPlug("ikBlend")
	                mAttr_blendAttr = mPlug_blendAttr.attribute()
	                mMFnAttribute = OpenMaya.MFnAttribute(mAttr_blendAttr)
	                mMFnAttribute.setKeyable(0)
	                mMFnAttribute.setChannelBox(0)

	                # Find Pole Vector Constraint
	                mFnDependencyNode.setObject(self.activeHandle)
	                mPlugArray_handle = OpenMaya.MPlugArray()
	                mFnDependencyNode.getConnections(mPlugArray_handle)
	                for i in xrange(mPlugArray_handle.length()):
	                    mPlug_handle = mPlugArray_handle[i]
	                    mPlugArray2 = OpenMaya.MPlugArray()
	                    mPlug_handle.connectedTo(mPlugArray2,True,True)
	                    mPlug2 = mPlugArray2[0]
	                    if mPlug2.node().apiTypeStr() == "kPoleVectorConstraint":
	                        self.activePoleVector = mPlug2.node()
	                        break


	                ''' If IK-PoleVector is found then :
	                    - find IK-PoleVector Control Curve
	                '''
	                # If IK pole vector found, find the curve
	                if self.activePoleVector.apiTypeStr() == "kPoleVectorConstraint":
	                    mFnDependencyNode.setObject(self.activePoleVector)
	                    mPlugArray_handle = OpenMaya.MPlugArray()
	                    mFnDependencyNode.getConnections(mPlugArray_handle)
	                    for i in xrange(mPlugArray_handle.length()):
	                        mPlug_handle = mPlugArray_handle[i]
	                        mPlugArray2 = OpenMaya.MPlugArray()
	                        mPlug_handle.connectedTo(mPlugArray2,True,True)
	                        mPlug2 = mPlugArray2[0]
	                        if mPlug2.node().apiTypeStr() == "kTransform":
	                            self.activePoleVectorControl = mPlug2.node()
	                            break


	                    ''' If IK-PoleVector Control Curve is found then :
	                        - find middle joint of joint change, to which this control should be attached.
	                    '''
	                    # If the control curve is found, find middle joint of the chain
	                    if self.activePoleVectorControl.apiTypeStr() == "kTransform":
	                        mFnDependencyNode.setObject(self.activeEffector)
	                        mPlugArray_effector = OpenMaya.MPlugArray()
	                        mFnDependencyNode.getConnections(mPlugArray_effector)
	                        for i in xrange(mPlugArray_effector.length()):
	                            mPlug_effector = mPlugArray_effector[i]
	                            mPlugArray2 = OpenMaya.MPlugArray()
	                            mPlug_effector.connectedTo(mPlugArray2,True,True)
	                            mPlug2 = mPlugArray2[0]
	                            if mPlug2.node().apiTypeStr() == "kJoint":
	                                self.joint3 = mPlug2.node()
	                                break
	                        # Finds joint connected to IK Handle
	                        mFnDependencyNode.setObject(self.activeHandle)
	                        mPlugArray_handle = OpenMaya.MPlugArray()
	                        mFnDependencyNode.getConnections(mPlugArray_handle)
	                        for i in xrange(mPlugArray_handle.length()):
	                            mPlug_handle = mPlugArray_handle[i]
	                            mPlugArray2 = OpenMaya.MPlugArray()
	                            mPlug_handle.connectedTo(mPlugArray2,True,True)
	                            mPlug2 = mPlugArray2[0]
	                            if mPlug2.node().apiTypeStr() == "kJoint":
	                                self.joint1 = mPlug2.node()
	                                break

	                        # Find joint connected to Joint1 and Joint3
	                        mObj_joint1Connections = OpenMaya.MObjectArray()
	                        mObj_joint3Connections = OpenMaya.MObjectArray()

	                        # Collect child Joints connected to Joint1
	                        mFnDependencyNode.setObject(self.joint1)
	                        mPlugArray_joint1 = OpenMaya.MPlugArray()
	                        mPlug_joint1Scale = mFnDependencyNode.findPlug("scale")
	                        mPlugArray_joint1 = OpenMaya.MPlugArray()
	                        mPlug_joint1Scale.connectedTo(mPlugArray_joint1,True,True)
	                        for i in xrange(mPlugArray_joint1.length()):
	                            if mPlugArray_joint1[i].node().apiTypeStr() == "kJoint":
	                                mObj_joint1Connections.append(mPlugArray_joint1[i].node())

	                        # Collect parent Joints connected to Joint3
	                        mFnDependencyNode.setObject(self.joint3)
	                        mPlugArray_joint3 = OpenMaya.MPlugArray()
	                        mPlug_joint3Scale = mFnDependencyNode.findPlug("inverseScale")
	                        mPlugArray_joint3 = OpenMaya.MPlugArray()
	                        mPlug_joint3Scale.connectedTo(mPlugArray_joint3,True,True)
	                        for i in xrange(mPlugArray_joint3.length()):
	                            if mPlugArray_joint3[i].node().apiTypeStr() == "kJoint":
	                                mObj_joint3Connections.append(mPlugArray_joint3[i].node())


	                        mFnDependencyNode_temp1 = OpenMaya.MFnDependencyNode()
	                        mFnDependencyNode_temp3 = OpenMaya.MFnDependencyNode()

	                        for i in xrange(mObj_joint1Connections.length()):
	                            for j in xrange(mObj_joint3Connections.length()):
	                                mFnDependencyNode_temp1.setObject(mObj_joint1Connections[i])
	                                mFnDependencyNode_temp3.setObject(mObj_joint3Connections[j])
	                                if mFnDependencyNode_temp1.name() ==mFnDependencyNode_temp3.name():
	                                    self.joint2 = mObj_joint3Connections[j]
	                                    break


	        if self.activeEffector.apiTypeStr() == "kIkEffector":
	            # Control curve 'visibility' plug
	            if self.activePoleVectorControl.apiTypeStr() != "kInvalid":
	                mPlug_controlCurveVisibility = OpenMaya.MFnTransform(self.activePoleVectorControl).findPlug("visibility")

	            m = OpenMaya.MFnDependencyNode(self.activeHandle)
	            print m.name()
	            for i in range(len(selectedIK)):
	                if m.name() == selectedIK[i-1]:

        	            if mode=='fk':
        	                # Because fk is the default mode, even if IK-handle does not exist it will try to set the plug
        	                try:
        	                    mPlug_blendAttr.setInt(0)
        	                    mPlug_controlCurveVisibility.setBool(False)
        	                except:
        	                    pass
        	            else:
        	                if self.joint2.apiTypeStr() == "kJoint":
        	                    mFnTransform_poleControl = OpenMaya.MFnTransform(self.activePoleVectorControl)
        	                    mFnTransform_joint2 = OpenMaya.MFnTransform(self.joint2)

        	                    # Reading MDagPath from MObject.
        	                    mDagPath_joint2 = OpenMaya.MDagPath()
        	                    mFnTransform_joint2.getPath(mDagPath_joint2)
        	                    mFnTransform_joint2.setObject(mDagPath_joint2)

        	                    mDagPath_poleControl = OpenMaya.MDagPath()
        	                    mFnTransform_poleControl.getPath(mDagPath_poleControl)
        	                    mFnTransform_poleControl.setObject(mDagPath_poleControl)

        	                    mFnTransform_poleControl.setTranslation(mFnTransform_joint2.getTranslation(OpenMaya.MSpace.kWorld),OpenMaya.MSpace.kWorld)
        	                    try:
        	                        mPlug_controlCurveVisibility.setBool(True)
        	                    except:
        	                        pass
        	                mPlug_blendAttr.setInt(1)

	def remove(self,*args):
		try:
			OpenMaya.MSelectionList.add(self.thisMObject())
		except:
			# Remove callbacks
			for i in xrange(len(self.idCallback)):
				try:
					OpenMaya.MEventMessage.removeCallback(self.idCallback[i])
				except:
					pass
				try:
					OpenMaya.MDGMessage.removeCallback(self.idCallback[i])
				except:
					pass


	def compute(self, plug, dataBlock):
		pass

#Creates the CVG node
def nodeCreator():
    nodePtr = OpenMayaMPx.asMPxPtr(CVG())
    return nodePtr

#Creates the GetIKHandles command
def cmdCreator():
    return OpenMayaMPx.asMPxPtr(GetIKHandles())

def nodeInitializer():
	pass

#Initializes the plugin
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject,"Farley Maya Practicum", "1.0")

    # Register GetIKHandles as a command
    try:
        mplugin.registerCommand("GetIKHandles", cmdCreator)
    except:
        sys.stderr.write("Failed to register command: GetIKHandles")
    #Register CVG as a node
    try:
        mplugin.registerNode(nodeName, nodeId, nodeCreator, nodeInitializer)
    except:
        sys.stderr.write("Failed to register node: %s" % nodeName)
        raise

    BasicDialog().show()

#Uninstalls the plugin
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand("GetIKHandles")
    except:
        sys.stderr.write("Failed to deregister command: GetIKHandles")
    try:
        mplugin.deregisterNode(nodeId)
    except:
        sys.stderr.write("Failed to deregister node: %s" % nodeName)
        raise
