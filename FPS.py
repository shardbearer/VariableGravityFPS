#!/usr/bin/env ppython
from panda3d.core import loadPrcFileData
loadPrcFileData("", "parallax-mapping-samples 3")
loadPrcFileData("", "parallax-mapping-scale 0.1")

resX=1280
resY=778
screenX=1280
topBar=22
#loadPrcFileData('', 'win-origin '+`screenX-resX`+' '+`topBar`) # upper right
loadPrcFileData('', 'win-origin 0 '+`topBar`) # upper left
loadPrcFileData('', 'win-size '+`resX`+' '+`resY`)

import math
from direct.gui.OnscreenImage import OnscreenImage
import direct.directbase.DirectStart
from panda3d.core import WindowProperties
from panda3d.core import Filename,Shader
from panda3d.core import AmbientLight,PointLight
from panda3d.core import TextNode
from panda3d.core import TransparencyAttrib
from panda3d.core import Point3,Vec3,Vec4
from direct.task.Task import Task
from direct.actor.Actor import Actor
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.filter.CommonFilters import *
import sys,os

class BumpMapDemo(DirectObject):
    speed=80
    vJump=35
    G=-98 # Gravity acceleration
    Gmin=-2
    Gmax=-1000
    fallMult=3
    vZTarg= -400 #Terminal velocity
    gAcc= 350 #Max acc on ground
    jumpSlow=.9 #Slow down horizontal speed when jumping
    L = 0.65
    crosshairSize=4

    floor=17
    roof=45

    heading=-20
    pitch=-20
    key=[0,0,0]
    forward=[0]
    back=[0]
    left=[0]
    right=[0]
    jump=[0]
    vX=0
    vY=0
    vZ=0
    vXTarg=0
    vYTarg=0
    k=0

    def __init__(self):
        self.title = OnscreenText(text="Adrian's Unamed Game", style=1, fg=(1,1,1,1), pos=(-1.0, 1.25), align=TextNode.ALeft, scale = .05)
        self.crosshair = OnscreenImage(image = 'Crosshair16Sharp.png', scale=min((float(self.crosshairSize)/resX), (float(self.crosshairSize)/resY))) 
#        self.crosshair = OnscreenImage(image = 'Crosshair16Sharp.png', parent=pixel2d, scale=(self.crosshairSize/2.0, 1, self.crosshairSize/2.0), pos=(resX/2.0, 0, -resY/2.0)) 
        self.crosshair.setTransparency(TransparencyAttrib.MAlpha)
        self.room = loader.loadModel('models/abstractroom')
        self.room.reparentTo(render)

        base.disableMouse()
        props = WindowProperties()
        props.setCursorHidden(True)
        base.win.requestProperties(props)

        base.camLens.setFov(80)
        taskMgr.add(self.controlCamera, "camera-task")
        self.accept("escape", sys.exit, [0])
        self.accept("space", self.setJump, [0, 1])
        self.accept("space-up", self.setJump, [0, 0])
        self.accept("e", self.setForward, [0, 1])
        self.accept("e-up", self.setForward, [0, 0])
        self.accept("d", self.setBackward, [0, 1])
        self.accept("d-up", self.setBackward, [0, 0])
        self.accept("s", self.setLeft, [0, 1])
        self.accept("s-up", self.setLeft, [0, 0])
        self.accept("f", self.setRight, [0, 1])
        self.accept("f-up", self.setRight, [0, 0])

        self.lightpivot = render.attachNewNode("lightpivot")
        self.lightpivot.setPos(0,0,25)
        self.lightpivot.hprInterval(10,Point3(360,0,0)).loop()
        plight = PointLight('plight')
        plight.setColor(Vec4(1, 1, 1, 1))
        plight.setAttenuation(Vec3(0.7,0.05,0))
        plnp = self.lightpivot.attachNewNode(plight)
        plnp.setPos(45, 0, 0)
        self.room.setLight(plnp)
        self.room.setShaderInput("light", plnp)

        alight = AmbientLight('alight')
        alight.setColor(Vec4(self.L, self.L, self.L, 1))
        alnp = render.attachNewNode(alight)
        self.room.setLight(alnp)

        self.shaderenable = 0
        self.room.setShaderAuto()

    def rotateLight(self, offset):
        self.lightpivot.setH(self.lightpivot.getH()+offset*20)

    def setJump(self, btn, value):
        self.jump[btn] = value

    def setForward(self, btn, value):
        self.forward[btn] = value

    def setBackward(self, btn, value):
        self.back[btn] = value

    def setLeft(self, btn, value):
        self.left[btn] = value

    def setRight(self, btn, value):
        self.right[btn] = value

    def setKey(self, btn, value):
        self.key[btn] = value

    def controlCamera(self, task):
        self.vXTarg = 0
        self.vYTarg = 0
        k=0
        md = base.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        if base.win.movePointer(0, 100, 100):
            self.heading = self.heading - (x - 100) * 0.2
            self.pitch = self.pitch - (y - 100) * 0.2
        if (self.pitch < -90): self.pitch = -90
        if (self.pitch >  90): self.pitch =  90
        base.camera.setHpr(self.heading, self.pitch, 0)

        if self.forward[0] == 1 and self.back[0] == 0: #Move Forward
            self.vXTarg = float(k*self.vXTarg - math.sin(math.radians(self.heading%360)) * self.speed)/(k+1)
            self.vYTarg = float(k*self.vYTarg + math.cos(math.radians(self.heading%360)) * self.speed)/(k+1)
            k=k+1
        if self.back[0] == 1 and self.forward[0] == 0: #Move Back
            self.vXTarg = float(k*self.vXTarg + math.sin(math.radians(self.heading%360)) * self.speed)/(k+1)
            self.vYTarg = float(k*self.vYTarg - math.cos(math.radians(self.heading%360)) * self.speed)/(k+1)
            k=k+1
        if self.left[0] == 1 and self.right[0] == 0: #Move Left
            self.vXTarg = float(k*self.vXTarg - math.sin(math.radians(self.heading%360+90)) * self.speed)/(k+1)
            self.vYTarg = float(k*self.vYTarg + math.cos(math.radians(self.heading%360+90)) * self.speed)/(k+1)
            k=k+1
        if self.right[0] == 1 and self.left[0] == 0: #Move Right
            self.vXTarg = float(k*self.vXTarg + math.sin(math.radians(self.heading%360+90)) * self.speed)/(k+1)
            self.vYTarg = float(k*self.vYTarg - math.cos(math.radians(self.heading%360+90)) * self.speed)/(k+1)
            k=k+1

        if self.jump[0] == 1 and base.camera.getZ() <= self.floor and self.vZ < 0:
            self.vX = self.vXTarg*.6
            self.vY = self.vYTarg*.6

        if self.jump[0] and base.camera.getZ() <= self.floor: #Jump
            self.vZ=self.vJump

        if self.vX < self.vXTarg and base.camera.getZ() <= self.floor:
            self.vX = self.vX + (self.gAcc * globalClock.getDt())
            if self.vX > self.vXTarg:
                self.vX = self.vXTarg
        if self.vX > self.vXTarg and base.camera.getZ() <= self.floor:
            self.vX = self.vX - (self.gAcc * globalClock.getDt())
            if self.vX < self.vXTarg:
                self.vX = self.vXTarg
        if self.vY < self.vYTarg and base.camera.getZ() <= self.floor:
            self.vY = self.vY + (self.gAcc * globalClock.getDt())
            if self.vY > self.vYTarg:
                self.vY = self.vYTarg
        if self.vY > self.vYTarg and base.camera.getZ() <= self.floor:
            self.vY = self.vY - (self.gAcc * globalClock.getDt())
            if self.vY < self.vYTarg:
                self.vY = self.vYTarg

        if self.vZ > self.vZTarg and base.camera.getZ() > self.floor:
            self.vZ = self.vZ + self.G * globalClock.getDt()

        if (self.floor >= base.camera.getZ() and self.vZ < 0) or (self.roof <= base.camera.getZ() and self.vZ > 0.0): #Stop moving if you hit the walls 
            self.vZ = 0

        if math.fabs( self.vX ) > self.speed: self.vX=self.speed
        if math.fabs( self.vY ) > self.speed: self.vY=self.speed
        if self.vZ < self.vZTarg: self.vZ=self.vZTarg

        base.camera.setX(base.camera.getX() + self.vX * globalClock.getDt())
        base.camera.setY(base.camera.getY() + self.vY * globalClock.getDt())
        base.camera.setZ(base.camera.getZ() + self.vZ * globalClock.getDt() * self.fallMult)

#        if (base.camera.getX() < -55.0): base.camera.setX(-55) # Keep in room
#        if (base.camera.getX() >  55.0): base.camera.setX( 55)
#        if (base.camera.getY() < -55.0): base.camera.setY(-55)
#        if (base.camera.getY() >  55.0): base.camera.setY( 55)
        if (base.camera.getZ() < self.floor): base.camera.setZ(self.floor)
#        if (base.camera.getZ() >  self.roof): base.camera.setZ(self.roof)

        print str(self.heading%360), str(self.pitch%360)
        if globalClock.getDt() != 0:
            print int(1/globalClock.getDt())
        print self.vX, self.vY, self.vZ
#        print base.camera.getX(), base.camera.getY()
        return Task.cont

t = BumpMapDemo()
run()
