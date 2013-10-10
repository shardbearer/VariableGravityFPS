#!/usr/bin/env ppython
from panda3d.core import loadPrcFileData
loadPrcFileData("", "parallax-mapping-samples 3")
loadPrcFileData("", "parallax-mapping-scale 0.1")

screenX=1280
screenY=800
topBar=22

resX=screenX
resY=screenY-topBar

resX=800
resY=600

loadPrcFileData('', 'win-origin '+`screenX-resX`+' '+`topBar`) # upper right
#loadPrcFileData('', 'win-origin 0 '+`topBar`) # upper left
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
import numpy as np

class BumpMapDemo(DirectObject):

    ratio=resX/float(resY)

    speed=80
    VJumpDef=35
    VJumpMax=200
    jumpMaxG=300
    Acc= 350 #Max acc on ground
    jumpSlow=.9 #Coefficient for slowing down horizontal speed when jumping
    jumpAgainCoef=.7
    
    Vhurt=100
    rollInc=500
    health=100
    fallHurtCoef=.1

    height=20
    eyeHeight=15
    floor=eyeHeight
    roof=9999999999-eyeHeight

    Gdef=-98.0 # Gravity acceleration
    Gmin=30
    Gmax=200
    Ginc=0.5
    GTickNum=10
    Gcurve=2
    VZTargDef= -500 #Terminal velocity

    GTickA=np.arange(-GTickNum, GTickNum+1, 1)
    GA = np.sign(GTickA) * (abs(GTickA/float(GTickNum))**Gcurve*(Gmax-Gmin)+Gmin)
    GTickA = np.delete(GTickA,GTickNum)
    GA = np.delete(GA,GTickNum)

    print GTickA
    print GA
    
    L = 0.65 #Light level
    crosshairSize=4

    heading=-20
    pitch=-20
    roll=0
    forward=[0]
    back=[0]
    left=[0]
    right=[0]
    jump=[0]
    flip=1
    X=0
    Y=0
    Z=floor
    VX=0
    VY=0
    VZ=0
    VXTarg=0
    VYTarg=0
    XAccDir=0
    YAccDir=0
    ZAccDir=0
    k=0
    dt=0.0
    G=Gdef
    GTick=0
    VJump=VJumpDef
    VZTarg=VZTargDef
    i=0
    startTime=0

    def __init__(self):

        self.title = OnscreenText(text="Variable Gravity FPS", pos=(self.ratio-.1, .9), fg=(1,1,1,1), align=TextNode.ARight, scale = .1)
        self.title = OnscreenText(text="100", pos=(self.ratio-.1, -.9), fg=(1,1,1,1), align=TextNode.ARight, scale = .1)
        self.crosshair = OnscreenImage(image = 'Crosshair16Sharp.png', scale=min((float(self.crosshairSize)/resX), (float(self.crosshairSize)/resY))) 
#        self.crosshair = OnscreenImage(image = 'Crosshair16Sharp.png', parent=pixel2d, scale=(self.crosshairSize/2.0, 1, self.crosshairSize/2.0), pos=(resX/2.0, 0, -resY/2.0)) 
        self.crosshair.setTransparency(TransparencyAttrib.MAlpha)

#        self.room = loader.loadModel('models/abstractroom')
        self.room = loader.loadModel('models/world')
        self.room.reparentTo(render)

        base.disableMouse()
        props = WindowProperties()
        props.setCursorHidden(True)
        base.win.requestProperties(props)

        base.camLens.setFov(80)
        base.camera.setZ(self.floor)
        taskMgr.add(self.controlCamera, "camera-task")
        self.accept("escape", sys.exit, [0])
        self.accept("space", self.setJump, [0, 1])
        self.accept("space-up", self.setJump, [0, 0])
        self.accept("w", self.setForward, [0, 1])
        self.accept("w-up", self.setForward, [0, 0])
        self.accept("s", self.setBackward, [0, 1])
        self.accept("s-up", self.setBackward, [0, 0])
        self.accept("a", self.setLeft, [0, 1])
        self.accept("a-up", self.setLeft, [0, 0])
        self.accept("d", self.setRight, [0, 1])
        self.accept("d-up", self.setRight, [0, 0])
        self.accept("f", self.setFlip)
        self.accept("wheel_up", self.gravUp)
        self.accept("wheel_down", self.gravDown)
        self.accept("r", self.gravReset)

        alight = AmbientLight('alight')
        alight.setColor(Vec4(self.L, self.L, self.L, 1))
        alnp = render.attachNewNode(alight)
        self.room.setLight(alnp)

        self.shaderenable = 0
        self.room.setShaderAuto()
        self.startTime=globalClock.getDt()

        base.camera.setZ(self.floor)
        self.health=100


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

    def gravUp(self):
        self.GTick += 1

        if self.GTick > self.GTickNum - 1:
            self.GTick = self.GTickNum - 1

        self.G = self.GA[self.GTick-self.GTickNum]

        self.VJump = self.VJumpDef * (self.Gdef/self.G)
        if self.VJump > self.VJumpMax:
            self.VJump = self.VJumpMax

        self.VZTarg = self.VZTargDef * (self.G/self.Gdef) 

    def gravDown(self):
        self.GTick -= 1

        if self.GTick < -self.GTickNum:
            self.GTick = -self.GTickNum

        self.G = self.GA[self.GTick-self.GTickNum]

        self.VJump = self.VJumpDef * (self.Gdef/self.G)
        if self.VJump > self.VJumpMax:
            self.VJump = self.VJumpMax

        self.VZTarg = self.VZTargDef * (self.G/self.Gdef) 
    
    def setFlip(self):
        if self.roll == 0 or self.roll == 180:
            self.flip *= -1

    def gravReset(self):
        self.G = self.Gdef

    def controlCamera(self, task):
        self.X = base.camera.getX()
        self.Y = base.camera.getY()
        self.Z = base.camera.getZ()
        
        self.VXTarg = 0
        self.VYTarg = 0
        k=0
        md = base.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        if base.win.movePointer(0, 100, 100):
            self.heading = self.heading - (x - 100) * 0.2 * self.flip
            self.pitch = self.pitch - (y - 100) * 0.2 * self.flip
        if (self.pitch < -90): self.pitch = -90
        if (self.pitch >  90): self.pitch =  90

        if self.flip == -1 and self.roll < 180:
            self.roll += self.rollInc*self.dt
            if self.roll > 180:
                self.roll = 180
        if self.flip ==  1 and self.roll < 360 and self.roll > 0:
            self.roll += self.rollInc*self.dt
            if self.roll > 360:
                self.roll = 0

        if self.roll > 360:
            self.roll = 0
        if self.roll < 0:
            self.roll = 0
           
        base.camera.setHpr(self.heading, self.pitch, self.roll)


        if self.VZ * cmp(self.G,0) < abs(self.VZTarg):
            self.VZ += self.G * self.dt * self.flip #Gravity
        
        if (self.floor >= self.Z and self.VZ < 0) or (self.roof <= self.Z and self.VZ > 0): #Stop moving if you hit the floor or ceiling
            if(abs(self.VZ)>self.Vhurt):
                self.health-=(abs(self.VZ)-self.Vhurt)*self.fallHurtCoef
            self.VZ = 0

        if (self.roll == 0 or self.roll == 180) and ((self.flip == 1 and self.Z <= self.floor) or (self.flip == -1 and self.Z >= self.roof)):
            
            if self.forward[0] == 1 and self.back[0] == 0: #Move Forward
                self.VXTarg = float(k*self.VXTarg - math.sin(math.radians(self.heading%360)) * self.speed)/(k+1)
                self.VYTarg = float(k*self.VYTarg + math.cos(math.radians(self.heading%360)) * self.speed)/(k+1)
                k+=1
            if self.back[0] == 1 and self.forward[0] == 0: #Move Back
                self.VXTarg = float(k*self.VXTarg + math.sin(math.radians(self.heading%360)) * self.speed)/(k+1)
                self.VYTarg = float(k*self.VYTarg - math.cos(math.radians(self.heading%360)) * self.speed)/(k+1)
                k+=1
            if self.left[0] == 1 and self.right[0] == 0: #Move Left
                self.VXTarg = float(k*self.VXTarg - math.sin(math.radians(self.heading%360+90)) * self.flip * self.speed)/(k+1)
                self.VYTarg = float(k*self.VYTarg + math.cos(math.radians(self.heading%360+90)) * self.flip * self.speed)/(k+1)
                k+=1
            if self.right[0] == 1 and self.left[0] == 0: #Move Right
                self.VXTarg = float(k*self.VXTarg + math.sin(math.radians(self.heading%360+90)) * self.flip * self.speed)/(k+1)
                self.VYTarg = float(k*self.VYTarg - math.cos(math.radians(self.heading%360+90)) * self.flip * self.speed)/(k+1)
                k+=1

            if self.jump[0] == 1 and ((self.Z <= self.floor and self.VZ < 0) or (self.Z >=self.roof and self.VZ > 0)):
                self.VX = self.VXTarg*self.jumpAgainCoef
                self.VY = self.VYTarg*self.jumpAgainCoef
            
            if self.jump[0] and abs(self.G) <= self.jumpMaxG: #Jump
                self.VZ = self.VJump * self.flip
            
            self.XAccDir=cmp(self.VXTarg, self.VX)
            self.VX += self.XAccDir * self.Acc * self.dt
            if cmp(self.VXTarg, self.VX) != self.XAccDir:
                self.VX = self.VXTarg

            self.YAccDir=cmp(self.VYTarg, self.VY)
            self.VY += self.YAccDir * self.Acc * self.dt
            if cmp(self.VYTarg, self.VY) != self.YAccDir:
                self.VY = self.VYTarg

        self.X += self.VX * self.dt
        self.Y += self.VY * self.dt
        self.Z += self.VZ * self.dt

        if (self.Z < self.floor): self.Z = self.floor
        if (self.Z > self.roof): self.Z = self.roof

        base.camera.setPos(self.X, self.Y, self.Z)


#        print str(self.heading%360), str(self.pitch%360), str(self.roll%360)

#        if self.dt != 0:
#            print int(1/self.dt)

#        if self.dt !=0:
#            print int(self.i/(globalClock.getFrameTime()-self.startTime))

#        print self.VX, self.VY, self.VZ
#        print self.X, self.Y, self.Z
        print self.health
#        print self.VZ
        print self.Z
#        print self.GTick
        print self.G

        self.dt = float(globalClock.getDt())
        return Task.cont

t = BumpMapDemo()
run()
