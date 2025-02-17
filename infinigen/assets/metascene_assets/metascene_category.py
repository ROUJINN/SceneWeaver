# Copyright (C) 2024, Princeton University.
# This source code is licensed under the BSD 3-Clause license found in the LICENSE file in the root directory of this source tree.

# Authors:
# - Karhan Kayan



import bpy
from infinigen.assets.utils.object import new_bbox
from infinigen.core.tagging import tag_support_surfaces
from .base import MetaSceneFactory


def metascene_object_factory(
    tag_support=False,
) -> MetaSceneFactory:
    """
    Create a factory for external asset import.
    tag_support: tag the planes of the object that are parallel to xy plane as support surfaces (e.g. shelves)
    """

    class MetaCategoryFactory(MetaSceneFactory):
        _category = None
        _asset_file = None
        def __init__(self, factory_seed, coarse=False):
            super().__init__(factory_seed, coarse)
            self.tag_support = tag_support
            self.category = self._category
            self.asset_file = self._asset_file


        def create_asset(self, **params) -> bpy.types.Object:
            bpy.ops.import_scene.gltf(filepath=self.asset_file)
            imported_obj = bpy.context.selected_objects[0]
            self.location_orig = imported_obj.location.copy()
            self.rotation = imported_obj.rotation_euler
            self.scale = imported_obj.scale

            if self.tag_support:
                tag_support_surfaces(imported_obj)


            bpy.context.view_layer.objects.active = (
                imported_obj  # Set as active object
            )
            imported_obj.select_set(True)  # Select the object
            bpy.ops.object.transform_apply(
                location=False, rotation=True, scale=True
            )
            
            if imported_obj:
                return imported_obj
            else:
                raise ValueError(f"Failed to import asset: {self.asset_file}")
        
        def create_placeholder(self, **kwargs) -> bpy.types.Object:
            return new_bbox(
                -1,1,-1,1,
                0,
                2,
            )

    return MetaCategoryFactory


# Create factory instances for different categories
GeneralMetaFactory = metascene_object_factory(tag_support=True)
