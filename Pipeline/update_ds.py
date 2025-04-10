from deepseek import DeepSeek
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
5.This is the scene layout: {layout}. 
6.This is the layout of door and windows: {structure}

Please take a moment to relax and carefully look through each object and their relations.
What problem do you think it has? 
Then tell me how to solve these problems.

Fianlly, according to the problem and thoughts, you should modify objects' layout to fix each of the problem.
For objects that remain unchanged, you must keep their original layout in the response rather than omit it. 
For deleted objects, omit their layout in the response.
Keep the objects inside the room. 

Before returning the final results, you need to carefully confirm that each issue has been resolved. 
If not, update the layout until each problem is resolved.

Provide me with the new layout of each object in json format.

"""
    

def update_scene_ds(user_demand,ideas,iter,roomtype):

    with open(f"/home/yandan/workspace/infinigen/record_scene/layout_{iter-1}.json", "r") as f:
        layout = json.load(f)
    
    roomsize = [layout["roomsize"][0]*100, layout["roomsize"][1]*100]
    roomsize = lst2str(roomsize)

    
    structure = dict2str(layout["structure"])
    layout = layout["objects"]
    
    for objname in layout:
        layout[objname]["location"] = [int(100*x) for x in layout[objname]["location"]]
        layout[objname]["size"] = [int(100*x) for x in layout[objname]["size"]]
    layout = dict2str(layout)
    
    system_prompt_1 = system_prompt 
    user_prompt_1 = user_prompt.format(roomtype=roomtype,roomsize=roomsize,layout=layout,
                                       structure=structure,user_demand=user_demand,ideas=ideas) 
        
    ds = DeepSeek()

    prompt_payload = ds.get_payload(system_prompt_1, user_prompt_1)
    response = ds(payload=prompt_payload, verbose=True)
    print(response)
    
    json_name = f"/home/yandan/workspace/infinigen/Pipeline/record/update_ds_results_{iter}_response.json"
    with open(json_name, "w") as f:
        json.dump(response, f, indent=4)

    new_layout = extract_json(response)
    
    for objname in new_layout:
        new_layout[objname]["location"] = [round(x/100.0,2) for x in new_layout[objname]["location"]]
        new_layout[objname]["size"] = [round(x/100.0,2) for x in new_layout[objname]["size"]]
    json_name = f"/home/yandan/workspace/infinigen/Pipeline/record/update_ds_results_{iter}.json"
    with open(json_name, "w") as f:
        json.dump(new_layout, f, indent=4)

    

    return json_name
    
if __name__=="__main__":
    new_layout = {
                "1133652_backpack": {
                    "location": [306, 218, 35],
                    "rotation": [0.0, -0.0, 1.57],
                    "size": [21, 42, 43]
                },
                "4778707_chair": {
                    "location": [157, 429, 69],
                    "rotation": [0.0, -0.0, 1.57],
                    "size": [61, 76, 111]
                },
                "852804_trash can": {
                    "location": [540, 294, 38],
                    "rotation": [0.0, -0.0, 1.57],
                    "size": [22, 40, 49]
                },
                "5229206_file cabinet": {
                    "location": [222, 69, 60],
                    "rotation": [0.0, -0.0, 3.14],
                    "size": [42, 35, 55]
                },
                "7787053_desk": {
                    "location": [227, 387, 66],
                    "rotation": [0.0, -0.0, 3.14],
                    "size": [69, 145, 71]
                },
                "2633337_a white napkin": {
                    "location": [517, 413, 3],
                    "rotation": [0.0, -0.0, 0.0],
                    "size": [14, 19, 13]
                },
                "4485089_monitor": {
                    "location": [467, 163, 145],
                    "rotation": [0.0, -0.0, 3.14],
                    "size": [24, 57, 50]
                },
                "5584290_box": {
                    "location": [416, 235, 24],
                    "rotation": [0.0, -0.0, 3.14],
                    "size": [27, 27, 20]
                },
                "7274977_a black mouse pad": {
                    "location": [410, 90, 122],
                    "rotation": [0.0, 0.0, -1.57],
                    "size": [17, 19, 1]
                },
                "7301665_office chair": {
                    "location": [163, 387, 61],
                    "rotation": [0.0, 0.0, 0.0],
                    "size": [60, 69, 94]
                },
                "6171229_a black keyboard": {
                    "location": [100, 130, 145],
                    "rotation": [0.0, 0.0, -1.57],
                    "size": [41, 14, 6]
                },
                "142875_trash can": {
                    "location": [508, 400, 39],
                    "rotation": [0.0, -0.0, 1.57],
                    "size": [23, 39, 51]
                },
                "5359367_office chair": {
                    "location": [122, 69, 69],
                    "rotation": [0.0, -0.0, 0.0],
                    "size": [62, 60, 92]
                },
                "3275938_a black bag": {
                    "location": [240, 50, 0],
                    "rotation": [0.0, -0.0, 1.57],
                    "size": [28, 26, 6]
                },
                "4875154_desk": {
                    "location": [83, 119, 73],
                    "rotation": [0.0, -0.0, 1.57],
                    "size": [146, 65, 72]
                },
                "3656479_desk": {
                    "location": [326, 401, 56],
                    "rotation": [0.0, -0.0, 3.14],
                    "size": [68, 138, 85]
                },
                "9979962_a black computer mouse": {
                    "location": [326, 401, 141],
                    "rotation": [0.0, -0.0, 1.57],
                    "size": [14, 8, 7]
                },
                "5169061_file cabinet": {
                    "location": [88, 438, 41],
                    "rotation": [0.0, 0.0, -1.57],
                    "size": [60, 79, 55]
                },
                "1723833_keyboard": {
                    "location": [227, 387, 137],
                    "rotation": [0.0, -0.0, 3.14],
                    "size": [35, 37, 1]
                },
                "6402090_cup": {
                    "location": [435, 60, 122],
                    "rotation": [0.0, 0.0, -1.57],
                    "size": [11, 16, 8]
                },
                "2130438_monitor": {
                    "location": [83, 119, 145],
                    "rotation": [0.0, -0.0, 0.0],
                    "size": [24, 50, 41]
                },
                "3947407_clock": {
                    "location": [316, 454, 15],
                    "rotation": [0.0, -0.0, 0.0],
                    "size": [32, 32, 3]
                },
                "7195964_keyboard": {
                    "location": [104, 176, 15],
                    "rotation": [0.0, -0.0, 0.0],
                    "size": [20, 44, 2]
                },
                "3307376_office chair": {
                    "location": [539, 339, 61],
                    "rotation": [0.0, -0.0, 1.57],
                    "size": [66, 65, 95]
                },
                "8642510_computer tower": {
                    "location": [466, 161, 33],
                    "rotation": [0.0, -0.0, 3.14],
                    "size": [32, 15, 39]
                },
                "1044621_box": {
                    "location": [146, 206, 27],
                    "rotation": [0.0, -0.0, 1.57],
                    "size": [36, 46, 27]
                },
                "6793254_box": {
                    "location": [278, 398, 26],
                    "rotation": [0.0, 0.0, -1.57],
                    "size": [33, 36, 25]
                },
                "5099795_divider": {
                    "location": [483, 91, 137],
                    "rotation": [0.0, -0.0, 3.14],
                    "size": [4, 142, 246]
                },
                "7363164_divider": {
                    "location": [295, 76, 126],
                    "rotation": [0.0, -0.0, 3.14],
                    "size": [7, 123, 225]
                },
                "9449825_office chair": {
                    "location": [343, 102, 62],
                    "rotation": [0.0, -0.0, 1.57],
                    "size": [74, 81, 97]
                },
                "4006788_office chair": {
                    "location": [77, 285, 62],
                    "rotation": [0.0, 0.0, -1.57],
                    "size": [61, 59, 97]
                },
                "2058751_a orange marker pen": {
                    "location": [412, 85, 122],
                    "rotation": [0.0, 0.0, -1.57],
                    "size": [14, 2, 2]
                },
                "8623329_a black keyboard": {
                    "location": [422, 90, 122],
                    "rotation": [0.0, -0.0, 0.0],
                    "size": [15, 45, 1]
                },
                "1618211_a silver laptop": {
                    "location": [430, 60, 122],
                    "rotation": [0.0, 0.0, -1.57],
                    "size": [26, 23, 18]
                },
                "1688211_file cabinet": {
                    "location": [30, 221, 42],
                    "rotation": [0.0, -0.0, 0.0],
                    "size": [59, 38, 56]
                },
                "8513474_file cabinet": {
                    "location": [386, 180, 54],
                    "rotation": [0.0, -0.0, 3.14],
                    "size": [93, 37, 56]
                },
                "3744248_desk": {
                    "location": [422, 75, 56],
                    "rotation": [0.0, -0.0, 3.14],
                    "size": [66, 150, 66]
                },
                "4441751_whiteboard": {
                    "location": [585, 216, 76],
                    "rotation": [0.0, -0.0, 3.14],
                    "size": [10, 178, 124]
                },
                "672610_backpack": {
                    "location": [480, 336, 31],
                    "rotation": [0.0, 0.0, -1.57],
                    "size": [27, 40, 35]
                },
                "9248640_office chair": {
                    "location": [43, 352, 63],
                    "rotation": [0.0, -0.0, 0.0],
                    "size": [71, 68, 98]
                },
                "1160541_a white pen": {
                    "location": [517, 413, 2],
                    "rotation": [0.0, 0.0, -1.57],
                    "size": [13, 1, 1]
                },
                "7300291_board": {
                    "location": [459, 189, 95],
                    "rotation": [0.0, -0.0, 1.57],
                    "size": [4, 54, 162]
                },
                "9371924_a white box": {
                    "location": [200, 50, 0],
                    "rotation": [0.0, 0.0, -1.57],
                    "size": [30, 34, 22]
                },
                "3616140_a blue book": {
                    "location": [415, 100, 122],
                    "rotation": [0.0, -0.0, 3.14],
                    "size": [21, 15, 2]
                },
                "1383887_office chair": {
                    "location": [117, 87, 63],
                    "rotation": [0.0, -0.0, 3.14],
                    "size": [67, 57, 99]
                },
                "6330067_box": {
                    "location": [386, 180, 55],
                    "rotation": [0.0, 0.0, -1.57],
                    "size": [38, 26, 25]
                },
                "7842737_monitor": {
                    "location": [222, 69, 101],
                    "rotation": [0.0, -0.0, 3.14],
                    "size": [19, 50, 44]
                }
                }

    iter = 3
    for objname in new_layout:
        new_layout[objname]["location"] = [round(x/100.0,2) for x in new_layout[objname]["location"]]
        new_layout[objname]["size"] = [round(x/100.0,2) for x in new_layout[objname]["size"]]
    json_name = f"/home/yandan/workspace/infinigen/Pipeline/record/update_ds_results_{iter}.json"
    with open(json_name, "w") as f:
        json.dump(new_layout, f, indent=4)