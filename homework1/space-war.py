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
    right = False
    left = False
    up = False
    down = False
    fire = False
    pass

# A class to manage game state
class GameModel:
    def __init__(self, enemies, screenWidht, screenHeight, controller):
        # Start clock
        self.ltime = 0.0
        # reference to the game controller
        self.controller = controller
        # Create game scene
        self.gameScene = sg.SceneGraphNode("gameScene")
        self.gameScene.transform = tr.scale(screenHeight/screenWidht,1.0,1.0)

        # Load game models
        self.enemyModel = gs.createEnemy()
        self.playerModel = gs.createPlayer()
        self.playerShotModel = gs.createShot(0.8,0.4,0.0)
        self.enemyShotModel = gs.createShot(0.4,0.8,0.0)

        # Spawn player
        self.playerX = 0.0
        self.playerY = -0.75
        self.player = sg.SceneGraphNode("Player")
        self.player.transform = tr.translate(self.playerX, self.playerY, 0.0)
        self.player.childs = [self.playerModel]

        self.playerSpeed = 1.0

    def movePlayer(self, dt):
        if (self.controller.right or self.controller.left) and \
                (self.controller.up or self.controller.down):
            vp = self.playerSpeed / np.sqrt(2)
        else:
            vp = self.playerSpeed
        self.playerX += dt*vp*(self.controller.right - self.controller.left )
        self.playerY += dt*vp*(self.controller.up - self.controller.down )

    def updateScene(self, time):
        dt = time - self.ltime
        self.ltime = time
        # Update player position
        self.movePlayer(dt)
        self.player.transform = tr.translate(self.playerX, self.playerY, 0.0)


        enemy1 = sg.SceneGraphNode("enemy1")
        enemy1.childs = [self.enemyModel]

        

        testShot = sg.SceneGraphNode("testShot")
        testShot.transform = tr.translate(0.0,-0.2,0.0)
        testShot.childs = [self.playerShotModel]

        self.gameScene.childs = [self.player, enemy1, testShot]
        #print(sg.findPosition(player,"Player"))
        return self.gameScene

    
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
    
    background = gs.createBackground("stars.png")

    gameModel = GameModel(10, width, height, controller)
    
    while not glfw.window_should_close(window):
        # Using GLFW to check for input events
        glfw.poll_events()

        # Clearing the screen in both, color and depth
        glClear(GL_COLOR_BUFFER_BIT)

        time = glfw.get_time()

        #Draw background
        # Telling OpenGL to use our shader program for textures
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