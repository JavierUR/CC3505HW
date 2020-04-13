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

def create_background(filename):
    # Load background image
    gpuStars = es.toGPUShape(bs.createTextureQuad(filename), GL_REPEAT, GL_LINEAR)

    #Create two background copies to have a scrolling effect
    background = sg.SceneGraphNode("background")
    background.transform = tr.scale(2, 2, 1)
    background.childs = [gpuStars]

    background2 = sg.SceneGraphNode("background2")
    background2.transform = tr.matmul([tr.scale(2,2,1),tr.translate(0,-1,0)])
    background2.childs = [gpuStars]

    # Node to control vertical movement of the two backgrounds objects
    backgroundVertical = sg.SceneGraphNode("backgroundVertical")
    backgroundVertical.childs = [background, background2]
    return backgroundVertical

def create_gameover_screen(filename):
    # Load background image
    gpuGameOver = es.toGPUShape(bs.createTextureQuad(filename), GL_REPEAT, GL_LINEAR)

    #Create two background copies to have a scrolling effect
    gameover = sg.SceneGraphNode("gameover")
    gameover.transform = tr.scale(2, 2, 1)
    gameover.childs = [gpuGameOver]

    # Node to control vertical movement of the two gameovers objects
    gameoverVertical = sg.SceneGraphNode("gameoverVertical")
    gameoverVertical.childs = [gameover]
    return gameoverVertical

def enemy_wing_shape(r,g,b):
    # Defining locations and colors for each vertex of the shape    
    vertices = [
    #   positions        colors
         0.0, -0.5, 0.0,  r, g, b,
         0.5, 0.5, 0.0,  r, g, b,
         0.0,  1.25, 0.0,  r, g, b]

    # Defining connections among vertices
    # We have a triangle every 3 indices specified
    indices = [
         0, 1, 2]

    return bs.Shape(vertices, indices)

def create_enemy():
    # Generate enemy model
    # Body
    gpuBody = es.toGPUShape(bs.createColorQuad(0.5, 0, 0.38))

    # Wing
    gpuWing = es.toGPUShape(enemy_wing_shape(0.0, 0.38, 0.5))

    enemyBody = sg.SceneGraphNode("body")
    enemyBody.childs = [gpuBody]

    enemyWing1 = sg.SceneGraphNode("wing1")
    enemyWing1.transform = tr.translate(0.5, 0, 0)
    enemyWing1.childs = [gpuWing]

    enemyWing2 = sg.SceneGraphNode("wing2")
    enemyWing2.transform = tr.matmul([tr.translate(-0.5, 0, 0),tr.scale(-1, 1, 1)])
    enemyWing2.childs = [gpuWing]

    enemy = sg.SceneGraphNode("enemyModel")
    enemy.transform = tr.uniformScale(0.08)
    enemy.childs = [enemyBody, enemyWing1, enemyWing2]

    return enemy

def player_body_shape(r,g,b):
    # Defining locations and colors for each vertex of the shape    
    vertices = [
    #   positions        colors
        -0.45, -0.525, 0.0,  r, g, b,
         0.45, -0.525, 0.0,  r, g, b,
         0.0,  0.75,0.0,  r, g, b]

    # Defining connections among vertices
    # We have a triangle every 3 indices specified
    indices = [
         0, 1, 2]

    return bs.Shape(vertices, indices)

def player_lower_wing_shape(r,g,b):
    # Defining locations and colors for each vertex of the shape    
    vertices = [
    #   positions        colors
        -1.0, -0.5, 0.0,  r, g, b,
         1.0, -0.5, 0.0,  r, g, b,
         0.0,  0.1, 0.0,  r, g, b]

    # Defining connections among vertices
    # We have a triangle every 3 indices specified
    indices = [
         0, 1, 2]

    return bs.Shape(vertices, indices)

def player_upper_wing_shape(r,g,b):
    # Defining locations and colors for each vertex of the shape    
    vertices = [
    #   positions        colors
         0.0, 0.425, 0.0,  r, g, b,
         0.4, 0.625, 0.0,  r, g, b,
        -0.4, 0.625, 0.0,  r, g, b]

    # Defining connections among vertices
    # We have a triangle every 3 indices specified
    indices = [
         0, 1, 2]

    return bs.Shape(vertices, indices)

def create_player():
    # Generate player model
    # Body
    gpuBody = es.toGPUShape(player_body_shape(0.8,0,0.07))

    # WingUp
    gpuWingUp = es.toGPUShape(player_upper_wing_shape(0.427,0.447,0.458))

    # WingDown
    gpuWingDown = es.toGPUShape(player_lower_wing_shape(0.427,0.447,0.458))

    playerBody = sg.SceneGraphNode("body")
    playerBody.childs = [gpuBody]

    playerUpWing = sg.SceneGraphNode("wing1")
    playerUpWing.childs = [gpuWingUp]

    playerDownWing = sg.SceneGraphNode("wing2")
    playerDownWing.childs = [gpuWingDown]

    player = sg.SceneGraphNode("playerModel")
    player.transform = tr.uniformScale(0.1)
    player.childs = [playerUpWing, playerDownWing, playerBody]

    return player

def create_shot(r,g,b):
    gpuShot = es.toGPUShape(bs.createColorQuad(r,g,b))

    shot = sg.SceneGraphNode("shot")
    shot.transform = tr.uniformScale(0.02)
    shot.childs = [gpuShot]

    return shot

def create_explosion():
    # Ship explosion model
    r,g,b = (0.95,0.4,0.0)
    # Defining locations and colors for each vertex of the shape    
    vertices = [
    #   positions        colors
        -0.5, -0.5, 0.0,  r, g, b,
         0.5, -0.5, 0.0,  r, g, b,
         0.0,  0.5, 0.0,  r, g, b,
         0.0, -0.75, 0.0,  r, g, b,
         0.5, 0.25, 0.0,  r, g, b,
        -0.5, 0.25, 0.0,  r, g, b]

    # Defining connections among vertices
    # We have a triangle every 3 indices specified
    indices = [
         0, 1, 2,
         3, 4, 5]

    gpuExplosion = es.toGPUShape(bs.Shape(vertices, indices))

    explosion =sg.SceneGraphNode("explosionModel")
    explosion.transform = tr.matmul([tr.translate(0.0,0.02,0.0),tr.uniformScale(0.15)])
    explosion.childs = [gpuExplosion]

    return explosion
