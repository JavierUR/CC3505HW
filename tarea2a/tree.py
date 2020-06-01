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
SPACE: Toggle fill or line mode
ENTER: Toggle axis
ARROW UP/DOWN: Move camera up or down
ARROW LEFT/RIGHT: Move camera left or right
W: Zoom in
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

# A class to manage branches position and orientation
class Branch:
    def __init__(self, origin, end, side, diameter):
        # origin -  branch origin 3d point
        # end - branch end 3d point
        # side - 3D vector pointing to the side of the branch
        # diameter - diameter of the branch
        self.origin=origin
        self.end = end
        self.diameter = diameter
        # Calculate parameters and orientation vectors
        self.length = np.sqrt(np.sum((self.end-self.origin)**2))
        self.forward = (self.end - self.origin)/self.length
        self.side = side
        
    def get_transform(self):
        # return -  A matrix tranform for the branch model
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
    
    def get_leaf_transform(self):
        # return - A matrix tranform for the leaf model
        # Asumes shape of dimension 1 in every axis and centered in origin
        scale = tr.scale(8*self.diameter, 8*self.diameter, self.length)

        # Create rotation matrix
        
        up = np.cross(self.side,self.forward)
        up = up/np.linalg.norm(up)
        
        traslation = self.end
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
        # height - height of the tree
        # split_ang - Angle of the branches
        # split_n - Number of separation in the trunk where branches start
        # decr - Factor to reduce branches as the tree grows
        # rec_level - Fractal recursion level
        # sides_n - Number of branch repetition on the sides
        # base_diameter - Diameter of the trunk
        # origin - Tree origin 3D point
        # direction - Tree direction 3D vector
        # side - Tree side 3D vector
        # split_ang
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
        seg_length = height/np.sum([decr**i for i in range(split_n+1)])
        # Create lateral branches
        branch_origin = trunk_origin + seg_length*direction
        for _ in range(split_n):
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


def get_tree_model(tree: FractalTree3D, branch_model: ob.OBJModel,
                    leaf_model: ob.OBJModel) -> ob.OBJModel:
    # Creaates a 3d obj model from a fractal tree and 
    # obj model for the branches and leaves
    # tree - FractalTree3D to use
    # branch_model - OBJ model for the branches and trunk
    # leaves_model - OBJ model for the leaves
    branches_list = []
    leaf_list = []

    for child in tree.childs:
        if isinstance(child, FractalTree3D):
            branches, leaves = get_tree_model(child, branch_model, leaf_model)
            branches_list.append(branches)
            leaf_list.append(leaves)
        else:
            t_M = child.get_transform()
            branches_list.append(branch_model.transform(t_M))
            # Add leaves at the last recursion level
            if len(tree.childs) == 1:
                l_M = child.get_leaf_transform()
                leaf_list.append(leaf_model.transform(l_M))

    tree_model = branches_list[0]
    leaves_model = leaf_list[0]
    for i in range(1,len(branches_list)):
        tree_model.join(branches_list[i])
    for leaf in leaf_list:
        leaves_model.join(leaf)
    
    return tree_model, leaves_model

def get_tree_model_sg(tree_obj: ob.OBJModel, leaves_obj: ob.OBJModel,
                        tree_color: tuple, leaves_color: tuple) -> sg.SceneGraphNode:
    # Generate a scenegraph node of the tree with leaves
    # tree_obj - Tree obj model
    # leaves_obj - Tree leaves obj model
    # tree_color - Color tuple for the Tree
    # leaves_color - Color tuple for the leaves
    # return - Tree ScenGraphNode

    # Convert obj models to shapes
    tree_shape = tree_obj.to_shape(tree_color)
    leaves_shape = leaves_obj.to_shape(leaves_color)
    # Create gpu models
    tree_gpu = es.toGPUShape(tree_shape)
    leaves_gpu = es.toGPUShape(leaves_shape)
    # Create tree scene graph node
    tree_node = sg.SceneGraphNode("tree")
    trunk_node = sg.SceneGraphNode("Trunk_branches")
    trunk_node.childs = [tree_gpu]
    leaves_node = sg.SceneGraphNode("leaves")
    leaves_node.childs = [leaves_gpu]
    tree_node.childs = [trunk_node, leaves_node]

    return tree_node

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
    branch_model = ob.cilinderOBJ(num_vertex=8)
    leaf_model = ob.leafOBJ()
    tree_obj, leaves_obj = get_tree_model(tree, branch_model, leaf_model)
    

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

    # # Generate tree gpu shape
    tree_node = get_tree_model_sg(tree_obj, leaves_obj, 
                                tree_color=(0.59,0.29,0.00), leaves_color=(0,0.7,0))

    # Save tree with leaves
    tree_obj.join(leaves_obj)
    tree_obj.to_file(args.filename)

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
        # Update camera values
        camera_theta -= 2.0*dt*(controller.right - controller.left)
        camera_phi -= 2.0*dt*(controller.up - controller.down)
        camera_phi = np.clip(camera_phi, 0+0.00001, np.pi/2) # view matrix is NaN when phi=0
        camera_r += 2.0*dt*(controller.zoomOut - controller.zoomIn)
        camera_r = np.clip(camera_r, 0.7, 3)

        cam_x = camera_r * np.sin(camera_phi) * np.sin(camera_theta)
        cam_y = camera_r * np.sin(camera_phi) * np.cos(camera_theta)
        cam_z = camera_r * np.cos(camera_phi)

        viewPos = np.array([cam_x,cam_y,cam_z])

        view = tr.lookAt(
            viewPos,
            np.array([0,0,0.5]),
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
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "Ka"), 0.3, 0.3, 0.3)
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "Kd"), 0.9, 0.5, 0.5)
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "Ks"), 0.4, 0.4, 0.4)

        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "lightPosition"), -5, -5, 5)
        glUniform3f(glGetUniformLocation(phongPipeline.shaderProgram, "viewPosition"), viewPos[0], viewPos[1], viewPos[2])
        glUniform1ui(glGetUniformLocation(phongPipeline.shaderProgram, "shininess"), 100)
        
        glUniform1f(glGetUniformLocation(phongPipeline.shaderProgram, "constantAttenuation"), 0.0001)
        glUniform1f(glGetUniformLocation(phongPipeline.shaderProgram, "linearAttenuation"), 0.03)
        glUniform1f(glGetUniformLocation(phongPipeline.shaderProgram, "quadraticAttenuation"), 0.01)

        glUniformMatrix4fv(glGetUniformLocation(phongPipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(phongPipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        

        sg.drawSceneGraphNode(tree_node, phongPipeline, "model")
        # Once the render is done, buffers are swapped, showing only the complete scene.
        glfw.swap_buffers(window)

    
    glfw.terminate()