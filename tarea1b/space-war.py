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
import argparse

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

class ScreenDrawer:
    def __init__(self, gameModel, backgroundFile, gameoverFile, winFile):
        # gameModel - GameModel instance
        # backgroundFile - File path of background texture
        # gameoverFile - File path of game over texture
        # winFile - File path of the game win texture
        # Reference to the game model instance
        self.gameModel = gameModel
        # Load background and gameover models
        self.background = gs.create_background(backgroundFile)
        self.gameoverScreen = gs.create_gameover_screen(gameoverFile)
        self.winScreen = gs.create_gameover_screen(winFile)

        # Define pipelines for drawing
        self.pipelineTexture = es.SimpleTextureTransformShaderProgram()
        self.pipelineColor = es.SimpleTransformShaderProgram()

        # Trayectory animation for end screen
        self.endTray = None
        self.endScreen = None

    def drawBackground(self, time):
        #Draw the moving background
        # time - current clock time in seconds
        # Telling OpenGL to use our shader program for textures
        glUseProgram(self.pipelineTexture.shaderProgram)
        self.background.transform = tr.translate(0,(-time/4)%2,0)
        sg.drawSceneGraphNode(self.background,self.pipelineTexture,"transform")

    def drawGameElements(self):
        #Draw ships snd shots
        # Telling OpenGL to use our shader program
        glUseProgram(self.pipelineColor.shaderProgram)
        sg.drawSceneGraphNode(self.gameModel.getGameScene(), self.pipelineColor, "transform")

    def drawEndScreen(self, time, endScreen):
        # End screen handling
        # endScreen - end creen SceneGraphNode
        # time - current clock time in seconds
        if self.endTray is None:
            self.endTray = gu.LinearTrayectory(time, 2, 0.0, 2.0, 0.0, 0.0)
        # Telling OpenGL to use our shader program for textures
        glUseProgram(self.pipelineTexture.shaderProgram)
        goX, goY = self.endTray.get_pos(time)
        endScreen.transform = tr.translate(goX, goY, 0.0)
        sg.drawSceneGraphNode(endScreen, self.pipelineTexture, "transform")

    def drawScene(self, time):
        # Draw elements in order
        # time - current clock time in seconds
        self.drawBackground(time)

        self.drawGameElements()
        
        if self.gameModel.state == gm.G_LOST:
            self.drawEndScreen(time, self.gameoverScreen)
        if self.gameModel.state == gm.G_WIN:
            self.drawEndScreen(time, self.winScreen)

if __name__ == "__main__":
    # Parse game argument
    parser = argparse.ArgumentParser(description='Space-Wars game.')
    parser.add_argument('nEnemies', metavar='N', type=int,
                    help='Number of enemies in the game')
    args = parser.parse_args()

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

    gameModel = gm.GameModel(args.nEnemies, width, height, controller)

    screenDrawer = ScreenDrawer(gameModel, "stars.png", "gameOver.png", "win.png")
    
    while not glfw.window_should_close(window):
        # Using GLFW to check for input events
        glfw.poll_events()

        # Clearing the screen in both, color and depth
        glClear(GL_COLOR_BUFFER_BIT)

        time = glfw.get_time()

        # Update the game state
        gameModel.updateGame(time)

        # Draw the screen
        screenDrawer.drawScene(time)

        # Once the render is done, buffers are swapped, showing only the complete scene.
        glfw.swap_buffers(window)