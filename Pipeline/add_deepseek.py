import json
import re
from functools import reduce
import init_gpt_prompt as prompts0
import add_deepseek_prompt as prompts1
from deepseek import DeepSeek
from utils import extract_json, lst2str



def generate_scene_iter1_ds(user_demand,ideas,iter):

    ds = DeepSeek()

    results = dict()
    render_path = f"/home/yandan/workspace/infinigen/record_scene/render_{iter-1}.jpg"
    with open(f"/home/yandan/workspace/infinigen/record_scene/layout_{iter-1}.json", "r") as f:
        layout = json.load(f)

    roomsize = layout["roomsize"]
    roomsize_str = f"[{roomsize[0]},{roomsize[1]}]"
    step_1_big_object_prompt_user = prompts1.step_1_big_object_prompt_user.format(demand=user_demand, 
                                                                                ideas = ideas,
                                                                                roomsize = roomsize_str,
                                                                                scene_layout=layout["objects"])
    
    prompt_payload = ds.get_payload(prompts1.step_1_big_object_prompt_system, 
                                                 step_1_big_object_prompt_user)
    gpt_text_response = ds(payload=prompt_payload, verbose=True)
    print(gpt_text_response)

    gpt_dict_response = extract_json(gpt_text_response)
    results = gpt_dict_response
    # gpt_dict_response = {
    #             "User demand": "A cozy living room with a modern aesthetic, featuring a large sofa, a coffee table.",
    #             "Roomsize": [9.5, 4.0],
    #             "Number of new furniture": {"Plate": "2", "Bowl": "1", "Vase": "1", "FruitContainer": "1"},
    #             "category_against_wall": [],
    #             "Relation": [
    #                 ["vase", "dining_table", "ontop"],
    #                 ["plate", "dining_table", "ontop"],
    #                 ["bowl", "dining_table", "ontop"],
    #                 ["fruit_container", "dining_table", "ontop"]
    #             ],
    #             "Placement": {
    #                 "Vase": {
    #                     "1": {
    #                         "position": [1.45, 1.64, 1.01],
    #                         "rotation": 0,
    #                         "size": [0.2, 0.2, 0.3],
    #                         "parent": ["4320945_dining_table", "ontop"]
    #                     }
    #                 },
    #                 "Plate": {
    #                     "1": {
    #                         "position": [1.05, 1.64, 1.01],
    #                         "rotation": 0,
    #                         "size": [0.25, 0.25, 0.04],
    #                         "parent": ["4320945_dining_table", "ontop"]
    #                     },
    #                     "2": {
    #                         "position": [1.85, 1.64, 1.01],
    #                         "rotation": 0,
    #                         "size": [0.25, 0.25, 0.04],
    #                         "parent": ["4320945_dining_table", "ontop"]
    #                     }
    #                 },
    #                 "Bowl": {
    #                     "1": {
    #                         "position": [1.45, 1.94, 1.01],
    #                         "rotation": 0,
    #                         "size": [0.15, 0.15, 0.06],
    #                         "parent": ["4320945_dining_table", "ontop"]
    #                     }
    #                 },
    #                 "FruitContainer": {
    #                     "1": {
    #                         "position": [1.45, 1.34, 1.01],
    #                         "rotation": 0,
    #                         "size": [0.3, 0.3, 0.2],
    #                         "parent": ["4320945_dining_table", "ontop"]
    #                     }
    #                 }
    #             }
    #         }
    results = gpt_dict_response


    # #### 2. get object class name in infinigen
    category_list = gpt_dict_response["List of new furniture"]
    s = lst2str(list(category_list.keys()))
    user_prompt = prompts0.step_3_class_name_prompt_user.format(
        category_list=s, demand=user_demand
    )
    system_prompt = prompts0.step_3_class_name_prompt_system
    prompt_payload = ds.get_payload(system_prompt, user_prompt)
    gpt_text_response = ds(payload=prompt_payload, verbose=True)
    print(gpt_text_response)

    gpt_dict_response = extract_json(
        gpt_text_response.replace("'", '"').replace("None", "null")
    )
    name_mapping = gpt_dict_response["Mapping results"]
    results["name_mapping"] = name_mapping

    json_name = f"/home/yandan/workspace/infinigen/Pipeline/record/add_ds_results_{iter}.json"
    with open(json_name, "w") as f:
        json.dump(results, f, indent=4)
    return json_name

if __name__ == "__main__":
    # user_demand = "Add floor lamp next to the armchair and wall art above the sofa."
    user_demand = "Add vase with flowers on the coffee table, magazines, and remote controls on the TV stand."
    generate_scene_iter1_ds(user_demand,iter=4)
