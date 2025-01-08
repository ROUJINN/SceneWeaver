import gzip
import pickle

import bpy
import numpy as np
from mathutils import Vector

def load_pickled_3d_asset(file_path, idx=0):
    # Open the compressed pickled file
    with gzip.open(file_path, "rb") as f:
        # Load the pickled object
        loaded_object_data = pickle.load(f)

    # Create a new mesh object in Blender
    mesh = bpy.data.meshes.new(name="LoadedMesh")
    obj = bpy.data.objects.new("LoadedObject", mesh)

    # Link the object to the scene
    bpy.context.scene.collection.objects.link(obj)

    # Set the mesh data for the object
    obj.data = mesh

    # Update the mesh with the loaded data
    # print(loaded_object_data.keys())
    # print(loaded_object_data['triangles'])
    # triangles = [vertex_index for face in loaded_object_data['triangles'] for vertex_index in face]
    triangles = np.array(loaded_object_data["triangles"]).reshape(-1, 3)
    vertices = []

    for v in loaded_object_data["vertices"]:
        vertices.append([v["x"], v["z"], v["y"]])

    mesh.from_pydata(vertices, [], triangles)

    uvs = []
    for uv in loaded_object_data["uvs"]:
        uvs.append([uv["x"], uv["y"]])

    mesh.update()

    # Ensure UV coordinates are stored
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")

    uv_layer = mesh.uv_layers["UVMap"]
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = uvs[vertex_index]

    material = bpy.data.materials.new(name="AlbedoMaterial")
    obj.data.materials.append(material)

    # Assign albedo color to the material
    material.use_nodes = True
    nodes = material.node_tree.nodes
    principled_bsdf = nodes.get("Principled BSDF")

    texture_node = nodes.new(type="ShaderNodeTexImage")

    image_path = f"{'/'.join(file_path.split('/')[:-1])}/albedo.jpg"  # Replace with your image file path

    image = bpy.data.images.load(image_path)

    # Assign the image to the texture node
    texture_node.image = image

    # Connect the texture node to the albedo color
    material.node_tree.links.new(
        texture_node.outputs["Color"], principled_bsdf.inputs["Base Color"]
    )

    # normal
    image_path = f"{'/'.join(file_path.split('/')[:-1])}/normal.jpg"
    img_normal = bpy.data.images.load(image_path)
    image_texture_node_normal = material.node_tree.nodes.new(type="ShaderNodeTexImage")
    image_texture_node_normal.image = img_normal
    image_texture_node_normal.image.colorspace_settings.name = "Non-Color"

    normal_map_node = material.node_tree.nodes.new(type="ShaderNodeNormalMap")

    material.node_tree.links.new(
        normal_map_node.outputs["Normal"], principled_bsdf.inputs["Normal"]
    )
    material.node_tree.links.new(
        image_texture_node_normal.outputs["Color"], normal_map_node.inputs["Color"]
    )

    # Assign the material to the object
    obj.data.materials[0] = material

    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

    xx = [v[0] for v in bbox]
    yy = [v[1] for v in bbox]
    zz = [v[2] for v in bbox]

    length = max(xx) - min(xx)
    width = max(yy) - min(yy)
    height = max(zz) - min(zz)

    obj.location = [-(max(xx) + min(xx)) / 2, -(max(xx) + min(xx)) / 2, -min(zz)]
    # obj.location = [0,0,-height/2]
    with butil.SelectObjects(obj):
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    #    i = idx//10
    #    j = idx%10
    #    obj.location =    [0.2*i ,0.5*j, 0  ]

    # Update mesh to apply UV changes
    mesh.update()

    return obj
