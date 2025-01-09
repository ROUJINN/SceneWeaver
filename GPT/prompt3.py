from gpt import GPT4 as gpt
import prompts as prompts
from functools import reduce



import json
import re


def extract_data(input_string):
    # First, try to extract a JSON object
    json_match = re.search(r"{.*?}", input_string, re.DOTALL)
    if json_match:
        extracted_json = json_match.group(0)
        try:
            # Convert the extracted JSON string into a Python dictionary
            json_dict = json.loads(extracted_json)
            return json_dict
        except json.JSONDecodeError:
            print(input_string)
            print("Error while decoding the JSON.")
            return None

    # If no JSON object, try to extract a Python-style list
    list_match =  re.findall(r"\[.*?\]", input_string, re.DOTALL)
    if list_match:
        try:
            # extracted_list = list_match #list_match.group(0)
            extracted_list = [re.split(r",\s*", match.strip("[]")) for match in list_match]
            # Safely evaluate the extracted list string
            # list_data = re.split(r'[,\[\]]', extracted_list)
            # list_data = [data for data in list_data if len(data)>0]
            return extracted_list
        except (ValueError, SyntaxError):
            print(input_string)
            print("Error while decoding the list.")
            return None

    print("No valid JSON or list found.")
    return None

def lst2str(lst):
    if isinstance(lst[0], list):
        lst = ["["+", ".join(i)+"]" for i in lst]
        lst = "\n".join(lst)
    else:
        return "["+", ".join(lst)+"]"

    return lst

gpt = gpt()

roomtype = "Living Room"
results = dict()
### 1. get big object, count, and relation
user_prompt = prompts.step_1_big_object_prompt_user.format(roomtype=roomtype)
prompt_payload = gpt.get_payload(prompts.step_1_big_object_prompt_system,user_prompt)
gpt_text_response = gpt(payload=prompt_payload, verbose=True)
print(gpt_text_response)

response = [i for i in gpt_text_response.split("\n") if len(i)>0]
big_category_dict = extract_data(response[0])
big_category_list = list(big_category_dict.keys())
category_against_wall = extract_data(response[1])[0]
relation_big_object = [extract_data(i) for i in response[2:]]
relation_big_object = [i for i in relation_big_object if i is not None]
relation_big_object = reduce(lambda x, y: x + y, relation_big_object)


# # Category list of big objects: [1 checkout counter, 5 bookshelves, 2 reading tables, 8 chairs]
# # Object against the wall: [bookshelves]
# # Relation between big objects: [chair, reading table, front_against]


#### 2. get small object and relation
s = lst2str(big_category_list)
# s = "[bookshelves, reading tables, chairs, checkout counter]"
user_prompt = prompts.step_2_small_object_prompt_user.format(big_category_list=s,roomtype=roomtype)
prompt_payload = gpt.get_payload(prompts.step_2_small_object_prompt_system, user_prompt)
gpt_text_response = gpt(payload=prompt_payload, verbose=True)

response = [i for i in gpt_text_response.split("\n") if (len(i)>0 and "[" in i and "]" in i)]
response = [i.replace("\"","") for i in response]
small_category_list = extract_data(response[0])[0]
relation_small_object = [extract_data(i) for i in response[1:]]
relation_small_object = [i for i in relation_small_object if i is not None]
relation_small_object = reduce(lambda x, y: x + y, relation_small_object)

# List of small furniture: ["books", "lamps", "magazines", "decorative items", "cash register"]
# Relation: [
#     ["books", "bookshelves", "on", 50],
#     ["lamps", "reading tables", "ontop", 4],
#     ["magazines", "reading tables", "ontop", 6],
#     ["decorative items", "checkout counter", "ontop", 3],
#     ["cash register", "checkout counter", "ontop", 1]
# ]



#### 3. get object class name in infinigen
category_list = big_category_list + small_category_list
s = lst2str(category_list)
user_prompt = prompts.step_3_class_name_prompt_user.format(category_list=s,roomtype=roomtype)
prompt_payload = gpt.get_payload(prompts.step_3_class_name_prompt_system, user_prompt)
gpt_text_response = gpt(payload=prompt_payload, verbose=True)

name_mapping = extract_data(gpt_text_response.replace("'","\"").replace("None", "null"))
# Mapping results: {
#     "books": 'table_decorations.BookFactory',
#     "bookmarks": None,
#     "lamps": 'lamp.DeskLampFactory',
#     "reading glasses": None,
#     "cash register": None,
#     "decorative items": None
# }

#### 4. generate rule code

def get_rule_prompt(
        big_category_list,
        small_category_list,
        relation_big_object,
        relation_small_object,
        big_category_dict,
        roomtype,
        name_mapping
        ):
    
    var_dict = dict()
    for name in big_category_list:
        if name_mapping[name] is None:
            big_category_dict.pop(name)
            continue
        var_name = name.replace(" ","_")+"_obj"
        info = var_name + " = "
        if name in category_against_wall:
            info += "wallfurn"
        else:
            info += "furniture"
        info += "[" + name_mapping[name] + "]"
        var_dict[name] = {"var_name":var_name,"info":info}

    for name in small_category_list:
        if name_mapping[name] is None:
            continue
        var_name = name.replace(" ","_")+"_obj"
        info = var_name + " = "
        info += "obj"
        info += "[" + name_mapping[name] + "]"
        var_dict[name] = {"var_name":var_name,"info":info}

    rel_small_big_object_name = set()
    for rel in relation_small_object.copy():
        obj1name,obj2name,relation,cnt = rel
        if obj1name not in var_dict or obj2name not in var_dict:
            relation_small_object.remove(rel)
            continue
        else:
            rel_small_big_object_name.add(obj2name)

    for rel in relation_big_object.copy():
        obj1name,obj2name,relation = rel
        if obj1name not in var_dict or obj2name not in var_dict:
            relation_big_object.remove(rel)
            continue
        relation = "cu."+relation
        if "related" in var_dict[obj1name]["info"]:
            import pdb
            pdb.set_trace()
        if obj1name in rel_small_big_object_name:
            continue
        var_name = var_dict[obj2name]["var_name"]
        var_dict[obj1name]["info"] += f".related_to({var_name},{relation})"

    vars_definition_1 = [var["info"] for var in var_dict.values() if "related" not in var["info"]]
    vars_definition_2 = [var["info"] for var in var_dict.values() if "related" in var["info"]]
    vars_definition = "\n".join(vars_definition_1+vars_definition_2)

    big_category_cnt_str = json.dumps(big_category_dict)
    relation_big_object_str = lst2str(relation_big_object)
    relation_small_object_str = lst2str(relation_small_object)

    user_prompt =  prompts.step_4_rule_prompt_user.format(
        big_category_cnt = big_category_cnt_str,
        relation_big_object = relation_big_object_str,
        relation_small_object = relation_small_object_str,
        vars_definition = vars_definition,
        roomtype=roomtype
    )
    print(user_prompt)
    return user_prompt

user_prompt = get_rule_prompt(big_category_list, small_category_list, relation_big_object, relation_small_object, big_category_dict, roomtype, name_mapping)
prompt_payload = gpt.get_payload(prompts.step_4_rule_prompt_system,user_prompt)
gpt_text_response = gpt(payload=prompt_payload, verbose=True)
gpt_text_response = gpt_text_response.replace("{{","{").replace("}}","}")
print(gpt_text_response)


results["big_category_dict"] = big_category_dict
results["category_against_wall"] = category_against_wall
results["relation_big_object"] = relation_big_object
results["small_category_list"] = small_category_list
results["relation_small_object"] = relation_small_object
results["name_mapping"] = name_mapping
results["gpt_text_response"] = gpt_text_response
with open("results.json","w") as f:
    json.dump(results,f,indent=4)