
from gpt import GPT4 
from utils import extract_json, dict2str, lst2str
import json

system_prompt = """
You are an expert in 3D scene evaluation. 

Your task is to : 
1) evaluate the current scene, 
2) tell me what problem it has, 
3) help me solve the problem.

**3D Convention:**
- Right-handed coordinate system.
- The X-Y plane is the floor; the Z axis points up. The origin is at a corner (the left-top corner of the rendered image), defining the global frame.
- Original asset (without rotation) faces point along the positive X axis. The Z axis points up. The local origin is centered in X-Y and at the bottom in Z. 
- A 90-degree Z rotation means that the object will face the positive Y axis. The bounding box aligns with the assets local frame.
For the image:
- The origin point x,y =[0,0] represents the top-left corner of the image.
- The x-coordinate increases from left to right (positive x is to the right).
- The y-coordinate usually increases from top to bottom (positive y is downward).

"""




user_prompt = """
Here is the information you receive:
1.This is a {roomtype}. 
2.The room size is [{roomsize}] in length and width.
3.User demand for the entire scene: {user_demand}
4.Ideas for this step: {ideas}
5.This is the scene layout: {layout}
6.This is the layout of door and windows: {structure}
7.This is the image render from the top view: SCENE_IMAGE 

**3D Convention:**
- Right-handed coordinate system.
- The X-Y plane is the floor; the Z axis points up. The origin is at a corner (the left-top corner of the rendered image), defining the global frame.
- Asset front faces point along the positive X axis. The Z axis points up. The local origin is centered in X-Y and at the bottom in Z. 
A 90-degree Z rotation means that the object will face the positive Y axis. The bounding box aligns with the assets local frame.

Please take a moment to relax and carefully look through each object and their relations.
You can consider the following factors:

1. Room Structure: Be aware of the door and windows. Make sure objects do not overlap with the door and windows.
2. Collision and Layout Issues: Check if there are any collisions or improper placements of objects that disrupt the flow of the room. 
3. User Prompt Satisfaction: Does the current scene meet the user's prompt requirements? What needs to be changed to align with the prompt more closely?
4. Realism Enhancement: What adjustments can be made to make the scene feel more realistic? Consider removing or repositioning objects to enhance visual harmony and authenticity.
5. Check Object: Check for any redundant or unnecessary objects that could be removed to streamline the scene.
6. Relation: Add relations to some objects (saved in "parent") when the layout is similar to the relation. This can make the room tidy.

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
Note child_obj is usually smaller than parent_obj, or obj1 belongs to parent_obj.

What problem do you think it has? 
Then tell me how to solve these problems.

Fianlly, according to the problem and thoughts, you should modify objects' layout to fix each of the problem.
You can change the location, rotation, and size of the objects.
You can also add,delete, or modify the parent relations for each object.
For objects that remain unchanged, you must keep their original layout in the response rather than omit it. 
For deleted objects, omit their layout in the response.
Keep the objects inside the room. 

Before returning the final results, you need to carefully confirm that each issue has been resolved. 
If not, update the layout until each problem is resolved.

Provide me with the new layout of each object in json format.
Do not add any comment in the json. For example:
False:
"location": [5.5, 2.5, 0.28],  // Adjusted to avoid overlap
True:
"location": [5.5, 2.5, 0.28],

"""

def update_scene_gpt(user_demand,ideas,iter,roomtype):

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

    json_name = f"/home/yandan/workspace/infinigen/Pipeline/record/update_gpt_results_{iter}_response.json"
    with open(json_name, "w") as f:
        json.dump(gpt_text_response, f, indent=4)

    new_layout = extract_json(gpt_text_response)
    
    json_name = f"/home/yandan/workspace/infinigen/Pipeline/record/update_gpt_results_{iter}.json"
    with open(json_name, "w") as f:
        json.dump(new_layout, f, indent=4)

    return json_name
    
if __name__ == "__main__":
    user_demand = "A Bedroom"
    ideas = "improve"
    iter=10
    roomtype=user_demand
    update_scene_gpt(user_demand,ideas,iter,roomtype)
