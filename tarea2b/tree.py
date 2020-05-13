import sys

import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders

import numpy as np

import transformations as tr
import basic_shapes as bs
import scene_graph as sg
import easy_shaders as es
import lighting_shaders as ls

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

class Branch:
    def __init__(self, origin, end, diameter):
        self.origin=origin
        self.end = end
        self.diameter = diameter
        # Calculate parameters and orientation vectors
        self.length = np.sqrt(np.sum((self.end-self.origin)**2))
        self.forward = (self.end - self.origin)/self.length
        
    def get_transform(self):
        # Asumes shape of dimension 1 in every axis and centered in origin
        scale = tr.scale(self.diameter, self.diameter, self.length)

        # Create rotation matrix
        
        vy = np.array([self.forward[2],self.forward[0],self.forward[1]])
        z = np.cross(self.forward,vy)
        up = z/np.linalg.norm(z)
        y = np.cross(up, self.forward)
        side = y/np.linalg.norm(y)
        
        traslation = (self.origin+self.end)/2
        look = np.array([
            [up[0],       side[0],    self.forward[0], traslation[0]],
            [up[1],     side[1],   self.forward[1], traslation[1]],
            [up[2], side[2], self.forward[2], traslation[2]],
            [0,0,0,1]
            ], dtype = np.float32)

        return tr.matmul([ look, scale])

class FractalTree3D:
    def __init__(self, height, split_ang, split_n, decr, rec_level, sides_n, base_diameter, origin=(0,0,0), direction=(0,0,1)):
        self.childs=[]
        # Length of first segment h=l+decr*l+decr^2*l...
        seg_length = height/np.sum([decr**i for i in range(split_n)])
        direction = np.array(direction)
        branch_origin = np.array(origin)
        branch_end = branch_origin + seg_length*direction
        for i in range(split_n-1):
            self.childs.append(Branch(branch_origin,branch_end, base_diameter))
            seg_length = decr*seg_length # Lenght of following segments
            if rec_level > 0: # Add lateral branches
                rotM1 = tr.rotationA(split_ang, np.cross(direction, np.array([1,0,0])))
                branch_rot = 2*np.pi/sides_n
                rotM2 = tr.rotationA(branch_rot, direction)
                branch_dir = np.matmul(direction,rotM1[:3,:3])
                for j in range(sides_n):
                    self.childs.append(FractalTree3D(seg_length, 
                                                    split_ang, 
                                                    split_n, 
                                                    decr, 
                                                    rec_level-1, 
                                                    sides_n,
                                                    base_diameter*0.5,
                                                    branch_end, branch_dir))
                    branch_dir = np.matmul(branch_dir, rotM2[:3,:3])
            branch_origin = branch_end
            branch_end = branch_origin + seg_length*direction
        self.childs.append(Branch(branch_origin, branch_end, base_diameter))

def get_tree_model(tree: FractalTree3D, branch_model: es.GPUShape):
    tree_sg = sg.SceneGraphNode("tree")
    tree_sg.childs = []

    for child in tree.childs:
        if isinstance(child, FractalTree3D):
            tree_sg.childs.append(get_tree_model(child, branch_model))
        else:
            branch = sg.SceneGraphNode("branch")
            branch.transform = child.get_transform()
            branch.childs = [branch_model]
            tree_sg.childs.append(branch)
    return tree_sg

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

    # Create a tree
    tree = FractalTree3D(height=1.0, split_ang=np.pi/3, split_n=2, decr=1, rec_level=2, sides_n=3, base_diameter=0.05)
    # branch model
    branch_model = es.toGPUShape(bs.createColorNormalsCube(0.59,0.29,0.00))
    tree_model = get_tree_model(tree, branch_model)

    gpuAxis = es.toGPUShape(bs.createAxis(7))

    # Using the same view and projection matrices in the whole application
    projection = tr.perspective(45, float(width)/float(height), 0.1, 100)
    
    camera_theta = 0.0
    cam_z = 3
    ltime = 0
    
    while not glfw.window_should_close(window):
        # Using GLFW to check for input events
        glfw.poll_events()
        time = glfw.get_time()
        dt = time-ltime
        ltime = time
        camera_theta += 2.0*dt*(controller.right - controller.left)
        #cam_y += 2.0*dt*(controller.up - controller.down)

        cam_x = 3 * np.sin(camera_theta)
        cam_y = 3 * np.cos(camera_theta)

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

        # TO DO: Explore different parameter combinations to understand their effect!

        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "lightPosition"), -5, -5, 5)
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "viewPosition"), viewPos[0], viewPos[1], viewPos[2])
        glUniform1ui(glGetUniformLocation(phongPipeline.shaderProgram, "shininess"), 100)
        
        glUniform1f(glGetUniformLocation(phongPipeline.shaderProgram, "constantAttenuation"), 0.0001)
        glUniform1f(glGetUniformLocation(phongPipeline.shaderProgram, "linearAttenuation"), 0.03)
        glUniform1f(glGetUniformLocation(phongPipeline.shaderProgram, "quadraticAttenuation"), 0.01)

        glUniformMatrix4fv(glGetUniformLocation(phongPipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(phongPipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        

        sg.drawSceneGraphNode(tree_model, phongPipeline, "model")
        # Once the render is done, buffers are swapped, showing only the complete scene.
        glfw.swap_buffers(window)

    
    glfw.terminate()