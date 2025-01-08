################## list all Semantics category #####################
from infinigen.core.tags import Semantics
semantic_member = list((Semantics.__members__).values())

################## list all object factory #####################
from infinigen.assets.objects import (
    appliances,
    bathroom,
    decor,
    elements,
    lamp,
    seating,
    shelves,
    table_decorations,
    tables,
    tableware,
    wall_decorations,
)
import inspect

imported_modules = {
    'appliances':appliances,
    'bathroom':bathroom,
    'decor':decor,
    'elements':elements,
    'lamp':lamp,
    'seating':seating,
    'shelves':shelves,
    'table_decorations':table_decorations,
    'tables':tables,
    'tableware':tableware,
    'wall_decorations':wall_decorations,
}

def get_classes_from_module(module=seating):
    return [name for name, obj in vars(module).items() if inspect.isclass(obj)]

modulenames = []
for modulename, module in imported_modules.items():
    class_list = get_classes_from_module(module)
    modulenames += [modulename+"."+name for name in class_list]

############# load spatial constraints ###############
from infinigen_examples.util import constraint_util as cu

def get_local_variables(module):
    # Get all attributes of the module
    variables = {}
    for name, obj in vars(module).items():
        # Exclude imports and built-in attributes
        if not (name.startswith("__") or inspect.ismodule(obj) or inspect.isfunction(obj) or inspect.isclass(obj)):
            variables[name] = obj
    return variables

local_variables = get_local_variables(cu) 


# relation = [key for key, value in local_variables.items() if not isinstance(value, set) ]
relation = ['on_floor', 'flush_wall', 'against_wall', 'spaced_wall', 'hanging', 'side_against_wall', 
            'ontop', 'on', 'front_against', 'front_to_front', 'leftright_leftright', 'side_by_side', 'back_to_back']

################ room type #########################
room_types = local_variables['room_types']

################ example of rule  ####################

rules_example="""
    rooms = cl.scene()[{Semantics.Room, -Semantics.Object}]
    obj = cl.scene()[{Semantics.Object, -Semantics.Room}]

    cutters = cl.scene()[Semantics.Cutter]
    window = cutters[Semantics.Window]
    doors = cutters[Semantics.Door]

    constraints = OrderedDict()
    score_terms = OrderedDict()

    # region overall fullness

    furniture = obj[Semantics.Furniture].related_to(rooms, cu.on_floor)
    wallfurn = furniture.related_to(rooms, cu.against_wall)
    storage = wallfurn[Semantics.Storage]

    # region CLOSETS
    closets = rooms[Semantics.Closet].excludes(cu.room_types)
    constraints["closets"] = closets.all(
        lambda r: (
            (storage.related_to(r).count() >= 1)
            * ceillights.related_to(r, cu.hanging).count().in_range(0, 1)
            * (
                walldec.related_to(r).count() == 0
            )  # special case exclusion - no paintings etc in closets
        )
    )
    score_terms["closets"] = closets.all(
        lambda r: (
            storage.related_to(r).count().maximize(weight=2)
            * obj.related_to(storage.related_to(r)).count().maximize(weight=2)
        )
    )

    # endregion

    # region LIVINGROOMS

    livingrooms = rooms[Semantics.LivingRoom].excludes(cu.room_types)
    sofas = furniture[seating.SofaFactory]
    tvstands = wallfurn[shelves.TVStandFactory]
    coffeetables = furniture[tables.CoffeeTableFactory]

    sofa_back_near_wall = cl.StableAgainst(
        cu.back, cu.walltags, margin=uniform(0.1, 0.3)
    )
    cl.StableAgainst(cu.side, cu.walltags, margin=uniform(0.1, 0.3))

    def freestanding(o, r):
        return o.related_to(r).related_to(r, -sofa_back_near_wall)

    constraints["sofa"] = livingrooms.all(
        lambda r: (
            # sofas.related_to(r).count().in_range(2, 3)
            sofas.related_to(r, sofa_back_near_wall).count().in_range(2, 4)
            # * sofas.related_to(r, sofa_side_near_wall).count().in_range(0, 1)
            * freestanding(sofas, r).all(
                lambda t: (  # frustrum infront of freestanding sofa must directly contain tvstand
                    cl.accessibility_cost(t, tvstands.related_to(r), dist=3) > 0.7
                )
            )
            * sofas.all(
                lambda t: (
                    cl.accessibility_cost(t, furniture.related_to(r), dist=2).in_range(
                        0, 0.5
                    )
                    * cl.accessibility_cost(t, r, dist=1).in_range(0, 0.5)
                )
            )
            
        )
    )

    constraints["sofa_positioning"] = rooms.all(
        lambda r: (
            sofas.all(
                lambda s: (
                    (cl.accessibility_cost(s, rooms, dist=3) < 0.5)
                    * (
                        cl.focus_score(s, tvstands.related_to(r)) > 0.5
                    )  # must face or perpendicular to TVStand
                )
            )
        )
    )

    score_terms["sofa"] = livingrooms.mean(
        lambda r: (
            sofas.volume().maximize(weight=10)
            + sofas.related_to(r).mean(
                lambda t: (
                    t.distance(sofas.related_to(r)).hinge(0, 1).minimize(weight=1)
                    + t.distance(tvstands.related_to(r)).hinge(2, 3).minimize(weight=5)
                    + cl.focus_score(t, tvstands.related_to(r)).maximize(weight=5)
                    + cl.angle_alignment_cost(
                        t, tvstands.related_to(r), cu.front
                    ).minimize(weight=1)
                    + cl.focus_score(t, coffeetables.related_to(r)).maximize(weight=2)
                    + cl.accessibility_cost(t, r, dist=3).minimize(weight=3)
                )
            )
            + freestanding(sofas, r).mean(
                lambda t: (
                    cl.angle_alignment_cost(t, tvstands.related_to(r)).minimize(
                        weight=5
                    )
                    + cl.angle_alignment_cost(t, r, cu.walltags).minimize(weight=3)
                    + cl.center_stable_surface_dist(t).minimize(weight=0.5)
                )
            )
        )
    )

    tvs = obj[appliances.TVFactory].related_to(tvstands, cu.ontop)

    if params["has_tv"]:
        constraints["tv"] = livingrooms.all(
            lambda r: (
                tvstands.related_to(r).all(
                    lambda t: (
                        (tvs.related_to(t).count() == 1)
                        * tvs.related_to(t).all(
                            lambda tv: cl.accessibility_cost(tv, r, dist=1).in_range(
                                0, 0.1
                            )
                        )
                    )
                )
            )
        )

    score_terms["tvstand"] = rooms.all(
        lambda r: (
            tvstands.mean(
                lambda stand: (
                    tvs.related_to(stand).volume().maximize(weight=1)
                    + stand.distance(window).maximize(
                        weight=1
                    )  # penalize being very close to window. avoids tv blocking window.
                    + cl.accessibility_cost(stand, furniture).minimize(weight=3)
                    + cl.center_stable_surface_dist(stand).minimize(
                        weight=5
                    )  # center tvstand against wall (also tries to do vertical & floor but those are constrained)
                    + cl.center_stable_surface_dist(tvs.related_to(stand)).minimize(
                        weight=1
                    )
                )
            )
        )
    )

    constraints["livingroom"] = livingrooms.all(
        lambda r: (
            storage.related_to(r).count().in_range(1, 5)
            * tvstands.related_to(r).count().equals(1)
            * (  # allow sidetables next to any sofa
                sidetable.related_to(r)
                .related_to(sofas.related_to(r), cu.side_by_side)
                .count()
                .in_range(0, 2)
            )
            * desks.related_to(r).count().in_range(0, 1)
            * coffeetables.related_to(r).count().in_range(0, 1)
            * coffeetables.related_to(r).all(
                lambda t: (
                    obj[Semantics.OfficeShelfItem]
                    .related_to(t, cu.on)
                    .count()
                    .in_range(0, 3)
                )
            )
            * (
                rugs.related_to(r)
                # .related_to(furniture.related_to(r), cu.side_by_side)
                .count()
                .in_range(0, 2)
            )
        )
    )
   
    score_terms["livingroom"] = livingrooms.mean(
        lambda r: (
            coffeetables.related_to(r).mean(
                lambda t: (
                    # ideal coffeetable-to-tv distance according to google
                    t.distance(sofas.related_to(r)).hinge(0.45, 0.6).minimize(weight=5)
                    + cl.angle_alignment_cost(
                        t, sofas.related_to(r), cu.front
                    ).minimize(weight=5)
                    + cl.focus_score(sofas.related_to(r), t).maximize(weight=5)
                )
            )
        )
    )
   
    constraints["livingroom_objects"] = livingrooms.all(
        lambda r: (
            storage.all(
                lambda t: (
                    obj[Semantics.OfficeShelfItem].related_to(t, cu.on).count()
                    >= 0  
                )
            )
            * coffeetables.all(
                lambda t: (
                    obj[Semantics.TableDisplayItem]
                    .related_to(t, cu.ontop)
                    .count()
                    .in_range(0, 1)
                    * (obj[Semantics.OfficeShelfItem].related_to(t, cu.on).count() >= 0)
                )
            )
        )
    )

    # endregion

"""

prompt = f"""
You are an experienced layout designer that place 3D assets into a scene. 
Your goal is to design the asset's placement rule using a Python-based DSL.

You will receive:
1. The room type you need to design.
2. A category list of the 3D assets.
3. A semantic list of the grouped categories.
4. A list of relation you can use in the rule to define the relation between 2 assets.
5. An example of rules for CLOSETS and LIVINGROOMS

Your task is to write a program that:
1. Specifies rules of the asset placements for the given roomtype.
2. Return both constraints and score_terms for the asset placements. 

Follow these instructions carefully:
1. Do not name the variable with the same name of {imported_modules.keys()}. For example, use "sofas = furniture[seating.SofaFactory]" instead of "seating = furniture[seating.SofaFactory]".
2. "wallfurn" is defined as "furniture.related_to(rooms, cu.against_wall)", which means objects against wall.
3. "furniture" is defined as "obj[Semantics.Furniture].related_to(rooms, cu.on_floor)", which means objects on the floor.

ROOM TYPE: Bookstore
CATEGORY LIST: {modulenames}
SEMANTIC LIST: {semantic_member}
RELATION LIST: {relation}

EXAMPLE: {rules_example}

Please show me your rules for the given roomtype:
"""



print(prompt)



"""
You are an experienced layout designer that place 3D assets into a scene. 
Your goal is to design the asset's placement rule using a Python-based DSL.

You will receive:
1. The room type you need to design.
2. A specific category list of the 3D assets.
3. A semantic list of the grouped categories.
4. A list of relation you can use in the rule to define the relation between 2 assets.
5. An example of rules for CLOSETS and LIVINGROOMS

Your task is to write a program that:
1. Specifies rules of the asset placements for the given roomtype.
2. Return both constraints and score_terms for the asset placements. 

Follow these instructions carefully:
1. Do not name the variable with the name of ['appliances','bathroom':bathroom,'decor','elements','lamp','seating','shelves','table_decorations','tables','tableware','wall_decorations']. For example, use "sofas = furniture[seating.SofaFactory]" instead of "seating = furniture[seating.SofaFactory]".
2. "wallfurn" is defined as "furniture.related_to(rooms, cu.against_wall)", which means objects against wall.
3. "furniture" is defined as "obj[Semantics.Furniture].related_to(rooms, cu.on_floor)", which means objects on the floor.

room type: Bookstore
category list: ['appliances.BeverageFridgeFactory', 'appliances.DishwasherFactory', 'appliances.MicrowaveFactory', 'appliances.OvenFactory', 'appliances.MonitorFactory', 'appliances.TVFactory', 'bathroom.BathroomSinkFactory', 'bathroom.StandingSinkFactory', 'bathroom.BathtubFactory', 'bathroom.HardwareFactory', 'bathroom.ToiletFactory', 'decor.AquariumTankFactory', 'elements.DoorCasingFactory', 'elements.GlassPanelDoorFactory', 'elements.LiteDoorFactory', 'elements.LouverDoorFactory', 'elements.PanelDoorFactory', 'elements.NatureShelfTrinketsFactory', 'elements.PillarFactory', 'elements.RugFactory', 'elements.CantileverStaircaseFactory', 'elements.CurvedStaircaseFactory', 'elements.LShapedStaircaseFactory', 'elements.SpiralStaircaseFactory', 'elements.StraightStaircaseFactory', 'elements.UShapedStaircaseFactory', 'elements.PalletFactory', 'elements.RackFactory', 'lamp.CeilingClassicLampFactory', 'lamp.CeilingLightFactory', 'lamp.DeskLampFactory', 'lamp.FloorLampFactory', 'lamp.LampFactory', 'seating.BedFactory', 'seating.BedFrameFactory', 'seating.BarChairFactory', 'seating.ChairFactory', 'seating.OfficeChairFactory', 'seating.MattressFactory', 'seating.PillowFactory', 'seating.ArmChairFactory', 'seating.SofaFactory', 'shelves.CellShelfFactory', 'shelves.TVStandFactory', 'shelves.CountertopFactory', 'shelves.CabinetDoorBaseFactory', 'shelves.KitchenCabinetFactory', 'shelves.KitchenIslandFactory', 'shelves.KitchenSpaceFactory', 'shelves.LargeShelfFactory', 'shelves.SimpleBookcaseFactory', 'shelves.SidetableDeskFactory', 'shelves.SimpleDeskFactory', 'shelves.SingleCabinetFactory', 'shelves.TriangleShelfFactory', 'table_decorations.BookColumnFactory', 'table_decorations.BookFactory', 'table_decorations.BookStackFactory', 'table_decorations.SinkFactory', 'table_decorations.TapFactory', 'table_decorations.VaseFactory', 'tables.TableCocktailFactory', 'tables.CoffeeTableFactory', 'tables.SideTableFactory', 'tables.TableDiningFactory', 'tables.TableTopFactory', 'tableware.BottleFactory', 'tableware.BowlFactory', 'tableware.CanFactory', 'tableware.ChopsticksFactory', 'tableware.CupFactory', 'tableware.FoodBagFactory', 'tableware.FoodBoxFactory', 'tableware.ForkFactory', 'tableware.SpatulaFactory', 'tableware.FruitContainerFactory', 'tableware.JarFactory', 'tableware.KnifeFactory', 'tableware.LidFactory', 'tableware.PanFactory', 'tableware.LargePlantContainerFactory', 'tableware.PlantContainerFactory', 'tableware.PlateFactory', 'tableware.PotFactory', 'tableware.SpoonFactory', 'tableware.WineglassFactory', 'wall_decorations.BalloonFactory', 'wall_decorations.RangeHoodFactory', 'wall_decorations.MirrorFactory', 'wall_decorations.WallArtFactory', 'wall_decorations.WallShelfFactory']
semantic list: [Semantics.Room, Semantics.Object, Semantics.Cutter, Semantics.Kitchen, Semantics.Bedroom, Semantics.LivingRoom, Semantics.Closet, Semantics.Hallway, Semantics.Bathroom, Semantics.Garage, Semantics.Balcony, Semantics.DiningRoom, Semantics.Utility, Semantics.Staircase, Semantics.Office, Semantics.Furniture, Semantics.FloorMat, Semantics.WallDecoration, Semantics.HandheldItem, Semantics.Storage, Semantics.Seating, Semantics.LoungeSeating, Semantics.Table, Semantics.Bathing, Semantics.SideTable, Semantics.Watchable, Semantics.Desk, Semantics.Bed, Semantics.Sink, Semantics.CeilingLight, Semantics.Lighting, Semantics.KitchenCounter, Semantics.KitchenAppliance, Semantics.TableDisplayItem, Semantics.OfficeShelfItem, Semantics.KitchenCounterItem, Semantics.FoodPantryItem, Semantics.BathroomItem, Semantics.ShelfTrinket, Semantics.Dishware, Semantics.Cookware, Semantics.Utensils, Semantics.ClothDrapeItem, Semantics.Objaverse, Semantics.AccessTop, Semantics.AccessFront, Semantics.AccessAnySide, Semantics.AccessAllSides, Semantics.AccessStandingNear, Semantics.AccessStandingNear, Semantics.AccessOpenDoor, Semantics.AccessHand, Semantics.Chair, Semantics.Window, Semantics.Open, Semantics.Entrance, Semantics.Door, Semantics.StaircaseWall, Semantics.RealPlaceholder, Semantics.AssetAsPlaceholder, Semantics.AssetPlaceholderForChildren, Semantics.PlaceholderBBox, Semantics.SingleGenerator, Semantics.NoRotation, Semantics.NoCollision, Semantics.NoChildren]
relation list: ['on_floor', 'flush_wall', 'against_wall', 'spaced_wall', 'hanging', 'side_against_wall', 'ontop', 'on', 'front_against', 'front_to_front', 'leftright_leftright', 'side_by_side', 'back_to_back']

example: 
    rooms = cl.scene()[{Semantics.Room, -Semantics.Object}]
    obj = cl.scene()[{Semantics.Object, -Semantics.Room}]

    cutters = cl.scene()[Semantics.Cutter]
    window = cutters[Semantics.Window]
    doors = cutters[Semantics.Door]

    constraints = OrderedDict()
    score_terms = OrderedDict()

    # region overall fullness

    furniture = obj[Semantics.Furniture].related_to(rooms, cu.on_floor)
    wallfurn = furniture.related_to(rooms, cu.against_wall)
    storage = wallfurn[Semantics.Storage]

    # region CLOSETS
    closets = rooms[Semantics.Closet].excludes(cu.room_types)
    constraints["closets"] = closets.all(
        lambda r: (
            (storage.related_to(r).count() >= 1)
            * ceillights.related_to(r, cu.hanging).count().in_range(0, 1)
            * (
                walldec.related_to(r).count() == 0
            )  # special case exclusion - no paintings etc in closets
        )
    )
    score_terms["closets"] = closets.all(
        lambda r: (
            storage.related_to(r).count().maximize(weight=2)
            * obj.related_to(storage.related_to(r)).count().maximize(weight=2)
        )
    )

    # endregion

    # region LIVINGROOMS

    livingrooms = rooms[Semantics.LivingRoom].excludes(cu.room_types)
    sofas = furniture[seating.SofaFactory]
    tvstands = wallfurn[shelves.TVStandFactory]
    coffeetables = furniture[tables.CoffeeTableFactory]

    sofa_back_near_wall = cl.StableAgainst(
        cu.back, cu.walltags, margin=uniform(0.1, 0.3)
    )
    cl.StableAgainst(cu.side, cu.walltags, margin=uniform(0.1, 0.3))

    def freestanding(o, r):
        return o.related_to(r).related_to(r, -sofa_back_near_wall)

    constraints["sofa"] = livingrooms.all(
        lambda r: (
            # sofas.related_to(r).count().in_range(2, 3)
            sofas.related_to(r, sofa_back_near_wall).count().in_range(2, 4)
            # * sofas.related_to(r, sofa_side_near_wall).count().in_range(0, 1)
            * freestanding(sofas, r).all(
                lambda t: (  # frustrum infront of freestanding sofa must directly contain tvstand
                    cl.accessibility_cost(t, tvstands.related_to(r), dist=3) > 0.7
                )
            )
            * sofas.all(
                lambda t: (
                    cl.accessibility_cost(t, furniture.related_to(r), dist=2).in_range(
                        0, 0.5
                    )
                    * cl.accessibility_cost(t, r, dist=1).in_range(0, 0.5)
                )
            )
            
        )
    )

    constraints["sofa_positioning"] = rooms.all(
        lambda r: (
            sofas.all(
                lambda s: (
                    (cl.accessibility_cost(s, rooms, dist=3) < 0.5)
                    * (
                        cl.focus_score(s, tvstands.related_to(r)) > 0.5
                    )  # must face or perpendicular to TVStand
                )
            )
        )
    )

    score_terms["sofa"] = livingrooms.mean(
        lambda r: (
            sofas.volume().maximize(weight=10)
            + sofas.related_to(r).mean(
                lambda t: (
                    t.distance(sofas.related_to(r)).hinge(0, 1).minimize(weight=1)
                    + t.distance(tvstands.related_to(r)).hinge(2, 3).minimize(weight=5)
                    + cl.focus_score(t, tvstands.related_to(r)).maximize(weight=5)
                    + cl.angle_alignment_cost(
                        t, tvstands.related_to(r), cu.front
                    ).minimize(weight=1)
                    + cl.focus_score(t, coffeetables.related_to(r)).maximize(weight=2)
                    + cl.accessibility_cost(t, r, dist=3).minimize(weight=3)
                )
            )
            + freestanding(sofas, r).mean(
                lambda t: (
                    cl.angle_alignment_cost(t, tvstands.related_to(r)).minimize(
                        weight=5
                    )
                    + cl.angle_alignment_cost(t, r, cu.walltags).minimize(weight=3)
                    + cl.center_stable_surface_dist(t).minimize(weight=0.5)
                )
            )
        )
    )

    tvs = obj[appliances.TVFactory].related_to(tvstands, cu.ontop)

    if params["has_tv"]:
        constraints["tv"] = livingrooms.all(
            lambda r: (
                tvstands.related_to(r).all(
                    lambda t: (
                        (tvs.related_to(t).count() == 1)
                        * tvs.related_to(t).all(
                            lambda tv: cl.accessibility_cost(tv, r, dist=1).in_range(
                                0, 0.1
                            )
                        )
                    )
                )
            )
        )

    score_terms["tvstand"] = rooms.all(
        lambda r: (
            tvstands.mean(
                lambda stand: (
                    tvs.related_to(stand).volume().maximize(weight=1)
                    + stand.distance(window).maximize(
                        weight=1
                    )  # penalize being very close to window. avoids tv blocking window.
                    + cl.accessibility_cost(stand, furniture).minimize(weight=3)
                    + cl.center_stable_surface_dist(stand).minimize(
                        weight=5
                    )  # center tvstand against wall (also tries to do vertical & floor but those are constrained)
                    + cl.center_stable_surface_dist(tvs.related_to(stand)).minimize(
                        weight=1
                    )
                )
            )
        )
    )

    constraints["livingroom"] = livingrooms.all(
        lambda r: (
            storage.related_to(r).count().in_range(1, 5)
            * tvstands.related_to(r).count().equals(1)
            * (  # allow sidetables next to any sofa
                sidetable.related_to(r)
                .related_to(sofas.related_to(r), cu.side_by_side)
                .count()
                .in_range(0, 2)
            )
            * desks.related_to(r).count().in_range(0, 1)
            * coffeetables.related_to(r).count().in_range(0, 1)
            * coffeetables.related_to(r).all(
                lambda t: (
                    obj[Semantics.OfficeShelfItem]
                    .related_to(t, cu.on)
                    .count()
                    .in_range(0, 3)
                )
            )
            * (
                rugs.related_to(r)
                # .related_to(furniture.related_to(r), cu.side_by_side)
                .count()
                .in_range(0, 2)
            )
        )
    )
   
    score_terms["livingroom"] = livingrooms.mean(
        lambda r: (
            coffeetables.related_to(r).mean(
                lambda t: (
                    # ideal coffeetable-to-tv distance according to google
                    t.distance(sofas.related_to(r)).hinge(0.45, 0.6).minimize(weight=5)
                    + cl.angle_alignment_cost(
                        t, sofas.related_to(r), cu.front
                    ).minimize(weight=5)
                    + cl.focus_score(sofas.related_to(r), t).maximize(weight=5)
                )
            )
        )
    )
   
    constraints["livingroom_objects"] = livingrooms.all(
        lambda r: (
            storage.all(
                lambda t: (
                    obj[Semantics.OfficeShelfItem].related_to(t, cu.on).count()
                    >= 0  
                )
            )
            * coffeetables.all(
                lambda t: (
                    obj[Semantics.TableDisplayItem]
                    .related_to(t, cu.ontop)
                    .count()
                    .in_range(0, 1)
                    * (obj[Semantics.OfficeShelfItem].related_to(t, cu.on).count() >= 0)
                )
            )
        )
    )

    # endregion

    Please show me your rules for the given roomtype:
"""


# 2. Try to use specific category names rather than semantic names if the semantic name is confused. For example, use ......
# # shelves = furniture[Semantics.Storage]