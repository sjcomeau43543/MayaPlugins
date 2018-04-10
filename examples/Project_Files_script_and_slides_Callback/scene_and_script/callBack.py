# =====================================================================
# Author : Chayan Vinayak
# Copyright Chayan Vinayak
#
# =====================================================================

import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx

nodeName = "CVGKNode"
nodeId = OpenMaya.MTypeId(0x100fff)

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
		# Event Callback 
		self.idCallback.append(OpenMaya.MEventMessage.addEventCallback("SelectionChanged",self.callbackFunc))
		# DG Callback 
		self.idCallback.append(OpenMaya.MDGMessage.addNodeRemovedCallback(self.remove,"dependNode"))
		
	def callbackFunc(self,*args):
	    print "Called"
	    # 1. Find active selection in the scene
	    mSel = OpenMaya.MSelectionList()
	    OpenMaya.MGlobal.getActiveSelectionList(mSel)
	    mItSelectionList = OpenMaya.MItSelectionList(mSel,OpenMaya.MFn.kDagNode)
	    mode = "fk"
	    
	    mFnDependencyNode = OpenMaya.MFnDependencyNode()
	    
	    # 2. Find IK-Effector        
	    while(not mItSelectionList.isDone()):
	        mObj = OpenMaya.MObject()
	        mItSelectionList.getDependNode(mObj)          
	        # If effector itself is selected
	        if mObj.apiTypeStr() == "kIkEffector":
	            self.activeEffector = mObj
	            mode = "ik"
	            break
	        # If control curve is selected
	        if self.activePoleVectorControl.apiTypeStr() != "kInvalid":
	            if OpenMaya.MFnDependencyNode(mObj).name() == OpenMaya.MFnDependencyNode(self.activePoleVectorControl).name():
	                mode = "ik"
	                break                
	        mFnDependencyNode.setObject(mObj)
	        mPlugArray_joint = OpenMaya.MPlugArray()
	        mFnDependencyNode.getConnections(mPlugArray_joint)
	        # Check If effector is connected to selected object
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
	        
	        # 3. Find IK-Handle         
	        #print self.activeEffector.apiTypeStr()      
	        ''' If IK-Effector is found then :
	            - find IK-Handle
	        '''  
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
	            
	            ''' If IK-Handle is found then :
	                - find IK-Blend Plug
	                - find IK-PoleVector 
	            '''                 
	            
	            if self.activeHandle.apiTypeStr() == "kIkHandle": 
	                # 4. Find IK-Blend Plug
	                mFnDependNodeHandle = OpenMaya.MFnDependencyNode(self.activeHandle)
	                mPlug_blendAttr = mFnDependNodeHandle.findPlug("ikBlend")
	                mAttr_blendAttr = mPlug_blendAttr.attribute() 
	                # make IK-blend attribute "unKeyable" and hidden from Channel box
	                mMFnAttribute = OpenMaya.MFnAttribute(mAttr_blendAttr)
	                mMFnAttribute.setKeyable(0)
	                mMFnAttribute.setChannelBox(0)       
	                
	                # 5. Find Pole Vector Constraint
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
	                                   
	                if self.activePoleVector.apiTypeStr() == "kPoleVectorConstraint": 
	                    # 6. Find Curve controlling Pole Vector
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
	                    if self.activePoleVectorControl.apiTypeStr() == "kTransform":  
	                        # 7. Find Joint2 of the chain.
	                        # 7. a : find joint connected to IK-Effector - call it : Joint3
	                        # 7. b : find joint connected to IK-Handle   - call it : Joint1
	                        # 7. c : find joint connected to Joint1 and Joint3 - call it Joint2
	                                                     
	                        # 7. a : find joint connected to IK-Effector - call it : Joint3                    
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
	                        # 7. b : find joint connected to IK-Handle   - call it : Joint1                  
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
	                         
	                        # 7. c : find joint connected to Joint1 and Joint3 - call it Joint2
	                        '''
	                        Find joints connected to Joint1 , and if any joint which is connected to Joint1 is also connected to Joint3
	                        then it is Joint2                       
	                        '''
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
			# Check if this node exists in the scene
			OpenMaya.MSelectionList.add(self.thisMObject())
		except:
			# Remove callback 
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
		
def nodeCreator():
    nodePtr = OpenMayaMPx.asMPxPtr(CVG())
    return nodePtr

def nodeInitializer():
	pass
    
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject,"Chayan Vinayak", "1.0")
    try:
        mplugin.registerNode(nodeName, nodeId, nodeCreator, nodeInitializer)
    except:
        sys.stderr.write("Failed to register node: %s" % nodeName)
        raise

def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode(nodeId)
    except:
        sys.stderr.write("Failed to deregister node: %s" % nodeName)
        raise