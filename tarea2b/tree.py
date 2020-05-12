import numpy as np

import transformations as tr
import matplotlib.pyplot as plt

class Branch:
    def __init__(self, origin, end):
        self.origin=origin
        self.end = end

class FractalTree3D:
    def __init__(self, height, split_ang, split_n, decr, rec_level, sides_n, origin=(0,0,0), direction=(0,0,1)):
        self.childs=[]
        # Length of first segment
        seg_length = height/np.sum([decr**i for i in range(split_n)])
        direction = np.array(direction)
        branch_origin = np.array(origin)
        branch_end = branch_origin + seg_length*direction
        for i in range(split_n-1):
            self.childs.append(Branch(branch_origin,branch_end))
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
                                                    branch_end, branch_dir))
                    branch_dir = np.matmul(branch_dir, rotM2[:3,:3])
            branch_origin = branch_end
            branch_end = branch_origin + seg_length*direction
        self.childs.append(Branch(branch_origin, branch_end))

def treePlotter(tree, axis, styles, rec_level=0):
    for section in tree.childs:
        if isinstance(section, FractalTree3D):
            treePlotter(section, axis, styles, rec_level=rec_level+1)
        else:
            points = list(zip(section.origin, section.end))
            axis.plot(points[0],points[1],points[2],styles[rec_level])

if __name__ == "__main__":
    tree = FractalTree3D(height=1.0, split_ang=np.pi/3, split_n=4, decr=0.8, rec_level=2, sides_n=3)

    styles = ['r','g','b']
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.set_zlim(-1, 1)
    treePlotter(tree, ax, styles)
    plt.show()