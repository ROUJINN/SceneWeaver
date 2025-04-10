
from gpt import GPT4 
from utils import extract_json, dict2str, lst2str
import json

system_prompt = """
You are an expert in 3D scene design. We design a code to manage the scene, where more relations will make the scene more tidy.
Sometimes the relation is encoded in the layout coordinate rather than represented explicitly, making it difficult to manage.

Your task is to : 
Add explicit relation to objects in the current scene according to the layout and daily-usage prior. 

For example, if the nightstand stands next to the bed, you should add ["bed_name", "side_by_side"] to the relation of the nightstand.
If the chair face to the front of the desk, you should add ["desk_name", "front_to_front"] to the relation of the chair.
If the shelf stands with its back to the wall, you should add ["room_name", "against_wall"] to the relation of the shelf. Here wall is part of the room.
More relations can be added according to the relation list and objects' layout.

"""


user_prompt = """
Here is the information you receive:
1.This is a {roomtype}. 
2.The room size is [{roomsize}] in length and width.
3.User demand for the entire scene: {user_demand}
4.This is the scene layout: {layout}
5.This is the layout of door and windows: {structure}
6.This is the image render from the top view: SCENE_IMAGE 

**3D Convention:**
- Right-handed coordinate system.
- The X-Y plane is the floor; the Z axis points up. The origin is at a corner (the left-top corner of the rendered image), defining the global frame.
- Asset front faces point along the positive X axis. The Z axis points up. The local origin is centered in X-Y and at the bottom in Z. 
A 90-degree Z rotation means that the object will face the positive Y axis. The bounding box aligns with the assets local frame.

For the image:
- The origin point x,y =[0,0] represents the top-left corner of the image.
- The x-coordinate increases from left to right (positive x is to the right).
- The y-coordinate usually increases from top to bottom (positive y is downward).

Please take a moment to relax and carefully look through each object and their relations.
The relation is written as a list in the "parent" key, in the format of [parent_obj's name, relation]. 
For example, ["newroom_0-0", "onfloor"] means the child_obj is on the floor of the room. Note "newroom_0-0" is not listed in the objetcs' layout.
And ["2419840_bed","ontop"] means the child_obj is on the top of "2419840_bed".
Some relations have already been added, and you need to implement the relations when the layout is similar to the relation but not recorded in "parent" explicitly.
You can take regular usage habits into account.

The optional relation is: 
1.front_against: child_obj's front faces to parent_obj, and stand very close.
2.front_to_front: child_obj's  front faces to parent_obj's front, and stand very close.
3.leftright_leftright: child_obj's left or right faces to parent_obj's left or right, and stand very close. 
4.side_by_side: child_obj's side(left, right , or front) faces to parent_obj's side(left, right , or front), and stand very close. 
5.back_to_back: child_obj's back faces to parent_obj's back, and stand very close. 
6.ontop: child_obj is placed on the top of parent_obj.
7.on: child_obj is placed on the top of or inside parent_obj.
8.against_wall: child_obj's back faces to the wall of the room, and stand very close.
9.side_against_wall: child_obj's side(left, right , or front) faces to the wall of the room, and stand very close.
9.on_floor: child_obj stand on the parent_obj, which is the floor of the room.

Note child_obj is usually smaller than parent_obj, or child_obj belongs to parent_obj. 
And the child_obj can have no more than one relation with other objects.

Before returning the final results, you need to carefully confirm that each obvious relation has been added. 

Provide me with the newly added relation of each object in json format.
For example:
{
    "3454242_VaseFactory": {
        "parent": [["5433016_dresser","ontop"]]
    },
    "1542543_Sofa": {
        "parent": [["newroom_0-0","against_wall"]]
    },
    "4254546_Cabinet": {
        "parent": [["newroom_0-0","against_wall"],["1542543_Sofa","leftright_leftright"]]
    },
}

"""

def add_relation(user_demand,ideas,iter,roomtype):

    render_path = f"/home/yandan/workspace/infinigen/record_scene/render_{iter-1}.jpg"
    with open(f"/home/yandan/workspace/infinigen/record_scene/layout_{iter-1}.json", "r") as f:
        layout = json.load(f)
    
    roomsize = layout["roomsize"]
    roomsize = lst2str(roomsize)

    structure = dict2str(layout["structure"])
    layout = dict2str(layout["objects"])
    
    
    system_prompt_1 = system_prompt
    user_prompt_1 = user_prompt.format(roomtype=roomtype,roomsize=roomsize,
                                       layout=layout,structure=structure,
                                       user_demand=user_demand,ideas=ideas) 
        
    gpt = GPT4(version="4o")

    prompt_payload = gpt.get_payload_scene_image(system_prompt_1, user_prompt_1,render_path=render_path)
    gpt_text_response = gpt(payload=prompt_payload, verbose=True)
    print(gpt_text_response)

    json_name = f"/home/yandan/workspace/infinigen/Pipeline/record/add_relation_results_{iter}_response.json"
    with open(json_name, "w") as f:
        json.dump(gpt_text_response, f, indent=4)

    new_layout = extract_json(gpt_text_response)
    
    json_name = f"/home/yandan/workspace/infinigen/Pipeline/record/add_relation_results_{iter}.json"
    with open(json_name, "w") as f:
        json.dump(new_layout, f, indent=4)

    return json_name
    
if __name__ == "__main__":
    user_demand = "A Bedroom"
    ideas = "improve"
    iter=10
    roomtype=user_demand
    add_relation(user_demand,ideas,iter,roomtype)
