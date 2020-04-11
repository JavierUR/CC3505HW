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
# A class to store the application control
class Controller:
    pass


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

def createBackground(filename):
    # Load background image
    gpuStars = es.toGPUShape(bs.createTextureQuad("stars.png"), GL_REPEAT, GL_LINEAR)

    background = sg.SceneGraphNode("background")
    background.transform = tr.scale(2,2,1)
    background.childs = [gpuStars]

    return background



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
    pipeline = es.SimpleTextureTransformShaderProgram()
    
    # Telling OpenGL to use our shader program
    glUseProgram(pipeline.shaderProgram)

    background = createBackground("stars.png")

    while not glfw.window_should_close(window):
        # Using GLFW to check for input events
        glfw.poll_events()

        # Clearing the screen in both, color and depth
        glClear(GL_COLOR_BUFFER_BIT)

        time = glfw.get_time()

        #Draw background
        sg.drawSceneGraphNode(background,pipeline,"transform")
        # Once the render is done, buffers are swapped, showing only the complete scene.
        glfw.swap_buffers(window)