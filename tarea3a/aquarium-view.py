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

h=0.01

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

def find_voxel_volumes(space, Ta,Tb,Tc, voxel_a, voxel_b, voxel_c):
    global h
    volumeA = sg.SceneGraphNode("Fish_A_volume")
    volumeA.childs = []
    volumeB = sg.SceneGraphNode("Fish_A_volume")
    volumeC = sg.SceneGraphNode("Fish_A_volume")

    ta_1, ta_2 = Ta-2, Ta+2
    tb_1, tb_2 = Tb-2, Tb+2
    tc_1, tc_2 = Tc-2, Tc+2
    for i in range(space.shape[0]):
        for j in range(space.shape[1]):
            for k in range(space.shape[2]):
                # Find fish A area
                if ta_1 <= space[i,j,k] <= ta_2:
                    vox = sg.SceneGraphNode("vox_a_{}_{}_{}".format(i,j,k))
                    vox.childs = [voxel_a]
                    vox.transform = tr.translate(i*h, j*h, k*h)
                    volumeA.childs.append(vox)
                # Find fish B area
                elif tb_1 <= space[i,j,k] <= tb_2:
                    vox = sg.SceneGraphNode("vox_b_{}_{}_{}".format(i,j,k))
                    vox.childs = [voxel_b]
                    vox.transform = tr.translate(i*h, j*h, k*h)
                    volumeB.childs.append(vox)
                # Find fish C area
                elif tc_1 <= space[i,j,k] <= tc_2:
                    vox = sg.SceneGraphNode("vox_c_{}_{}_{}".format(i,j,k))
                    vox.childs = [voxel_c]
                    vox.transform = tr.translate(i*h, j*h, k*h)
                    volumeC.childs.append(vox)
    return volumeA, volumeB, volumeC


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
    aq_width = aq_space.shape[0] * h
    aq_lenght = aq_space.shape[1] * h
    aq_height = aq_space.shape[2] * h

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
    gpuVoxelA = es.toGPUShape(bs.createColorNormalsCube(1,0,0))
    voxA = sg.SceneGraphNode("vox_a")
    voxA.childs = [gpuVoxelA]
    voxA.transform = tr.uniformScale(h)

    gpuVoxelB = es.toGPUShape(bs.createColorNormalsCube(0,1,0))
    voxB = sg.SceneGraphNode("vox_b")
    voxB.childs = [gpuVoxelB]
    voxB.transform = tr.uniformScale(h)

    gpuVoxelC = es.toGPUShape(bs.createColorNormalsCube(0,0,1))
    voxC = sg.SceneGraphNode("vox_c")
    voxC.childs = [gpuVoxelC]
    voxC.transform = tr.uniformScale(h)

    fish_volumes = find_voxel_volumes(aq_space, config['t_a'],config['t_b'],config['t_c'],voxA, voxB, voxC)

    # testvox = sg.SceneGraphNode("testvox")
    # testvox.childs = [voxA]
    # testvox.transform = tr.translate(1*h,1*h,1*h)

    # volumeA = sg.SceneGraphNode("Vollume_A")
    # volumeA.childs = [testvox]
    
    scene = sg.SceneGraphNode("Aquarium")
    scene.childs = [fish_volumes[controller.showVolume]]
    scene.transform = tr.translate(aq_width/2, aq_lenght/2,0)

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

        if controller.showAxis:
            glUseProgram(mvpPipeline.shaderProgram)
            glUniformMatrix4fv(glGetUniformLocation(mvpPipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
            glUniformMatrix4fv(glGetUniformLocation(mvpPipeline.shaderProgram, "view"), 1, GL_TRUE, view)
            glUniformMatrix4fv(glGetUniformLocation(mvpPipeline.shaderProgram, "model"), 1, GL_TRUE, tr.identity())
            mvpPipeline.drawShape(gpuAxis, GL_LINES)

        # Draw aquarium
        glUseProgram(phongPipeline.shaderProgram)

        # White light in all components: ambient, diffuse and specular.
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "La"), 1.0, 1.0, 1.0)
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "Ld"), 1.0, 1.0, 1.0)
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "Ls"), 1.0, 1.0, 1.0)

        # Object is barely visible at only ambient. Diffuse behavior is slightly red. Sparkles are white
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "Ka"), 0.3, 0.3, 0.3)
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "Kd"), 0.9, 0.5, 0.5)
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "Ks"), 0.05, 0.05, 0.05)

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