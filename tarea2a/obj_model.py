import copy

import numpy as np

from basic_shapes import Shape

class OBJModel(object):
    def __init__(self, vertices:list, normals:list, faces:list):
        # vertices - List of 3d points
        # normal - List of 3d vector normal for each vertex
        # faces - List of vertex association
        self.vertices = vertices
        self.normals = normals
        self.faces = faces

    def to_file(self, file_name:str):
        # Write model to file in OBJ format
        # file_name - Name of the file
        with open(file_name, 'w') as f:
            f.write("# Generated tree OBJ model\n")
            f.write("# Vertices\n")
            for vertex in self.vertices:
                f.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")
            f.write("# Normals\n")
            for normal in self.normals:
                f.write(f"vn {normal[0]} {normal[1]} {normal[2]}\n")
            f.write("# Faces\n")
            for face in self.faces:
                f.write(f"f {face[0][0]}//{face[0][2]} {face[1][0]}//{face[1][2]} {face[2][0]}//{face[2][2]}\n")

    def to_shape(self, color):
        # Create a Shape from the OBJ model
        # Color - Color tuple for the created shape
        vertex_data = []
        indices = []
        aux_dict = {}
        index = 0

        for face in self.faces:
            face_vertex_index = []
            for i in range(3):
                vertex_id = f"{face[i][0]}/{face[i][2]}"
                if vertex_id in aux_dict.keys():
                    face_vertex_index.append(aux_dict[vertex_id])
                else:
                    vertex = self.vertices[face[i][0]-1]
                    normal = self.normals[face[i][2]-1]
                    vertex_data += [vertex[0], vertex[1], vertex[2],
                                    color[0], color[1], color[2],
                                    normal[0], normal[1], normal[2]]
                    aux_dict[vertex_id] = index
                    face_vertex_index.append(index)
                    index+=1
                
            indices += face_vertex_index
        
        return Shape(vertex_data, indices)

    def join(self, model: 'OBJModel') -> 'OBJModel':
        # Join the model with another (modifies the model)
        # model - OBJModel to merge
        n_vertices = len(self.vertices)
        n_normals = len(self.normals)
        # Join vertices and normals
        self.vertices += model.vertices
        self.normals += model.normals

        # Update indexes
        temp_faces = copy.deepcopy(model.faces)
        for face in temp_faces:
            for i in range(3):
                face[i][0] += n_vertices
                face[i][2] += n_normals
        # Join faces
        self.faces += temp_faces

    def transform(self, M) -> 'OBJModel':
        # Transform vertices and normals with a transformation matrix
        # Return new OBJModel
        # M - (4,4) Transformation matrix
        # Add dimension to vertices
        new_vertices = np.column_stack([self.vertices, np.ones(len(self.vertices))])[:,:,np.newaxis]
        # Transform vertices
        new_vertices = np.matmul(M,new_vertices).squeeze()[:,:3]

         # normals to numpy array
        new_normals = np.column_stack([self.normals, np.ones(len(self.normals))])[:,:,np.newaxis]
        # Transform normals
        G = np.linalg.inv(M).transpose()
        new_normals = np.matmul(G, new_normals).squeeze()[:,:3]
        # normalize
        norm = np.linalg.norm(new_normals, axis=1)
        new_normals = (new_normals.transpose()/norm).transpose()

        return OBJModel(new_vertices.tolist(), new_normals.tolist(), copy.deepcopy(self.faces))

def cubeOBJ():
    # A 3D cube in OBJ format
    # Defining the location of each vertex  of the shape
    vertices = [
    #   positions
    # Z+
        [-0.5, -0.5,  0.5],
        [ 0.5, -0.5,  0.5],
        [ 0.5,  0.5,  0.5],
        [-0.5,  0.5,  0.5],

    # Z-
        [-0.5, -0.5, -0.5],
        [0.5, -0.5, -0.5],
        [0.5,  0.5, -0.5],
        [-0.5,  0.5, -0.5],
        ]
    
    normals = [
    #normals
    # Z+
        [0,0,1],

    # Z-
        [0,0,-1],
        
    # X+
        [1,0,0],
 
    # X-
        [-1,0,0],

    # Y+
        [0,1,0],

    # Y-
        [0,-1,0]
        ]

    # Defining connections among vertices
    # Every face has 3 vertices

    faces = [
    #   vertex texture normal
        [[1,None,1],[2,None,1],[3,None,1]], #Z+
        [[3,None,1],[4,None,1],[1,None,1]], #Z+
        [[8,None,2],[7,None,2],[6,None,2]], #Z-
        [[6,None,2],[5,None,2],[8,None,2]], #Z-
        [[6,None,3],[7,None,3],[3,None,3]], #X+
        [[3,None,3],[2,None,3],[6,None,3]], #X+
        [[1,None,4],[4,None,4],[8,None,4]], #X-
        [[8,None,4],[5,None,4],[1,None,4]], #X-
        [[4,None,5],[3,None,5],[7,None,5]], #Y+
        [[7,None,5],[8,None,5],[4,None,5]], #Y+
        [[5,None,6],[6,None,6],[2,None,6]], #Y-
        [[2,None,6],[1,None,6],[5,None,6]], #Y-
    ]

    return OBJModel(vertices, normals, faces)

    

def cilinderOBJ(num_vertex: int):
    # A cilinder in OBJ format
    # num_vertex - Number of vertices to aproximate circles
    # Create a cilinder OBJ model
    assert(num_vertex>2)
    angles = np.linspace(0,2*np.pi,num_vertex+1)[:-1]
    vertices_up = []
    vertices_down = []
    normals = [
    #normals
    # Z+
        [0,0,1],
    # Z-
        [0,0,-1]
    ]
    faces = []
    # Create sides
    for i in range(num_vertex):
        # Create up and down vertices
        x = np.cos(angles[i])
        y = np.sin(angles[i])
        vertices_up.append([0.5*x, 0.5*y, 0.5])
        vertices_down.append([0.5*x, 0.5*y, -0.5])
        # Add normal
        normals.append([x, y, 0])
        # Create lateral faces
        j = i + 1
        j_next = (i+1)%num_vertex + 1
        k = j+num_vertex
        k_next = j_next + num_vertex
        faces.append(
            [[j,None,j+2],[k,None,j+2],[j_next,None,j_next+2]],
        )
        faces.append(
            [[j_next,None,j_next+2],[k,None,j+2],[k_next,None,j_next+2]],
        )
    vertices = vertices_up + vertices_down
    # create up/down faces
    for i in range(num_vertex-2):
        # Z+ circle
        j = i+1
        faces.append(
            [[1,None,1],[j+1,None,1],[j+2,None,1]]
        )
        # Z- circle
        k = j+num_vertex
        faces.append(
            [[k+2,None,2],[k+1,None,2],[num_vertex+1,None,2]]
        )

    return OBJModel(vertices, normals, faces)

def leafOBJ():
    # A simple leaf model in OBJ format
    # Defining the location of each vertex  of the shape
    vertices = [
    #   positions
        [ 0.0,  0.0,  0.0],
        [ 0.4,  0.0,  1.0],
        [-0.4,  0.0,  1.0]
    ]
    
    normals = [
    #normals
    # Y+
        [0,1,0],
    # Y-
        [0,-1,0]
    ]

    # Defining connections among vertices
    # Every face has 3 vertices

    faces = [
    #   vertex texture normal
        [[1,None,1],[2,None,1],[3,None,1]], #Y+
        [[3,None,2],[2,None,2],[1,None,2]], #Y-
    ]

    return OBJModel(vertices, normals, faces)