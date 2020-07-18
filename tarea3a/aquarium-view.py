import argparse
import json
import sys
import matplotlib.pyplot as plt
import numpy as np

import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders

import scene_graph as sg
import transformations as tr
import basic_shapes as bs
import easy_shaders as es
import lighting_shaders as ls

h=0.04

HELP_TEXT = """
SPACE: toggle fill or line mode
ENTER: toggle axis
ARROW UP/DOWN: move camera up or down
ARROW LEFT/RIGHT: move camera left or right
W: zoom in
S: Zoom out
"""

# A class to store the application control
class Controller:
    def __init__(self):
        self.fillPolygon = True
        self.showAxis = True
        self.up = False
        self.down = False
        self.right = False
        self.left = False
        self.zoomIn = False
        self.zoomOut = False
        self.showVolume = 0


# we will use the global controller as communication with the callback function
controller = Controller()

def on_key(window, key, scancode, action, mods):
    global controller

    if key == glfw.KEY_RIGHT:
        controller.right = (action == glfw.PRESS or action == glfw.REPEAT)
    elif key == glfw.KEY_LEFT:
        controller.left = (action == glfw.PRESS or action == glfw.REPEAT)
    elif key == glfw.KEY_UP:
        controller.up = (action == glfw.PRESS or action == glfw.REPEAT)
    elif key == glfw.KEY_DOWN:
        controller.down = (action == glfw.PRESS or action == glfw.REPEAT)
    elif key == glfw.KEY_W:
        controller.zoomIn = (action == glfw.PRESS or action == glfw.REPEAT)
    elif key == glfw.KEY_S:
        controller.zoomOut = (action == glfw.PRESS or action == glfw.REPEAT)
    elif key == glfw.KEY_A:
        if action == glfw.PRESS:
            controller.showVolume = 0
    elif key == glfw.KEY_B:
        if action == glfw.PRESS:
            controller.showVolume = 1
    elif key == glfw.KEY_C:
        if action == glfw.PRESS:
            controller.showVolume = 2
    
    elif key == glfw.KEY_SPACE:
        if action == glfw.PRESS:
            controller.fillPolygon = not controller.fillPolygon

    elif key == glfw.KEY_ENTER:
        if action == glfw.PRESS:
            controller.showAxis = not controller.showAxis

    elif key == glfw.KEY_ESCAPE:
        sys.exit()

    else:
        print('Unknown key')

class VoxelVolume(object):
    def __init__(self, voxel_size, color):
        self.h2 = voxel_size/2
        self.r = color[0]
        self.g = color[1]
        self.b = color[2]
        self.vertices = []
        self.indices = []
        self.vox_count = 0

    def _get_voxel(self, x, y, z):
        # Defining the location and colors of each vertex  of the shape
        vertices = [
        #   positions         colors   normals
        # Z+
            x-self.h2, y-self.h2,  z+self.h2, self.r, self.g, self.b, 0,0,1,
            x+self.h2, y-self.h2,  z+self.h2, self.r, self.g, self.b, 0,0,1,
            x+self.h2, y+self.h2,  z+self.h2, self.r, self.g, self.b, 0,0,1,
            x-self.h2, y+self.h2,  z+self.h2, self.r, self.g, self.b, 0,0,1,

        # Z-
            x-self.h2, y-self.h2, z-self.h2, self.r, self.g, self.b, 0,0,-1,
            x+self.h2, y-self.h2, z-self.h2, self.r, self.g, self.b, 0,0,-1,
            x+self.h2, y+self.h2, z-self.h2, self.r, self.g, self.b, 0,0,-1,
            x-self.h2, y+self.h2, z-self.h2, self.r, self.g, self.b, 0,0,-1,
            
        # X+
            x+self.h2, y-self.h2, z-self.h2, self.r, self.g, self.b, 1,0,0,
            x+self.h2, y+self.h2, z-self.h2, self.r, self.g, self.b, 1,0,0,
            x+self.h2, y+self.h2, z+self.h2, self.r, self.g, self.b, 1,0,0,
            x+self.h2, y-self.h2, z+self.h2, self.r, self.g, self.b, 1,0,0,
    
        # X-
            x-self.h2, y-self.h2, z-self.h2, self.r, self.g, self.b, -1,0,0,
            x-self.h2, y+self.h2, z-self.h2, self.r, self.g, self.b, -1,0,0,
            x-self.h2, y+self.h2, z+self.h2, self.r, self.g, self.b, -1,0,0,
            x-self.h2, y-self.h2, z+self.h2, self.r, self.g, self.b, -1,0,0,

        # Y+
            x-self.h2, y+self.h2, z-self.h2, self.r, self.g, self.b, 0,1,0,
            x+self.h2, y+self.h2, z-self.h2, self.r, self.g, self.b, 0,1,0,
            x+self.h2, y+self.h2, z+self.h2, self.r, self.g, self.b, 0,1,0,
            x-self.h2, y+self.h2, z+self.h2, self.r, self.g, self.b, 0,1,0,

        # Y-
            x-self.h2, y-self.h2, z-self.h2, self.r, self.g, self.b, 0,-1,0,
            x+self.h2, y-self.h2, z-self.h2, self.r, self.g, self.b, 0,-1,0,
            x+self.h2, y-self.h2, z+self.h2, self.r, self.g, self.b, 0,-1,0,
            x-self.h2, y-self.h2, z+self.h2, self.r, self.g, self.b, 0,-1,0
            ]

        # Defining connections among vertices
        # We have a triangle every 3 indices specified
        indices = np.array([
            0, 1, 2, 2, 3, 0, # Z+
            7, 6, 5, 5, 4, 7, # Z-
            8, 9,10,10,11, 8, # X+
            15,14,13,13,12,15, # X-
            19,18,17,17,16,19, # Y+
            20,21,22,22,23,20]) # Y-
        return vertices, indices

    def add_voxel(self, x,y,z):
        vox_vert, vox_ind = self._get_voxel(x,y,z)
        self.vertices.extend(vox_vert)
        self.indices.extend((vox_ind + 24*self.vox_count).tolist())
        self.vox_count +=1

    def to_shape(self):
        return bs.Shape(self.vertices, self.indices)


def find_voxel_volumes(space, Ta,Tb,Tc, voxel_a_color, voxel_b_color, voxel_c_color):
    global h
    volumeA = VoxelVolume(voxel_size=h, color=voxAcolor)
    volumeB = VoxelVolume(voxel_size=h, color=voxBcolor)
    volumeC = VoxelVolume(voxel_size=h, color=voxCcolor)
    ta_1, ta_2 = Ta-2, Ta+2
    tb_1, tb_2 = Tb-2, Tb+2
    tc_1, tc_2 = Tc-2, Tc+2
    # Search for adequate temperature in the water
    for i in range(1, space.shape[0]-1):
        for j in range(1, space.shape[1]-1):
            for k in range(1, space.shape[2]-1):
                # Find fish A area
                if ta_1 <= space[i,j,k] <= ta_2:
                    volumeA.add_voxel(i*h, j*h, k*h)
                # Find fish B area
                elif tb_1 <= space[i,j,k] <= tb_2:
                    volumeB.add_voxel(i*h, j*h, k*h)
                # Find fish C area
                elif tc_1 <= space[i,j,k] <= tc_2:
                    volumeC.add_voxel(i*h, j*h, k*h)

    volumeA_scene = sg.SceneGraphNode("Fish_A_volume")
    vol_a_shape = volumeA.to_shape()
    volumeA_scene.childs = [es.toGPUShape(vol_a_shape)]

    volumeB_scene = sg.SceneGraphNode("Fish_A_volume")
    vol_b_shape = volumeB.to_shape()
    volumeB_scene.childs = [es.toGPUShape(vol_b_shape)]

    volumeC_scene = sg.SceneGraphNode("Fish_A_volume")
    vol_c_shape = volumeC.to_shape()
    volumeC_scene.childs = [es.toGPUShape(vol_c_shape)]

    return volumeA_scene, volumeB_scene, volumeC_scene

def createAquarium(width, lenght, height, r,g,b):
    w2 = width/2
    l2 = lenght/2
    # Defining the location and colors of each vertex  of the shape
    vertices = [
    #    positions        colors
        # Z-
        -w2,  -l2,   0.0, r, g, b,
         w2,  -l2,   0.0, r, g, b,
         w2,   l2,   0.0, r, g, b,
        -w2,   l2,   0.0, r, g, b,
        # Z+
        -w2,  -l2,   height, r, g, b,
         w2,  -l2,   height, r, g, b,
         w2,   l2,   height, r, g, b,
        -w2,   l2,   height, r, g, b,
        ]

    # This shape is meant to be drawn with GL_LINES,
    # i.e. every 2 indices, we have 1 line.
    indices = [
         # Z-
         0, 1,
         1, 2,
         2, 3,
         3, 0,
         # Z+
         4, 5,
         5, 6,
         6, 7,
         7, 4,
         # sides
         0, 4,
         1, 5,
         2, 6,
         3, 7
         ]

    return bs.Shape(vertices, indices)

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description='Aquarium View.')
    parser.add_argument('filename', metavar='Setup_File', type=str,
                    help='(string) Name of the view setup file')
    args = parser.parse_args()
    """ Load json parameters
        filename: File to read aquarium temperature
        t_a :     Temperature prefered by fish A
        t_b :     Temperature prefered by fish B
        t_c :     Temperature prefered by fish C
        n_a :     Number of type A fish
        n_b :     Number of type B fish
        n_c :     Number of type C fish

    """
    with open(args.filename, 'r') as setup_file:
        config = json.load(setup_file)
    print(config)

    aq_space = np.load(config["filename"])
    aq_width  = (aq_space.shape[0]-1) * h
    aq_lenght = (aq_space.shape[1]-1) * h
    aq_height = (aq_space.shape[2]-1) * h

    # Initialize glfw
    if not glfw.init():
        sys.exit()

    width = 600
    height = 600

    window = glfw.create_window(width, height, "Forest Generator", None, None)

    if not window:
        glfw.terminate()
        sys.exit()

    print(HELP_TEXT)

    glfw.make_context_current(window)

    # Connecting the callback function 'on_key' to handle keyboard events
    glfw.set_key_callback(window, on_key)

    # Assembling the shader program (pipeline) with both shaders
    mvpPipeline = es.SimpleModelViewProjectionShaderProgram()
    phongPipeline = ls.SimplePhongShaderProgram()

    # Setting up the clear screen color
    glClearColor(0.85, 0.85, 0.85, 1.0)

    # As we work in 3D, we need to check which part is in front,
    # and which one is at the back
    glEnable(GL_DEPTH_TEST)

    gpuAxis = es.toGPUShape(bs.createAxis(7))

    # Define fish areas
    voxAcolor = (1,0,0)
    voxBcolor = (0,1,0)
    voxCcolor = (0,0,1)

    fish_volumes = find_voxel_volumes(aq_space, config['t_a'],config['t_b'],config['t_c'],voxAcolor, voxBcolor, voxCcolor)

    vols = VoxelVolume(h, (1,1,0))
    vols.add_voxel(0,0,0)

    # Create aquarium
    gpuAq = es.toGPUShape(createAquarium(aq_width, aq_lenght, aq_height,0,0,0))
    
    scene = sg.SceneGraphNode("Aquarium")
    scene.childs = [fish_volumes[controller.showVolume]]
    scene.transform = tr.translate(-aq_width/2, -aq_lenght/2,0)

    # Using the same view and projection matrices in the whole application
    projection = tr.perspective(45, float(width)/float(height), 0.1, 100)
    
    camera_theta = 0.0
    camera_phi = np.pi/4
    camera_r = 3
    ltime = 0
    
    while not glfw.window_should_close(window):
        # Using GLFW to check for input events
        glfw.poll_events()
        time = glfw.get_time()
        dt = time-ltime
        ltime = time
        camera_theta -= 2.0*dt*(controller.right - controller.left)
        camera_phi -= 2.0*dt*(controller.up - controller.down)
        camera_phi = np.clip(camera_phi, 0+0.00001, np.pi/2) # view matrix is NaN when phi=0
        camera_r += 2.0*dt*(controller.zoomOut - controller.zoomIn)
        camera_r = np.clip(camera_r, 0.7, 4)

        cam_x = camera_r * np.sin(camera_phi) * np.sin(camera_theta)
        cam_y = camera_r * np.sin(camera_phi) * np.cos(camera_theta)
        cam_z = camera_r * np.cos(camera_phi)

        viewPos = np.array([cam_x,cam_y,cam_z])

        view = tr.lookAt(
            viewPos,
            np.array([0,0,0]),
            np.array([0,0,1])
        )

        # Clearing the screen in both, color and depth
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Filling or not the shapes depending on the controller state
        if (controller.fillPolygon):
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        glUseProgram(mvpPipeline.shaderProgram)
        glUniformMatrix4fv(glGetUniformLocation(mvpPipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(mvpPipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(mvpPipeline.shaderProgram, "model"), 1, GL_TRUE, tr.identity())
        mvpPipeline.drawShape(gpuAq, GL_LINES)
        if controller.showAxis:
            mvpPipeline.drawShape(gpuAxis, GL_LINES)

        # Draw aquarium
        glUseProgram(phongPipeline.shaderProgram)

        # White light in all components: ambient, diffuse and specular.
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "La"), 1.0, 1.0, 1.0)
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "Ld"), 1.0, 1.0, 1.0)
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "Ls"), 1.0, 1.0, 1.0)

        # Object is barely visible at only ambient. Diffuse behavior is slightly red. Sparkles are white
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "Ka"), 0.3, 0.3, 0.3)
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "Kd"), 0.9, 0.9, 0.9)
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "Ks"), 1., 1., 1.)

        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "lightPosition"), -5, -5, 5)
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "viewPosition"), viewPos[0], viewPos[1], viewPos[2])
        glUniform1ui(glGetUniformLocation(phongPipeline.shaderProgram, "shininess"), 100)
        
        glUniform1f(glGetUniformLocation(phongPipeline.shaderProgram, "constantAttenuation"), 0.0001)
        glUniform1f(glGetUniformLocation(phongPipeline.shaderProgram, "linearAttenuation"), 0.03)
        glUniform1f(glGetUniformLocation(phongPipeline.shaderProgram, "quadraticAttenuation"), 0.01)

        glUniformMatrix4fv(glGetUniformLocation(phongPipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(phongPipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        
        # Volume to show
        scene.childs = [fish_volumes[controller.showVolume]]
        sg.drawSceneGraphNode(scene, phongPipeline, "model")

        # Once the render is done, buffers are swapped, showing only the complete scene.
        glfw.swap_buffers(window)

    glfw.terminate()