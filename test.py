#!/usr/bin/env ppython
from panda3d.core import loadPrcFileData
loadPrcFileData("", "parallax-mapping-samples 3")
loadPrcFileData("", "parallax-mapping-scale 0.1")

import direct.directbase.DirectStart
from panda3d.core import WindowProperties
from panda3d.core import Filename,Shader
from panda3d.core import AmbientLight,PointLight
from panda3d.core import TextNode
from panda3d.core import TransparencyAttrib
from panda3d.core import Point3,Vec3,Vec4
from direct.task.Task import Task
#from direct.actor.Actor import Actor
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.filter.CommonFilters import *
import sys,os

class DispTest(DirectObject):
    def __init__(self):
        self.room = loader.loadModel('models/abstractRoom2')
        self.room.reparentTo(render)

        self.accept("escape", sys.exit, [0])

        alight = AmbientLight('alight')
        alight.setColor(Vec4(.5, .5, .5, 1))
        alnp = render.attachNewNode(alight)
        self.room.setLight(alnp)

        self.shaderenable = 0
        self.room.setShaderAuto()

t = DispTest()
run()

