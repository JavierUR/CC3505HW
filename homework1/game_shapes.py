# coding=utf-8
"""
Javier Urrutia, CC3501, 2020-1
Space Wars game, designe with the 
Specific shapes used for the game
"""
from OpenGL.GL import *

import easy_shaders as es
import transformations as tr
import basic_shapes as bs
import scene_graph as sg

def createBackground(filename):
    # Load background image
    gpuStars = es.toGPUShape(bs.createTextureQuad(filename), GL_REPEAT, GL_LINEAR)

    #Create two background copies to have a scrolling effect
    background = sg.SceneGraphNode("background")
    background.transform = tr.scale(2,2,1)
    background.childs = [gpuStars]

    background2 = sg.SceneGraphNode("background2")
    background2.transform = tr.matmul([tr.scale(2,2,1),tr.translate(0,-1,0)])
    background2.childs = [gpuStars]

    # Node to control vertical movement of the two backgrounds objects
    backgroundVertical = sg.SceneGraphNode("backgroundVertical")
    backgroundVertical.childs = [background, background2]
    return backgroundVertical