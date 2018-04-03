import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import sys

commandName = "pluginCommand"

class pluginCommand(OpenMayaMPx.MPxCommand):
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)
    
    def doIt(self, argList):
        print "doIt..."

def cmdCreator():
    return OpenMayaMPx.asMPxPtr(pluginCommand())

def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerCommand(commandName, cmdCreator)
    except:
        sys.stderr.write("Failed to register command :"+commandName)

def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand(commandName)
    except:
        sys.stderr.write("Failed to de-register command :"+commandName)
