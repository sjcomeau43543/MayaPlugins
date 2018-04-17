import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import sys

d = OpenMaya.MItDependencyNodes()
mFnDependencyNode = OpenMaya.MFnDependencyNode()
while(not d.isDone()):
    mObj = d.thisNode()
    if mObj.apiTypeStr() == 'kIkHandle':
        m = OpenMaya.MFnDependencyNode(mObj)
        print m.name()

    d.next()
