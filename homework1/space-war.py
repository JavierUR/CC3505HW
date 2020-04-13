# coding=utf-8
"""
Javier Urrutia, CC3501, 2020-1
Space Wars game, designed with the 
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
import game_model as gm
import game_utils as gu
# A class to store the application control
class Controller:
    right = False
    left = False
    up = False
    down = False
    fire = False

controller = Controller()

def on_key(window, key, scancode, action, mods):
    global controller # Declares that we are going to use the global object controller inside this function.
    #Function to react to key press
    if key == glfw.KEY_D:
        controller.right = (action == glfw.PRESS or action == glfw.REPEAT)
    elif key == glfw.KEY_A:
        controller.left = (action == glfw.PRESS or action == glfw.REPEAT)
    elif key == glfw.KEY_W:
        controller.up = (action == glfw.PRESS or action == glfw.REPEAT)
    elif key == glfw.KEY_S:
        controller.down = (action == glfw.PRESS or action == glfw.REPEAT)
    elif key == glfw.KEY_SPACE:
        controller.fire = (action == glfw.PRESS or action == glfw.REPEAT)

    elif key == glfw.KEY_ESCAPE:
        sys.exit()

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
    
    background = gs.create_background("stars.png")
    gameoverScreen = gs.create_gameover_screen("gameOver.png")
    gameoverTray = gu.LinearTrayectory(0, 2, 0.0, 2.0, 0.0, 0.0)
    drawGameOver = False

    gameModel = gm.GameModel(10, width, height, controller)
    
    while not glfw.window_should_close(window):
        # Using GLFW to check for input events
        glfw.poll_events()

        # Clearing the screen in both, color and depth
        glClear(GL_COLOR_BUFFER_BIT)

        time = glfw.get_time()

        #Draw background
        # Telling OpenGL to use our shader program for textures
        glUseProgram(pipelineTexture.shaderProgram)
        background.transform = tr.translate(0,(-time/4)%2,0)
        sg.drawSceneGraphNode(background,pipelineTexture,"transform")

        #Draw ships
        # Telling OpenGL to use our shader program
        glUseProgram(pipelineColor.shaderProgram)
        gameScene = gameModel.updateScene(time)
        sg.drawSceneGraphNode(gameScene, pipelineColor, "transform")

        # Game over screen handling
        if gameModel.gameover and not drawGameOver:
            drawGameOver = True
            gameoverTray.ti = time
        if drawGameOver:
            # Telling OpenGL to use our shader program for textures
            glUseProgram(pipelineTexture.shaderProgram)
            goX, goY = gameoverTray.get_pos(time)
            gameoverScreen.transform = tr.translate(goX, goY, 0.0)
            sg.drawSceneGraphNode(gameoverScreen,pipelineTexture,"transform")

        # Once the render is done, buffers are swapped, showing only the complete scene.
        glfw.swap_buffers(window)