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

class Branch:
    def __init__(self, origin, end, side, diameter):
        self.origin=origin
        self.end = end
        self.diameter = diameter
        # Calculate parameters and orientation vectors
        self.length = np.sqrt(np.sum((self.end-self.origin)**2))
        self.forward = (self.end - self.origin)/self.length
        self.side = side
        
    def get_transform(self):
        # Asumes shape of dimension 1 in every axis and centered in origin
        scale = tr.scale(self.diameter, self.diameter, self.length)

        # Create rotation matrix
        
        up = np.cross(self.side,self.forward)
        up = up/np.linalg.norm(up)
        
        traslation = (self.origin+self.end)/2
        look = np.array([
            [up[0],       self.side[0],    self.forward[0], traslation[0]],
            [up[1],     self.side[1],   self.forward[1], traslation[1]],
            [up[2], self.side[2], self.forward[2], traslation[2]],
            [0,0,0,1]
            ], dtype = np.float32)

        return tr.matmul([ look, scale])

class FractalTree3D:
    def __init__(self, height, split_ang, split_n, decr, rec_level, sides_n, 
                base_diameter, origin=(0,0,0), direction=(0,0,1), side=(0,1,0)):
        self.childs=[]
        # normalize direction and side vectors
        direction = np.array(direction)/np.linalg.norm(direction)
        up = np.cross(side, direction)
        side = np.cross(direction, up)
        side = side/np.linalg.norm(side)
        # Create trunk
        trunk_origin = np.array(origin)
        trunk_end = trunk_origin + height*direction
        self.childs.append(Branch(trunk_origin,trunk_end, side, base_diameter))
        # Length of first segment h=l+decr*l+decr^2*l...
        seg_length = height/np.sum([decr**i for i in range(split_n)])
        # Create lateral branches
        branch_origin = trunk_origin + seg_length*direction
        for _ in range(split_n-1):
            seg_length = decr*seg_length # Length of following segments
            if rec_level > 0: # Add lateral branches
                rotM1 = tr.rotationA(split_ang, side)
                branch_rot = 2*np.pi/sides_n
                rotM2 = tr.rotationA(branch_rot, direction)
                branch_dir = np.matmul(direction,rotM1[:3,:3])
                branch_side = np.matmul(side,rotM1[:3,:3])
                for j in range(sides_n):
                    self.childs.append(FractalTree3D(seg_length, 
                                                    split_ang, 
                                                    split_n, 
                                                    decr, 
                                                    rec_level-1, 
                                                    sides_n,
                                                    base_diameter*0.5,
                                                    branch_origin, 
                                                    branch_dir, branch_side))
                    branch_dir = np.matmul(branch_dir, rotM2[:3,:3])
                    branch_side = np.matmul(branch_side, rotM2[:3,:3])
            branch_origin += seg_length*direction

def get_tree_model_sg(tree: FractalTree3D, branch_model: es.GPUShape):
    tree_sg = sg.SceneGraphNode("tree")
    tree_sg.childs = []

    for child in tree.childs:
        if isinstance(child, FractalTree3D):
            tree_sg.childs.append(get_tree_model_sg(child, branch_model))
        else:
            branch = sg.SceneGraphNode("branch")
            branch.transform = child.get_transform()
            branch.childs = [branch_model]
            tree_sg.childs.append(branch)
    return tree_sg

def get_tree_model(tree: FractalTree3D, branch_shape: ob.OBJModel) -> ob.OBJModel:
    obj_list = []

    for child in tree.childs:
        if isinstance(child, FractalTree3D):
            obj_list.append(get_tree_model(child, branch_shape))
        else:
            t_M = child.get_transform()
            obj_list.append(branch_shape.transform(t_M))

    tree_model = obj_list[0]
    for i in range(1,len(obj_list)):
        tree_model.join(obj_list[i])
    
    return tree_model

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description='3D fractal tree generator.')
    parser.add_argument('filename', metavar='Filename', type=str,
                    help='Name for the generated model file')
    parser.add_argument('split_ang', metavar='Angle', type=float,
                    help='Angle of branch separation in degrees')
    parser.add_argument('split_n', metavar='Separations', type=int,
                    help='Number of separation in the tree')
    parser.add_argument('decr', metavar='Decrement', type=float,
                    help='Percentage to make the branches smaller as the tree grows up')
    parser.add_argument('rec_level', metavar='Depth', type=int,
                    help='Depth or recursion level of the tree branches')
    parser.add_argument('sides_n', metavar='Sides', type=int,
                    help='Number of braches at the sides of the tree. (Minimum 1)')
    parser.add_argument('base_diameter', metavar='Diameter', type=float,
                    help='Tree trunk diameter')
    args = parser.parse_args()

    assert(args.split_n > 0)
    assert(0.0 <= args.decr<= 1.0)
    assert(args.rec_level >= 0)
    assert(args.sides_n > 1)
    assert(args.base_diameter > 0)
    
    # Initialize glfw
    if not glfw.init():
        sys.exit()

    print("Generating tree ...")
    # Create a tree
    tree = FractalTree3D(height=1.0, split_ang=np.deg2rad(args.split_ang), 
                        split_n=args.split_n, decr=args.decr, rec_level=args.rec_level, 
                        sides_n=args.sides_n, base_diameter=args.base_diameter)
    # branch model
    branch_model = ob.cilinderOBJ(num_sides=8)
    tree_obj = get_tree_model(tree, branch_model)
    tree_obj.to_file(args.filename)

    print("Tree ready!")

    width = 600
    height = 600

    window = glfw.create_window(width, height, "Tree Generator", None, None)

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

    # Generate tree gpu shape
    tree_shape = tree_obj.to_shape((0.59,0.29,0.00))
    #tree_gpu = es.toGPUShape(tree_obj.to_shape((0.59,0.29,0.00)))
    tree_gpu = es.toGPUShape(tree_shape)
    tree_model = sg.SceneGraphNode("tree")
    tree_model.childs = [tree_gpu
    ]
    gpuAxis = es.toGPUShape(bs.createAxis(7))

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
        

        sg.drawSceneGraphNode(tree_model, phongPipeline, "model")
        # Once the render is done, buffers are swapped, showing only the complete scene.
        glfw.swap_buffers(window)

    
    glfw.terminate()