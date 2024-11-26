import bpy




def load_infinigen_scene(blend_file_path="/home/yandan/workspace/infinigen/outputs/indoors/coarse_p/scene.blend"):
    
    bpy.ops.wm.open_mainfile(filepath=blend_file_path)
    bpy.context.view_layer.update()
    return 
# load_infinigen_scene()

# def load_infinigen_scene(blend_file_path="/home/yandan/workspace/infinigen/outputs/indoors/coarse_p/scene.blend"):
#     with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
#        data_to.collections = [name for name in data_from.collections]

#     # 将加载的集合添加到当前场景
#     for collection in data_to.collections:
#        if collection:
#            bpy.context.scene.collection.children.link(collection)
       
#     return 

def load_acdc_scene(blend_file_path="/home/yandan/Desktop/acdc_objaverse/acdc_output-desk111/step_3_output/scene_1/scene_1.blend"):

    collection_acdc = bpy.data.collections.new("CollectionACDC")
    bpy.context.scene.collection.children.link(collection_acdc)

    # 加载对象到当前场景
    with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
        data_to.objects = []

        for obj in data_from.objects :
            if obj.startswith("Area") or obj.startswith("Camera"):
                continue
            data_to.objects.append(obj)

    # 将加载的集合添加到当前场景
    for obj in data_to.objects:
        collection_acdc.objects.link(obj)

    bpy.context.view_layer.update()
    return

def get_obj_from_collection(collection_name,obj_name):
    
    collection = bpy.data.collections[collection_name]
    if obj_name in collection.objects:
        return collection.objects[obj_name]


load_acdc_scene()

source_name = "desk_0"
source_obj = get_obj_from_collection("CollectionACDC",source_name)

target_name = "SimpleDeskFactory(8569017).spawn_asset(5056988)"
target_obj = get_obj_from_collection("unique_assets",target_name) 


M_source = source_obj.matrix_world.copy()
M_target = target_obj.matrix_world.copy()



collection = bpy.data.collections["CollectionACDC"]
# 遍历集合中的对象
for obj in collection.objects:
    # 确保对象不是隐藏的
    if obj.hide_viewport:
        continue
    obj.matrix_world =  M_target @ M_source.inverted() @ obj.matrix_world
    print(f"Transformed object: {obj.name}")
    

# ####################################################

# # 目标 .blend 文件路径
# blend_file_path = "/home/yandan/Desktop/acdc_objaverse/acdc_output-desk111/step_3_output/scene_1/scene_1.blend"
# collection_name = "Collection 2"  # 想导入的集合名称

# # 加载对象到当前场景
# with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
#    data_to.collections = [name for name in data_from.collections if name == collection_name]

# # 将加载的集合添加到当前场景
# for collection in data_to.collections:
#    if collection:
#        bpy.context.scene.collection.children.link(collection)
       
        


