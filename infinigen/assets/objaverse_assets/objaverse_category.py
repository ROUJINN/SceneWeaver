# Copyright (C) 2024, Princeton University.
# This source code is licensed under the BSD 3-Clause license found in the LICENSE file in the root directory of this source tree.

# Authors:
# - Karhan Kayan

import os
import random

import bpy

from .base import ObjaverseFactory
from infinigen.assets.utils.object import new_bbox
from infinigen.core.tagging import tag_support_surfaces
from infinigen.core.util.math import FixedSeed
from GPT.constants import OBJATHOR_ASSETS_DIR

from .load_asset import load_pickled_3d_asset
from GPT.objaverse_retriever import ObjathorRetriever
from GPT.retrieve import ObjectRetriever

global Retriever
Retriever = ObjectRetriever()


def objaverse_category_factory(
    tag_support=False,
) -> ObjaverseFactory:
    """
    Create a factory for external asset import.
    tag_support: tag the planes of the object that are parallel to xy plane as support surfaces (e.g. shelves)
    """

    class ObjaverseCategoryFactory(ObjaverseFactory):
        def __init__(self, factory_seed, coarse=False):
            super().__init__(factory_seed, coarse)
            self.tag_support = tag_support
               
        # def set_info(self, x_dim, y_dim, z_dim, category):
        #     self.x_dim = x_dim
        #     self.y_dim = y_dim
        #     self.z_dim = z_dim
        #     self.category = category

        #     return

        def create_asset(self, **params) -> bpy.types.Object:
            
            object_names = Retriever.retrieve_object_by_cat(self.category)
            object_names = [name for name, score in object_names if score > 30]
            random.shuffle(object_names)

            for obj_name in object_names:
                basedir = OBJATHOR_ASSETS_DIR
                # indir = f"{basedir}/processed_2023_09_23_combine_scale"
                filename = f"{basedir}/{obj_name}/{obj_name}.pkl.gz"
                try:
                    imported_obj = load_pickled_3d_asset(filename)
                    break
                except:
                    continue

            #resize
            if (
                self.x_dim is not None
                or self.y_dim is not None
                or self.z_dim is not None
            ):
                # check only one dimension is provided
                # if (
                #     sum(
                #         [
                #             1
                #             for dim in [self.x_dim, self.y_dim, self.z_dim]
                #             if dim is not None
                #         ]
                #     )
                #     != 1
                # ):
                #     raise ValueError("Only one dimension can be provided")
                
                if self.x_dim is not None:
                    scale_x = self.x_dim / imported_obj.dimensions[0]
                if self.y_dim is not None:
                    scale_y = self.y_dim / imported_obj.dimensions[1]
                if self.z_dim is not None:
                    scale_z = self.z_dim / imported_obj.dimensions[2]
                imported_obj.scale = (scale_x, scale_y, scale_z)
                bpy.context.view_layer.objects.active = imported_obj  # Set as active object
                imported_obj.select_set(True)  # Select the object
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

            if self.tag_support:
                tag_support_surfaces(imported_obj)

            if imported_obj:
                return imported_obj
            else:
                raise ValueError(f"Failed to import asset: {self.asset_file}")

        def create_placeholder(self, **kwargs) -> bpy.types.Object:
            return new_bbox(
                -self.x_dim / 2,
                self.x_dim / 2,
                -self.y_dim / 2,
                self.y_dim / 2,
                0,
                self.z_dim,
            )

    return ObjaverseCategoryFactory


# Create factory instances for different categories
GeneralObjavFactory = objaverse_category_factory(tag_support=True)
