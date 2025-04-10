# Copyright (C) 2023, Princeton University.
# This source code is licensed under the BSD 3-Clause license found in the LICENSE file in the root directory
# of this source tree.

import argparse
import logging
from pathlib import Path

from numpy import deg2rad

# ruff: noqa: E402
# NOTE: logging config has to be before imports that use logging
logging.basicConfig(
    format="[%(asctime)s.%(msecs)03d] [%(module)s] [%(levelname)s] | %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
import sys
import os
import bpy
import gin
import numpy as np

from infinigen import repo_root
from infinigen.assets import lighting
from infinigen.assets.materials import invisible_to_camera
from infinigen.assets.objects.wall_decorations.skirting_board import make_skirting_board
from infinigen.assets.placement.floating_objects import FloatingObjectPlacement
from infinigen.assets.utils.decorate import read_co
from infinigen.core import execute_tasks, init, placement, surface, tagging
from infinigen.core import tags as t
from infinigen.core.constraints import checks
from infinigen.core.constraints import constraint_language as cl
from infinigen.core.constraints import reasoning as r
from infinigen.core.constraints.example_solver import (
    Solver,
    greedy,
    populate,
    state_def,
)
from infinigen.core.constraints.example_solver.room import constants
from infinigen.core.constraints.example_solver.room import decorate as room_dec
from infinigen.core.constraints.example_solver.room.constants import WALL_HEIGHT
from infinigen.core.placement import camera as cam_util
from infinigen.core.util import blender as butil
from infinigen.core.util import pipeline
from infinigen.core.util.camera import points_inview
from infinigen.core.util.test_utils import (
    import_item,
    load_txt_list,
)
from infinigen.terrain import Terrain
from infinigen_examples.indoor_constraint_examples import home_constraints
from infinigen_examples.util import constraint_util as cu
from infinigen_examples.util.generate_indoors_util import (
    apply_greedy_restriction,
    create_outdoor_backdrop,
    hide_other_rooms,
    place_cam_overhead,
    restrict_solving,
)
from infinigen_examples.util.visible import invisible_others, visible_others
import pickle
from infinigen_examples.steps import (
        basic_scene,
        room_structure, 
        init_graph, 
        solve_objects, 
        camera,
        populate_placeholder,
        light,
        update_graph,
        record,
        complete_structure
    )
    
logger = logging.getLogger(__name__)

all_vars = [cu.variable_room, cu.variable_obj]

@gin.configurable
def compose_indoors(output_folder: Path, scene_seed: int, iter, action, json_name, description, inplace, **overrides):
    height = 1


    consgraph = home_constraints()
    stages = basic_scene.default_greedy_stages()
    checks.check_all(consgraph, stages, all_vars)

    stages, consgraph, limits = restrict_solving(stages, consgraph)
    p = pipeline.RandomStageExecutor(scene_seed, output_folder, overrides)

    os.environ["JSON_RESULTS"] = json_name
    if iter==0:
        p,terrain = basic_scene.basic_scene(scene_seed,output_folder,overrides,logger,p)
        os.environ["ROOM_INFO"] = "/home/yandan/workspace/infinigen/roominfo.json"
        state,solver,override = room_structure.build_room_structure(p,overrides,stages,logger,output_folder,scene_seed,consgraph)
        
        light.turn_off(p)

        camera_rigs,solved_rooms,house_bbox,solved_bbox = camera.animate_camera(state,stages,limits,solver,p)

        match action:
            case "init_physcene": 
                state,solver = init_graph.init_physcene(stages,limits,solver,state,p)
                
            case "init_metascene":
                state,solver = init_graph.init_metascene(stages,limits,solver,state,p)
            case "init_gpt":
                solver.load_gpt_results()
                state,solver = init_graph.init_gpt(stages,limits,solver,state,p) 
            case _ :
                raise ValueError(f"Action is wrong: {action}") 
    else:
        if action=="add_acdc" and inplace:
            load_iter = iter
        else:
            load_iter = iter - 1
        state,solver,terrain,house_bbox,solved_bbox = record.load_scene(load_iter)
        camera_rigs = [bpy.data.objects.get('CameraRigs/0')]
        match action:
            case "solve_large":
                state,solver = solve_objects.solve_large_object(stages,limits,solver,state,p,consgraph,overrides)
            case "solve_medium":
                state,solver = solve_objects.solve_medium_object(stages,limits,solver,state,p,consgraph,overrides)
            case "solve_large_and_medium":
                state,solver = solve_objects.solve_large_and_medium_object(stages,limits,solver,state,p,consgraph,overrides)
            case "solve_small":
                state,solver = solve_objects.solve_small_object(stages,limits,solver,state,p,consgraph,overrides)
            case "add_gpt":
                state,solver = update_graph.add_gpt(stages,limits,solver,state,p)
            case "add_acdc":
                state,solver = update_graph.add_acdc(solver,state,p,description)
            case "add_rule":
                state,solver = update_graph.add_rule(stages,limits,solver,state,p)
            case "export_supporter":
                record.export_supporter(state, obj_name=description, export_path = "record_files/obj.blend")
                sys.exit()
            case "update":
                state,solver = update_graph.update(solver,state,p)
            case "modify":
                state,solver = update_graph.modify(stages,limits,solver,p)
            case "add_relation":
                state,solver = update_graph.add_new_relation(stages,limits,solver,p)
            case "finalize_scene":
                solved_rooms = [bpy.data.objects.get(bpy.data.objects['newroom_0-0'])]
                height = complete_structure.finalize_scene(overrides,stages,state,solver,output_folder,p,terrain,solved_rooms,house_bbox,camera_rigs)
            case _:
                raise ValueError(f"Action is wrong: {action}") 
        
    solver.del_no_relation_objects()
    
    state,solver = solve_objects.solve_large_object(stages,limits,solver,state,p,consgraph,overrides)

    # state,solver = solve_objects.solve_medium_object(stages,limits,solver,state,p,consgraph,overrides)
    # state,solver = solve_objects.solve_small_object(stages,limits,solver,state,p,consgraph,overrides)
    record.record_scene(state,solver,terrain,house_bbox,solved_bbox,camera_rigs,iter,p)

    # populate_placeholder.populate_intermediate_pholders(p,state)

    return {
        "height_offset": height,
        "whole_bbox": house_bbox,
    }


def main(args):

    scene_seed = init.apply_scene_seed(args.seed)
    init.apply_gin_configs(
        configs=["base_indoors.gin"] + args.configs,
        overrides=args.overrides,
        config_folders=[
            "infinigen_examples/configs_indoor",
            "infinigen_examples/configs_nature",
        ],
    )
    constants.initialize_constants()

    execute_tasks.main(
        compose_scene_func=compose_indoors,
        iter=args.iter,
        action=args.action,
        json_name=args.json_name,
        description=args.description,
        inplace=args.inplace,
        populate_scene_func=None,
        input_folder=args.input_folder,
        output_folder=args.output_folder,
        task=args.task,
        task_uniqname=args.task_uniqname,
        scene_seed=scene_seed,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()                                                     
    parser.add_argument("--iter", type=int, default=0)
    parser.add_argument("--action", type=str, default="init_physcene")
    parser.add_argument("--json_name", type=str, default="")
    parser.add_argument("--description", type=str, default="")
    parser.add_argument("--inplace", type=str, default="")
    parser.add_argument("--output_folder", type=Path)
    parser.add_argument("--input_folder", type=Path, default=None)
    parser.add_argument(
        "-s", "--seed", default=None, help="The seed used to generate the scene"
    )
    parser.add_argument(
        "-t",
        "--task",
        nargs="+",
        default=["coarse"],
        choices=[
            "coarse",
            "populate",
            "fine_terrain",
            "ground_truth",
            "render",
            "mesh_save",
            "export",
        ],
    )
    parser.add_argument(
        "-g",
        "--configs",
        nargs="+",
        default=["base"],
        help="Set of config files for gin (separated by spaces) "
        "e.g. --gin_config file1 file2 (exclude .gin from path)",
    )
    parser.add_argument(
        "-p",
        "--overrides",
        nargs="+",
        default=[],
        help="Parameter settings that override config defaults "
        "e.g. --gin_param module_1.a=2 module_2.b=3",
    )
    parser.add_argument("--task_uniqname", type=str, default=None)
    parser.add_argument("-d", "--debug", type=str, nargs="*", default=None)

    # invisible_others()
    # bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
    # visible_others()

    args = init.parse_args_blender(parser)
    logging.getLogger("infinigen").setLevel(logging.INFO)
    logging.getLogger("infinigen.core.nodes.node_wrangler").setLevel(logging.CRITICAL)

    if args.debug is not None:
        for name in logging.root.manager.loggerDict:
            if not name.startswith("infinigen"):
                continue
            if len(args.debug) == 0 or any(name.endswith(x) for x in args.debug):
                logging.getLogger(name).setLevel(logging.DEBUG)

    import json
    with open("args.json","r") as f:
        j = json.load(f)
        args.iter = j["iter"]
        args.action = j["action"]
        args.description = j["description"]
        args.inplace = j["inplace"]
        args.json_name = j["json_name"]

    os.system(f"cp args.json args_{args.iter}.json")

    


    main(args)
