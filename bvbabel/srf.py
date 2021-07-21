"""Read, write, create Brainvoyager SRF file format."""

import struct
import numpy as np
from bvbabel.utils import read_variable_length_string


# =============================================================================
def read_srf(filename):
    """Read Brainvoyager SRF file.

    Parameters
    ----------
    filename : string
        Path to file.

    Returns
    -------
    header : dictionary
        Pre-data and post-data headers.
    vertices : 2D numpy.array, (nr_vertices, XYZ coordinates)
        Vertex coordinates (float32).
    vertex_normals : 2D numpy.array, (nr_vertices, XYZ coordinates)
        Vertex normals (float32).
    faces : 2D numpy.array, (nr_vertices, vertex_indices)
        Faces (triangles), as indices of vertices (uint16).
    vertex_colors : 2D numpy.array, (nr_vertices, RGBA coordinates)
        Vertex colors. Values are in between 0-1 (float32).
    vertex_neighbors: list of lists, (nr vertices, nr neighbors)
        Other vertex members if the faces each vertex is a member of (uint16).
        Number of neighbors can vary but in conventional meshes they are often
        6 and occasionaly 5.

    """
    header = dict()
    with open(filename, 'rb') as f:
        # Expected binary data: float (4 bytes)
        data, = struct.unpack('<f', f.read(4))
        header["File version"] = data

        # Expected binary data: int (4 bytes)
        data, = struct.unpack('<i', f.read(4))
        header["Reserved"] = data  # Must be '0'
        data, = struct.unpack('<i', f.read(4))
        header["Nr vertices"] = data
        data, = struct.unpack('<i', f.read(4))
        header["Nr triangles"] = data

        # Expected binary data: float (4 bytes)
        data, = struct.unpack('<f', f.read(4))
        header["Mesh center X"] = data
        data, = struct.unpack('<f', f.read(4))
        header["Mesh center Y"] = data
        data, = struct.unpack('<f', f.read(4))
        header["Mesh center Z"] = data

        # Vertex coordinates, Expected binary data: float (4 bytes)
        vertices = np.zeros((header["Nr vertices"], 3), dtype=np.float32)
        for i in range(header["Nr vertices"]):
            data, = struct.unpack('<f', f.read(4))
            vertices[i, 0] = data

        for i in range(header["Nr vertices"]):
            data, = struct.unpack('<f', f.read(4))
            vertices[i, 1] = data

        for i in range(header["Nr vertices"]):
            data, = struct.unpack('<f', f.read(4))
            vertices[i, 2] = data

        # Vertex normals, Expected binary data: float (4 bytes)
        vertex_normals = np.zeros((header["Nr vertices"], 3), dtype=np.float32)
        for i in range(header["Nr vertices"]):
            data, = struct.unpack('<f', f.read(4))
            vertex_normals[i, 0] = data

        for i in range(header["Nr vertices"]):
            data, = struct.unpack('<f', f.read(4))
            vertex_normals[i, 1] = data

        for i in range(header["Nr vertices"]):
            data, = struct.unpack('<f', f.read(4))
            vertex_normals[i, 2] = data

        # Expected binary data: float (4 bytes)
        data, = struct.unpack('<f', f.read(4))
        header["Vertex convex curvature R"] = data
        data, = struct.unpack('<f', f.read(4))
        header["Vertex convex curvature G"] = data
        data, = struct.unpack('<f', f.read(4))
        header["Vertex convex curvature B"] = data
        data, = struct.unpack('<f', f.read(4))
        header["Vertex convex curvature A"] = data

        data, = struct.unpack('<f', f.read(4))
        header["Vertex concave curvature R"] = data
        data, = struct.unpack('<f', f.read(4))
        header["Vertex concave curvature G"] = data
        data, = struct.unpack('<f', f.read(4))
        header["Vertex concave curvature B"] = data
        data, = struct.unpack('<f', f.read(4))
        header["Vertex concave curvature A"] = data

        # ---------------------------------------------------------------------
        # NOTE(Users Guide 2.3): MeshColor, sequence of color indices.
        # Each vertex has one color index. An index value of 0 references the
        # convex curvature color (stored after the normal vectors), a value of
        # 1 references the concave curvature color (stored after the convex
        # curvature color). Functional color look-up table values or RGB colors
        # can also be represented. An RGB color is identified by an index
        # value >= 1056964608. From the 4 byte index, the R, G and B component
        # can be extracted as third byte from the right, second byte from the
        # right and right most byte. These values are stored in a range from
        # 0 - 255. For OPenGL rendering, they have to be divided by 255.0.
        #
        # Colors for POIs are stored in color indices from 10000 - 10200. Like
        # the basic (background) convex / concave colors, POI colors come also
        # in pairs. The value 10000 codes the convex color of the POI 1, the
        # value 10001 codes the concave color of POI 1, the value 10002 codes
        # the convex color of POI 2, the value 10003 codes the concave color
        # index of POI 3 and so on. The actual color values are stored in a POI
        # color look-up table.
        #
        # Colors for statistical look-up tables are stored in indices >= 1000.
        # From 1000 - 1009, the positive color bar indices are stored and from
        # 1010 - 1019, the negative color bar indices are stored. The actual
        # colors are stored in the current functional look-up table.

        vertex_colors = np.zeros((header["Nr vertices"], 4), dtype=np.float32)
        for i in range(header["Nr vertices"]):
            data, = struct.unpack('<i', f.read(4))
            bytes = data.to_bytes(4, byteorder='little', signed=False)

            if data >= 1056964608:
                vertex_colors[i, 0] = bytes[1] / 255.
                vertex_colors[i, 1] = bytes[2] / 255.
                vertex_colors[i, 2] = bytes[3] / 255
                vertex_colors[i, 3] = bytes[0] / 255.

            elif data == 0:  # convex curvature color
                vertex_colors[i, 0] = header["Vertex convex curvature R"]
                vertex_colors[i, 1] = header["Vertex convex curvature G"]
                vertex_colors[i, 2] = header["Vertex convex curvature B"]
                vertex_colors[i, 3] = header["Vertex convex curvature A"]

            elif data == 1:  # concave curvature color
                vertex_colors[i, 0] = header["Vertex concave curvature R"]
                vertex_colors[i, 1] = header["Vertex concave curvature G"]
                vertex_colors[i, 2] = header["Vertex concave curvature B"]
                vertex_colors[i, 3] = header["Vertex concave curvature A"]

            # TODO: Implement other indices too

            else:
                raise("Bad vertex color index! Should be 0, 1 or >=1056964608.")

        # ---------------------------------------------------------------------
        # Loop over nearest neighbor data for each vertex
        temp = []
        for i in range(header["Nr vertices"]):
            temp.append([])

            # Expected binary data: int (4 bytes)
            N, = struct.unpack('<i', f.read(4))
            temp[i].append(N)

            for n in range(N):  # Nearest neighbors
                NN, = struct.unpack('<i', f.read(4))
                temp[i].append(NN)
        vertex_neighbors = temp

        # ---------------------------------------------------------------------
        # Sequence of three indices to constituting vertices of each triangle
        faces = np.zeros((header["Nr vertices"], 3), dtype=np.uint16)
        for i in range(header["Nr vertices"]):
            # Expected binary data: int (4 bytes)
            faces[i, 0], = struct.unpack('<i', f.read(4))
            faces[i, 1], = struct.unpack('<i', f.read(4))
            faces[i, 2], = struct.unpack('<i', f.read(4))

        # ---------------------------------------------------------------------
        # Expected binary data: int (4 bytes)
        data, = struct.unpack('<i', f.read(4))
        header["Nr triangle strip elements"] = data
        if header["Nr triangle strip elements"] > 0:
            temp = np.zeros(header["Nr triangle strip elements"], dtype=np.int16)
            for i in range(header["Nr triangle strip elements"]):
                data, = struct.unpack('<i', f.read(4))
                temp[i] = data
        header["Sequence of strip elements"] = temp

        # Expected binary data: variable-length string
        data = read_variable_length_string(f)
        header["MTC name"] = data

    return header, vertices, vertex_normals, faces, vertex_colors, vertex_neighbors