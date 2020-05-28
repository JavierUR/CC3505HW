import sys

import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders

import argparse
import numpy as np

import transformations as tr
import basic_shapes as bs
import scene_graph as sg
import easy_shaders as es
import lighting_shaders as ls

import obj_model as ob

HELP_TEXT = """
SPACE: toggle fill or line mode
ENTER: toggle axis
ARROW UP/DOWN: move camera up or down
ARROW LEFT/RIGHT: move camera left or right
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

def create_terrain(width, lenght, spu, fz):
    assert(spu>0)
    w_n = int(width*spu) +1
    dw = width/(w_n-1)
    w0 = -width/2
    l_n = int(lenght*spu) +1
    dl = lenght/(l_n-1)
    l0 = -lenght/2
    vertices = []
    normals = []
    faces = []
    # Constants for normal aproximation
    dw2 = dw/2
    dl2 = dl/2

    for i in range(w_n):
        w = w0 + i*dw
        for j in range(l_n):
            l = l0 + j*dl
            vertices.append([w, l, fz(w,l)])
            # Aproximate normal of vertex by fz
            # using centered difference
            dfdw = (fz(w+dw2,l) - fz(w-dw2,l))/(dw)
            dfdl = (fz(w,l+dl2) - fz(w,l-dl2))/(dl)
            n = np.array([-dfdw,-dfdl,1])
            n = n/np.linalg.norm(n)
            normals.append(n.tolist())
            # Create faces
            if (i < (w_n-1)) and (j< (l_n-1)):
                v = l_n*i + j + 1 # vertex index
                faces.append(
                    [[v,None,v],[v+1,None,v+1],[v+l_n+1,None,v+l_n+1]]
                )
                faces.append(
                    [[v+l_n+1,None,v+l_n+1],[v+l_n,None,v+l_n],[v,None,v]]
                )
    
    return ob.OBJModel(vertices, normals, faces)

if __name__ == "__main__":
    # Initialize glfw
    if not glfw.init():
        sys.exit()

    width = 600
    height = 600

    window = glfw.create_window(width, height, "3D cars via scene graph", None, None)

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

    # Using the same view and projection matrices in the whole application
    projection = tr.perspective(45, float(width)/float(height), 0.1, 100)
    
    camera_theta = 0.0
    camera_phi = np.pi/4
    camera_r = 3
    ltime = 0

    # Create forest
    fz = lambda x,y: 1/(2*np.pi)*np.exp(-(x**2+y**2)/2)
    terrain = create_terrain(4, 4, 4,fz)
    forest = sg.SceneGraphNode("forest")
    forest.childs = [es.toGPUShape(terrain.to_shape((0,0.4,0.4)))]

    while not glfw.window_should_close(window):
        # Using GLFW to check for input events
        glfw.poll_events()
        time = glfw.get_time()
        dt = time-ltime
        ltime = time
        camera_theta -= 2.0*dt*(controller.right - controller.left)
        camera_phi -= 2.0*dt*(controller.up - controller.down)
        camera_phi = np.clip(camera_phi, 0+0.00001, np.pi/2) # view matrix is NaN when phi=0
        #cam_y += 2.0*dt*(controller.up - controller.down)

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

        # Draw Tree
        glUseProgram(phongPipeline.shaderProgram)

        # White light in all components: ambient, diffuse and specular.
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "La"), 1.0, 1.0, 1.0)
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "Ld"), 1.0, 1.0, 1.0)
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "Ls"), 1.0, 1.0, 1.0)

        # Object is barely visible at only ambient. Diffuse behavior is slightly red. Sparkles are white
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "Ka"), 0.2, 0.2, 0.2)
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "Kd"), 0.9, 0.5, 0.5)
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "Ks"), 1.0, 1.0, 1.0)

        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "lightPosition"), -5, -5, 5)
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "viewPosition"), viewPos[0], viewPos[1], viewPos[2])
        glUniform1ui(glGetUniformLocation(phongPipeline.shaderProgram, "shininess"), 100)
        
        glUniform1f(glGetUniformLocation(phongPipeline.shaderProgram, "constantAttenuation"), 0.0001)
        glUniform1f(glGetUniformLocation(phongPipeline.shaderProgram, "linearAttenuation"), 0.03)
        glUniform1f(glGetUniformLocation(phongPipeline.shaderProgram, "quadraticAttenuation"), 0.01)

        glUniformMatrix4fv(glGetUniformLocation(phongPipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(phongPipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        

        sg.drawSceneGraphNode(forest, phongPipeline, "model")
        # Once the render is done, buffers are swapped, showing only the complete scene.
        glfw.swap_buffers(window)

    
    glfw.terminate()