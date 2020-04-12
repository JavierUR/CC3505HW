# coding=utf-8
"""
Javier Urrutia, CC3501, 2020-1
Space Wars game, designe with the 
model-view-controller design pattern
"""
import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np
import sys

import easy_shaders as es
import basic_shapes as bs
import transformations as tr
import scene_graph as sg

import game_shapes as gs
# A class to store the application control
class Controller:
    pass

class GameModel:
    def __init__(self, enemies, screenWidht, screenHeight):
        # Create game scene
        self.gameScene = sg.SceneGraphNode("gameScene")
        self.gameScene.transform = tr.scale(screenHeight/screenWidht,1.0,1.0)

        # Load game models
        self.enemyModel = gs.createEnemy()
        self.playerModel = gs.createPlayer()
        self.playerShotModel = gs.createShot(0.8,0.4,0.0)
        self.enemyShotModel = gs.createShot(0.4,0.8,0.0)

    def updateScene(self, time):
        enemy1 = sg.SceneGraphNode("enemy1")
        enemy1.childs = [self.enemyModel]

        player = sg.SceneGraphNode("Player")
        player.transform = tr.translate(0.0, -0.75, 0.0)
        player.childs = [self.playerModel]

        testShot = sg.SceneGraphNode("testShot")
        testShot.transform = tr.translate(0.0,-0.2,0.0)
        testShot.childs = [self.playerShotModel]

        self.gameScene.childs = [player, enemy1, testShot]
        return self.gameScene

    
controller = Controller()

def on_key(window, key, scancode, action, mods):
    #Function to react to key press
    if action != glfw.PRESS:
        return
    
    global controller # Declares that we are going to use the global object controller inside this function.

    if key == glfw.KEY_ESCAPE:
        sys.exit()

    else:
        print('Unknown key')



if __name__ == "__main__":

    # Initialize glfw
    if not glfw.init():
        sys.exit()

    width = 450
    height = 600

    window = glfw.create_window(width, height, "Space Wars", None, None)

    if not window:
        glfw.terminate()
        sys.exit()
        

    glfw.make_context_current(window)

    # Connecting the callback function 'on_key' to handle keyboard events
    glfw.set_key_callback(window, on_key)

    # Setting up the clear screen color
    glClearColor(0.0, 0.0, 0.0, 1.0)

    # Enabling transparencies
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # A simple shader program with position and texture coordinates as inputs.
    pipelineTexture = es.SimpleTextureTransformShaderProgram()

    # A simple shader program with position and texture coordinates as inputs.
    pipelineColor = es.SimpleTransformShaderProgram()
    
    background = gs.createBackground("stars.png")

    gameModel = GameModel(10, width, height)
    
    while not glfw.window_should_close(window):
        # Using GLFW to check for input events
        glfw.poll_events()

        # Clearing the screen in both, color and depth
        glClear(GL_COLOR_BUFFER_BIT)

        time = glfw.get_time()

        #Draw background
        # Telling OpenGL to use our shader program
        glUseProgram(pipelineTexture.shaderProgram)
        background.transform = tr.translate(0,(-time/2)%2,0)
        sg.drawSceneGraphNode(background,pipelineTexture,"transform")

        #Draw ships
        # Telling OpenGL to use our shader program
        glUseProgram(pipelineColor.shaderProgram)
        gameScene = gameModel.updateScene(time)
        sg.drawSceneGraphNode(gameScene, pipelineColor, "transform")

        # Once the render is done, buffers are swapped, showing only the complete scene.
        glfw.swap_buffers(window)