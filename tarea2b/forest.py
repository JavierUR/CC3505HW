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
import tree

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

def generateTreeModels(num, rec_level):
    trees = []
    branch_model = ob.cubeOBJ()
    for _ in range(num):
        height = 0.8 + 0.4*np.random.random()
        angle = np.deg2rad(15 + 70*np.random.random())
        split_n = np.random.randint(1,4)
        decr = 0.8 + 0.15*np.random.random()
        sides_n = np.random.randint(1,6)
        base_diameter = 0.01 + 0.05*np.random.random()
        #fractalTree = tree.FractalTree3D(height, angle, split_n, decr,
        #                                rec_level, sides_n, base_diameter)
        fractalTree = tree.FractalTree3D(height,angle,split_n,decr,rec_level,sides_n,base_diameter)
        trees.append(tree.get_tree_model(fractalTree, branch_model))
    return trees

def generateUniformPoints(width, lenght, num_points, min_dis, pool=10000):
    xmin = -width/2
    xmax = -xmin
    ymin = -lenght/2
    ymax = -ymin
    possible_points = np.array((np.random.uniform(xmin,xmax,pool),
                       np.random.uniform(ymin,ymax,pool) )).transpose()
    keep_points = possible_points[0].reshape(1,2)
    count = 1
    for i in range(1,len(possible_points)):
        point = possible_points[i]
        distances = np.sqrt(
            (keep_points[:,0]-point[0])**2 + (keep_points[:,1]-point[1])**2
        )
        if min(distances) >= min_dis:
            keep_points = np.concatenate((keep_points,point.reshape(1,2)))
            count+=1
            if count == num_points:
                return keep_points
    return keep_points

def populateForest(width, lenght, fz, treeGPUModels, tree_den):
    scale = tr.uniformScale(0.5)
    area = width*lenght
    tree_rad = 0.15
    tree_area = np.pi*(tree_rad**2)
    num_trees = int(area/tree_area*tree_den)
    locations = generateUniformPoints(width,lenght,num_trees, tree_rad)
    forest_trees = sg.SceneGraphNode("forest_trees")
    for i in range(len(locations)):
        tree_node = sg.SceneGraphNode("tree")
        x, y = locations[i]
        tree_node.transform = tr.matmul([tr.translate(x, y, fz(x,y)),scale])
        model = i%len(treeGPUModels)
        tree_node.childs = [treeGPUModels[model]]
        forest_trees.childs.append(tree_node)
    return forest_trees

# A class to create a gaussian function
class Gaussian:
    def __init__(self, x0, y0, stdx, stdy):
        # x0 - Gaussian center x position
        # y0 - Gaussian center y position
        # stdx - x coordinate standard deviation
        # stdy - y coordinate standard deviation
        self.x0 = x0
        self.y0 = y0
        self.stdx = stdx
        self.stdy = stdy
        self.const = 1/(2*np.pi*stdx*stdy)
    
    def __call__(self,x,y):
        # x - x position
        # y - y position
        # return - Gaussian value at x,y
        mx = ((x-self.x0)/self.stdx)**2
        my = ((y-self.y0)/self.stdy)**2
        return self.const*np.exp(-0.5*(mx+my))

if __name__ == "__main__":
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

    # Using the same view and projection matrices in the whole application
    projection = tr.perspective(45, float(width)/float(height), 0.1, 100)
    
    camera_theta = 0.0
    camera_phi = np.pi/4
    camera_r = 3
    ltime = 0

    # Create forest terrain
    g1 = Gaussian(0,0,1,1)
    g2 = Gaussian(1,1,0.5,2)
    fz = lambda x,y: g1(x,y) + g2(x,y)
    terrain = create_terrain(4, 4, 4,fz)
    terrain_node = sg.SceneGraphNode("terrain_node")
    terrain_node.childs = [es.toGPUShape(terrain.to_shape((0,0.4,0.4)))]

    # Create trees
    trees = generateTreeModels(num=5, rec_level=3)
    treesGPU = []
    for objTree in trees:
        treesGPU.append(
            es.toGPUShape(objTree.to_shape((0.59,0.29,0.00)))
        )
    trees_node = populateForest(4, 4, fz, treesGPU,0.09)

    # treeFractal = tree.FractalTree3D(1,45,3,0.9,3,4,0.02)
    # branch_model = ob.cubeOBJ()
    # tree_obj = tree.get_tree_model(treeFractal, branch_model)
    # treeGPU = es.toGPUShape(tree_obj.to_shape((0.59,0.29,0.00)))
    # trees_node = sg.SceneGraphNode("tree_node")
    # trees_node.childs = [treeGPU]
    # trees_node.transform = tr.translate(0,0,fz(0,0))

    # Assemble forest
    forest = sg.SceneGraphNode("forest")
    forest.childs = [terrain_node, trees_node]

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