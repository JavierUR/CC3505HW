import argparse
import json

import numpy as np
import matplotlib.pyplot as plt
from scipy.sparse import dok_matrix
from scipy.sparse.linalg import spsolve

import tracemalloc
import linecache

def display_top(snapshot, key_type='lineno', limit=10):
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    print("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        print("#%s: %s:%s: %.1f KiB"
              % (index, frame.filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    print("Total allocated size: %.1f KiB" % (total / 1024))

tracemalloc.start()

# Point types
NORMAL    = 0
B_HEAT_A  = 1
B_HEAT_B  = 2
B_AMBIENT = 3
B_WALL    = 4
B_BOTTOM  = 5

def get_left_type(m,n,l):
    # Function get the type of the left border point
    # m,n,l - Point coordinates
    # return - Point type
    global bottom_mask
    if m >=0: # Inside point
        if l > 0: 
            return NORMAL
        else: # Bottom point
            return bottom_mask[m,n]
    else: # Outside point
        return B_WALL

def get_right_type(m,n,l):
     # Function get the type of the right border point
    # m,n,l - Point coordinates
    # return - Point type
    global bottom_mask, n_width
    if m < n_width: # Inside point
        if l > 0: 
            return NORMAL
        else: # Bottom point
            return bottom_mask[m,n]
    else: # Outside point
        return B_WALL

def get_up_type(m,n,l):
     # Function get the type of the up border point
    # m,n,l - Point coordinates
    # return - Point type
    global n_height
    if l < (n_height-1): # Inside point
        return NORMAL
    else: # surface point
        return B_AMBIENT

def get_down_type(m,n,l):
     # Function get the type of the down border point
    # m,n,l - Point coordinates
    # return - Point type
    global bottom_mask, n_lenght
    if l >0: # Inside point
        return NORMAL
    else: # Outside point
        if l == 0:
            return bottom_mask[m,n]
        else:
            return B_BOTTOM

def get_front_type(m,n,l):
     # Function get the type of the front border point
    # m,n,l - Point coordinates
    # return - Point type
    global bottom_mask, n_lenght
    if n < n_lenght: # Inside point
        if l > 0: 
            return NORMAL
        else: # Bottom point
            return bottom_mask[m,n]
    else: # Outside point
        return B_WALL

def get_back_type(m,n,l):
     # Function get the type of the back border point
    # m,n,l - Point coordinates
    # return - Point type
    global bottom_mask, n_lenght
    if n >= 0: # Inside point
        if l > 0: 
            return NORMAL
        else: # Bottom point
            return bottom_mask[m,n]
    else: # Outside point
        return B_WALL

if __name__ == '__main__':
    # Parse arguments
    #parser = argparse.ArgumentParser(description='Aquarium Solver.')
    #parser.add_argument('filename', metavar='Setup_File', type=str,
    #                help='(string) Name of the problem json setup file')
    #args = parser.parse_args()
    """ Load json parameters
        height:              Aquarium height [m]
        width:               Aquarium width [m]
        lenght:              Aquarium lenght [m]
        window_loss:         Heat loss in side Aquarium windows [°C/m]
        heater_a:            Heater A temperature [°C]
        heater_b:            Heater B temperature [°C]
        ambient_temperature: Ambient temperature of the aquarium [°C]
        filename:            file to save results 
    """
    filename = "problem-setup.json"
    with open(filename, 'r') as setup_file:
        config = json.load(setup_file)
    print(config)

    h = 0.2
    print("Solving with h = {}".format(h))
    n_width = round(config['width']/h)
    n_lenght = round(config['lenght']/h)
    n_height = round(config['height']/h)
    space = np.zeros((n_width,n_lenght,n_height))
    # Set bottom mask
    bottom_mask = np.zeros((n_width, n_lenght), dtype=np.uint8)
    n_1  = round((config['width']/3)/h)
    n_2  = round(2*(config['width']/3)/h)
    na_1 = round((config['lenght']/5)/h)
    na_2 = round(2*(config['lenght']/5)/h)
    nb_1 = round(3*(config['lenght']/5)/h)
    nb_2 = round(4*(config['lenght']/5)/h)
    bottom_mask[n_1:n_2,na_1:na_2] = B_HEAT_A
    bottom_mask[n_1:n_2,nb_1:nb_2] = B_HEAT_B
    # point mapping
    points = []
    for i in range(n_width):
        for j in range(n_lenght):
            for k in range(n_height-1):
                if k>0 or bottom_mask[i,j]==0:
                    points.append( (i,j,k) )
    inv_dict = { str(points[i]):i for i in range(len(points))}

    # Build linear equation system
    n_var = len(points)
    A = dok_matrix((n_var, n_var), dtype=np.float32)
    b = np.zeros(n_var)

    snapshot1 = tracemalloc.take_snapshot()

    for p_index in range(n_var):
        i, j, k = points[p_index]
        A[p_index, p_index] = -6
        # Borders
        m, n, l = i-1, j, k
        b_type = get_left_type(m,n,l)
        if b_type == NORMAL:
            b_index = inv_dict[str((m,n,l))]
            A[p_index,b_index] += 1
        elif b_type == B_WALL: # left side - Neumann
            b[p_index]+= 2*h*config['window_loss']
            b_index = inv_dict[str((i+1,j,k))] #u_{i+1,j,k}
            A[p_index,b_index]+=1 
        elif b_type == B_HEAT_A: # Heater A - Dirichlet
            b[p_index]-= config['heater_a']
        elif b_type == B_HEAT_B: # Heater B - Dirichlet
            b[p_index]-= config['heater_b']

        m, n, l = i+1, j, k
        b_type = get_right_type(m,n,l)
        if b_type == NORMAL:
            b_index = inv_dict[str((m,n,l))]
            A[p_index,b_index] += 1
        elif b_type == B_WALL: #right side - Neumann
            b[p_index]+= 2*h*config['window_loss']
            b_index = inv_dict[str((i-1,j,k))] #u_{i-1,j,k}
            A[p_index,b_index]+=1
        elif b_type == B_HEAT_A: # Heater A - Dirichlet
            b[p_index]-= config['heater_a']
        elif b_type == B_HEAT_B: # Heater B - Dirichlet
            b[p_index]-= config['heater_b']

        m, n, l = i, j+1, k
        b_type = get_front_type(m,n,l)
        if b_type == NORMAL:
            b_index = inv_dict[str((m,n,l))]
            A[p_index,b_index] += 1
        elif b_type == B_WALL: #front side - Neumann
            b[p_index]+= 2*h*config['window_loss']
            b_index = inv_dict[str((i,j-1,k))] #u_{i,j-1,k}
            A[p_index,b_index]+=1
        elif b_type == B_HEAT_A: # Heater A - Dirichlet
            b[p_index]-= config['heater_a']
        elif b_type == B_HEAT_B: # Heater B - Dirichlet
            b[p_index]-= config['heater_b']


        m, n, l = i, j-1, k
        b_type = get_back_type(m,n,l)
        if b_type == NORMAL:
            b_index = inv_dict[str((m,n,l))]
            A[p_index,b_index] += 1
        elif b_type == B_WALL: #back side - Neumann
            b[p_index]+= 2*h*config['window_loss']
            b_index = inv_dict[str((i,j+1,k))] #u_{i,j+1,k}
            A[p_index,b_index]+=1
        elif b_type == B_HEAT_A: # Heater A - Dirichlet
            b[p_index]-= config['heater_a']
        elif b_type == B_HEAT_B: # Heater B - Dirichlet
            b[p_index]-= config['heater_b']

        m, n, l = i, j, k+1
        b_type = get_up_type(m,n,l)
        if b_type == NORMAL:
            b_index = inv_dict[str((m,n,l))]
            A[p_index,b_index] += 1
        else: # surface - Dirichlet
            b[p_index]-= config['ambient_temperature']

        m, n, l = i, j, k-1
        b_type = get_down_type(m,n,l)
        if b_type == NORMAL:
            b_index = inv_dict[str((m,n,l))]
            A[p_index,b_index] += 1
        elif b_type == B_BOTTOM: # bottom - Null Neumann
            b[p_index]+= 0
            b_index = inv_dict[str((i,j,k+1))] #u_{i,j,k+1}
            A[p_index, b_index] += 1
        elif b_type == B_HEAT_A: # Heater A - Dirichlet
            b[p_index]-= config['heater_a']
        elif b_type == B_HEAT_B: # Heater B - Dirichlet
            b[p_index]-= config['heater_b']

    snapshot2 = tracemalloc.take_snapshot()
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')

    print("[ Top 10 differences ]")
    for stat in top_stats[:10]:
        print(stat)

    

    # Solve system
    A = A.tocsc()
    u = spsolve(A,b)
    # Fill values
    for p_index in range(n_var):
            i, j, k = points[p_index]
            space[i,j,k] = u[p_index]
    space[n_1:n_2,na_1:na_2,0] = config['heater_a']
    space[n_1:n_2,nb_1:nb_2,0] = config['heater_b']
    space[:,:,-1] = config['ambient_temperature']

    # Save results
    np.save(config['filename'],space)

    snapshot3 = tracemalloc.take_snapshot()
    display_top(snapshot3)
    