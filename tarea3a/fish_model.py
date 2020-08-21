import basic_shapes as bs
import scene_graph as sg
import transformations as tr
import numpy as np

def fish_body(lenght, height, r, g, b):
    # Function to create a fish body shape
    # lenght - Lenght of the body
    # height - Height of the body
    # r,g,b - Color of the body
    # return - Fish body Shape
    vertices = [
        -lenght/2, 0.0, 0.0,       r, g, b,
        -lenght/6, 0.0, -height/2, r, g, b,
        lenght/2,  0.0, 0.0,       r, g, b,
        -lenght/6, 0.0, height/2,  r, g, b
    ]

    indices = [
        0,1,3,
        1,2,3
    ]

    return bs.Shape(vertices, indices)

def fish_fin(lenght, height, r, g, b):
    # Function to create a fish fin shape
    # lenght - Lenght of the fin
    # height - Height of the fin
    # r,g,b - Color of the fin
    # return - Fish fin Shape
    vertices = [
        0.0,    0.0,  0.0,          r, g, b,
        lenght, 0.0, -height/2, r, g, b,
        lenght, 0.0,  height/2,  r, g, b
    ]

    indices = [
        0,1,2
    ]

    return bs.Shape(vertices, indices)

def make_fish(body_ratio, fin_ratio, size, r, g, b):
    # Function to create a fish
    # body_ratio - Ratio between body lenght and height
    # fin_ratio  - Ratio between fin lenght and height
    # size - Fish lenght size
    # r,g,b - Color of the body
    # return - Fish body Shape,Fish body Shape and transform matrix between body and fin 
    body_shape = fish_body(size, size/body_ratio, r, g, b)
    fin_shape = fish_fin(0.25*size, 0.25*size/fin_ratio, 0.8*r, 0.8*g, 0.8*b)

    return body_shape, fin_shape, tr.translate(size/2,0,0)

# Class to manage a single fish
class Fish(object):
    def __init__(self, rotFrec, gpuBody, gpuFin, finBodyTR, posTR):
        # rotFrec - Frecuency of the fin movement
        # gpuBody - Fish body gpu object
        # gpuFin  - Fish fin gpu object
        # finBodyTR - Transform between body and fin
        # posTR - Fish position tranform
        self.fin_rot = sg.SceneGraphNode("fin_rot")
        self.fin_rot.childs = [gpuFin]
        fin_pos = sg.SceneGraphNode("fin_pos")
        fin_pos.transform = finBodyTR
        fin_pos.childs = [self.fin_rot]
        body_scene = sg.SceneGraphNode("body")
        body_scene.childs = [gpuBody]
        self.fishScene = sg.SceneGraphNode("fish")
        self.fishScene.childs = [body_scene, fin_pos]
        self.fishScene.transform = posTR
        # Fin movement
        self.rotFrec = rotFrec
        self.phase = 2*np.pi*np.random.random()

    def update(self,time):
        # Method to update fin angle
        # time - Current time
        theta = np.cos(self.rotFrec*time + self.phase)
        self.fin_rot.transform = tr.rotationZ(theta)
