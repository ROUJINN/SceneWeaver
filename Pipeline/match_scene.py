
from gpt import GPT4 
from utils import extract_json, dict2str
import json

system_prompt = """
I want to design a scene based on the user's demand. 
I have already retrieved multiple scenes from the dataset. 
And now I need assistance in selecting the most similar scene that best matches the user's demand.
Help me identify the scene that aligns most closely with the user's demand.

You will reveive the following information:

1.User's demand of the scene
2.Roomtype: roomtype
3.Ideas about the scene
4.Category Counts for Candidate Scenes: Each key represents a scene_id, and the corresponding value is the count of objects per category within that scene.

You should return:
The scene id that aligns most closely with the user's demand.

Example Input:
1.User's demand: An office
2.Roomtype: bedroom
3.Ideas: Add basic bedroom
4.Category counts of candidate scenes: 
{
    "scene0001_00": {
        "a clear bottle": 1,
        "furnace": 1,
        "rack": 1,
        "table": 1,
        "sofa": 1
    },
    "scene0002_00": {
        "shelf": 2,
        "bucket": 3,
        "a yellow book": 1,
        "board": 1,
        "chair": 1
    }
}

    
Expected Output (only return scene_id):
scene0002_00

"""
user_prompt = """
Input:
User's demand: {user_demand}
Roomtype: {roomtype}
Ideas: {ideas}
Category counts of candidate scenes: {category_counts}

Your response:
"""

def match_scene_id(category_counts,user_demand,ideas,roomtype):
    category_counts = dict2str(category_counts)
    
    user_prompt_1 = user_prompt.format(user_demand=user_demand,
                                       roomtype=roomtype,
                                       ideas=ideas,
                                       category_counts = category_counts) 
        
    gpt = GPT4(version="4o")

    prompt_payload = gpt.get_payload(system_prompt, user_prompt_1)
    gpt_text_response = gpt(payload=prompt_payload, verbose=True)
    print(gpt_text_response)

    return gpt_text_response
    