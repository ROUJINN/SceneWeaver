from TongGPT import GPT4V, GPT4o, TongGPT


class GPT(GPT4o):
    """
    Simple interface for interacting with GPT-4O model
    """

    VERSIONS = {
        "4v": "gpt-4-vision-preview",
        "4o": "gpt-4o",
        "4o-mini": "gpt-4o-mini",
        "gpt-4-turbo-2024-04-09": "gpt-4-turbo-2024-04-09",
    }

    def __init__(
        self,
        api_key=None,
        version="4o",
    ):
        # def __init__(self, '
        MODEL = "gpt-4-turbo-2024-04-09"
        REGION = "eastus2"
        super().__init__(MODEL, REGION)
        self.version = MODEL

    def __call__(self, payload, verbose=False):
        """
        Queries GPT using the desired @prompt

        Args:
            payload (dict): Prompt payload to pass to GPT. This should be formatted properly, see
                https://platform.openai.com/docs/overview for details
            verbose (bool): Whether to be verbose as GPT is being queried

        Returns:
            None or str: Raw outputted GPT response if valid, else None
        """
        if verbose:
            print(f"Querying GPT-{self.version} API...")
        # import pdb
        # pdb.set_trace()
        response = self.send_request(payload)
        try:
            content = response.choices[0].message.content
        except:
            print(
                f"Got error while querying GPT-{self.version} API! Response:\n\n{response}"
            )
            return None

        if verbose:
            print(f"Finished querying GPT-{self.version}.")

        return content

    def get_payload(self, prompting_text_system, prompting_text_user):
        text_dict_system = {"type": "text", "text": prompting_text_system}
        content_system = [text_dict_system]

        content_user = [{"type": "text", "text": prompting_text_user}]

        object_caption_payload = {
            "model": "gpt-4-turbo-2024-04-09",
            "messages": [
                {"role": "system", "content": content_system},
                {"role": "user", "content": content_user},
            ],
            "temperature": 0,
            "max_tokens": 500,
        }
        return object_caption_payload


# 'on_floor', 'flush_wall', 'against_wall', 'spaced_wall', 'hanging', 'side_against_wall',

# 'ontop', 'on',
# 'front_against', 'front_to_front', 'leftright_leftright', 'side_by_side', 'back_to_back']


### 1. get big object, count, and relation
prompting_text_system = f"""
You are an experienced layout designer to design a 3D scene. 
Your goal is to help me choose objects to put in the scene.

You will receive:
1. The roomtype you need to design.

You need to return:
1. A list of big-furniture categories that stand on the floor, marked with count. Do not return objects like rug.
2. An object list that stand with back against the wall
3. Relation between different categories when they have a subordinate relationship and stay very close(less than 5 cm).
The former object is smaller than the latter object, such as chair and table, nightstand and bed. 

The optional relation is : 
1.front_against: obj1's front faces to obj2, and stand very close.
2.front_to_front: obj1's front faces to obj2's front, and stand very close.
3.leftright_leftright: obj1's left and right faces to obj2's left and right, and stand very close. 
4.side_by_side: obj1's side faces to obj2's side, and stand very close. 
5.back_to_back: obj1's back faces to obj2's back, and stand very close. 

Failure case of relation:
1.[table, table, side_by_side]: The relation between the same category is wrong. You only focus on relation between 2 different categories.
2.[chair, table, side_by_side]: Chair must be in front of the table, using 'front_against' instead of 'side_by_side'.
3.[wardrobe, bed, front_against]: Wardrobe has no subordinate relationship with bed. And they need to keep a long distance to make wardrobe accessable
4.[chair, table, side_by_side],[chair, bed, front_against]: Each category, such as chair can only have one relationship. 2 relations will cause failure.

Here is the example: 
Roomtype: Bedroom
Category list of big object: [1 bed, 1 wardrobe, 2 nightstand, 1 bench]
Object against the wall: [bed, wardrobe, nightstand]
Relation between big objects: [nightstand, bed, side_by_side], [bench, bed, front_to_front]

"""
prompting_text_user = f"""
Here is the roomtype you need to design:
Roomtype: Bookstore

Here is your response:
"""

# gpt = GPT()
# prompt_payload = gpt.get_payload(prompting_text_system,prompting_text_user)
# gpt_text_response = gpt(payload=prompt_payload, verbose=True)
# print(gpt_text_response)
# # Category list of big objects: [1 checkout counter, 5 bookshelves, 2 reading tables, 8 chairs]
# # Object against the wall: [bookshelves]
# # Relation between big objects: [chair, reading table, front_against]


#### 2. get small object and relation

prompting_text_system = f"""
You are an experienced layout designer to design a 3D scene. 
Your goal is to help me choose small objects to put in the scene.

You will receive:
1. The roomtype you need to design.
2. The big furniture that exist in this room.

You need to return:
1. A list of small-furniture categories that belongs to the big furniture. 
2. Relation between small furniture and big furniture, with count for each big furniture.
The former object is smaller than the latter object, such as laptop and desk. 

The optional relation is : 
1.ontop: obj1 is placed on the top of obj2.
2.on: obj1 is placed on the top of or inside obj2.

Here is the example: 
Roomtype: Bedroom
List of big furniture: [bed, wardrobe, nightstand, bench]
List of small furniture: [book, plant, lamp, clothes]
Relation: [book, nightstand, on, 2], [plant, nightstand, ontop, 1], [lamp, nightstand, ontop, 1], [clothes, bench, ontop, 2], [clothes, wardrobe, on, 4]

"""
prompting_text_user = f"""
Here is the roomtype you need to design:
Roomtype: Bookstore
List of big furniture: [checkout counter, bookshelves, reading tables, chairs]

Here is your response:
"""

# gpt = GPT()
# prompt_payload = gpt.get_payload(prompting_text_system,prompting_text_user)
# gpt_text_response = gpt(payload=prompt_payload, verbose=True)
# print(gpt_text_response)
# # List of small furniture: [books, bookmarks, lamps, reading glasses, cash register, decorative items]
# # Relation:
# # - [books, bookshelves, on, 50]
# # - [books, reading tables, on, 5]
# # - [bookmarks, bookshelves, on, 10]
# # - [lamps, reading tables, ontop, 4]
# # - [reading glasses, reading tables, ontop, 3]
# # - [cash register, checkout counter, ontop, 1]
# # - [decorative items, checkout counter, ontop, 2]
# # - [decorative items, bookshelves, ontop, 5]


#### 3. get object class name in infinigen


prompting_text_system = """
You are an experienced layout designer to design a 3D scene. 
Your goal is to match the given open-vocabulary category name with the standard category name.

The standard category list: ['appliances.BeverageFridgeFactory', 'appliances.DishwasherFactory', 'appliances.MicrowaveFactory', 'appliances.OvenFactory', 'appliances.MonitorFactory', 'appliances.TVFactory', 'bathroom.BathroomSinkFactory', 'bathroom.StandingSinkFactory', 'bathroom.BathtubFactory', 'bathroom.HardwareFactory', 'bathroom.ToiletFactory', 'decor.AquariumTankFactory', 'elements.DoorCasingFactory', 'elements.GlassPanelDoorFactory', 'elements.LiteDoorFactory', 'elements.LouverDoorFactory', 'elements.PanelDoorFactory', 'elements.NatureShelfTrinketsFactory', 'elements.PillarFactory', 'elements.RugFactory', 'elements.CantileverStaircaseFactory', 'elements.CurvedStaircaseFactory', 'elements.LShapedStaircaseFactory', 'elements.SpiralStaircaseFactory', 'elements.StraightStaircaseFactory', 'elements.UShapedStaircaseFactory', 'elements.PalletFactory', 'elements.RackFactory', 'lamp.CeilingClassicLampFactory', 'lamp.CeilingLightFactory', 'lamp.DeskLampFactory', 'lamp.FloorLampFactory', 'lamp.LampFactory', 'seating.BedFactory', 'seating.BedFrameFactory', 'seating.BarChairFactory', 'seating.ChairFactory', 'seating.OfficeChairFactory', 'seating.MattressFactory', 'seating.PillowFactory', 'seating.ArmChairFactory', 'seating.SofaFactory', 'shelves.CellShelfFactory', 'shelves.TVStandFactory', 'shelves.CountertopFactory', 'shelves.CabinetDoorBaseFactory', 'shelves.KitchenCabinetFactory', 'shelves.KitchenIslandFactory', 'shelves.KitchenSpaceFactory', 'shelves.LargeShelfFactory', 'shelves.SimpleBookcaseFactory', 'shelves.SidetableDeskFactory', 'shelves.SimpleDeskFactory', 'shelves.SingleCabinetFactory', 'shelves.TriangleShelfFactory', 'table_decorations.BookColumnFactory', 'table_decorations.BookFactory', 'table_decorations.BookStackFactory', 'table_decorations.SinkFactory', 'table_decorations.TapFactory', 'table_decorations.VaseFactory', 'tables.TableCocktailFactory', 'tables.CoffeeTableFactory', 'tables.SideTableFactory', 'tables.TableDiningFactory', 'tables.TableTopFactory', 'tableware.BottleFactory', 'tableware.BowlFactory', 'tableware.CanFactory', 'tableware.ChopsticksFactory', 'tableware.CupFactory', 'tableware.FoodBagFactory', 'tableware.FoodBoxFactory', 'tableware.ForkFactory', 'tableware.SpatulaFactory', 'tableware.FruitContainerFactory', 'tableware.JarFactory', 'tableware.KnifeFactory', 'tableware.LidFactory', 'tableware.PanFactory', 'tableware.LargePlantContainerFactory', 'tableware.PlantContainerFactory', 'tableware.PlateFactory', 'tableware.PotFactory', 'tableware.SpoonFactory', 'tableware.WineglassFactory', 'wall_decorations.BalloonFactory', 'wall_decorations.RangeHoodFactory', 'wall_decorations.MirrorFactory', 'wall_decorations.WallArtFactory', 'wall_decorations.WallShelfFactory']

You will receive:
1. The roomtype you need to design.
2. A list of given open-vocabulary category names.

You need to return:
1. The mapping of given category name with the most similar standard category name. 
If no standard category is matched, return None.

Here is the example: 
Roomtype: Bedroom
list of given category names: [bed, nightstand, lamp, wardrobe]
Mapping results: {"bed": 'seating.BedFactory',"nightstand": 'shelves.SingleCabinetFactory',"lamp": 'lamp.DeskLampFactory','wardrobe': None}
"""
prompting_text_user = f"""
Here is the roomtype you need to design:
Roomtype: Bookstore
List of given category names:  [checkout counter, bookshelves, reading tables, chairs]

Here is your response:
"""

# gpt = GPT()
# prompt_payload = gpt.get_payload(prompting_text_system,prompting_text_user)
# gpt_text_response = gpt(payload=prompt_payload, verbose=True)
# print(gpt_text_response)
# list of given category names: [checkout counter, bookshelves, reading tables, chairs]
# 1-to-many:
# Mapping results: {
#   "checkout counter": ['shelves.CountertopFactory'],
#   "bookshelves": ['shelves.SimpleBookcaseFactory', 'shelves.LargeShelfFactory'],
#   "reading tables": ['tables.TableDiningFactory', 'tables.CoffeeTableFactory'],
#   "chairs": ['seating.ChairFactory', 'seating.OfficeChairFactory']
# }
# 1-to-1:
# Mapping results: {
#     "checkout counter": 'shelves.SidetableDeskFactory',
#     "bookshelves": 'shelves.SimpleBookcaseFactory',
#     "reading tables": 'tables.TableDiningFactory',
#     "chairs": 'seating.ChairFactory'
# }


# list of given category names: [books, bookmarks, lamps, reading glasses, cash register, decorative items]
# 1-to-many:
# Mapping results: {
#     "books": ['table_decorations.BookFactory', 'table_decorations.BookStackFactory'],
#     "bookmarks": [],
#     "lamps": ['lamp.CeilingClassicLampFactory', 'lamp.CeilingLightFactory', 'lamp.DeskLampFactory', 'lamp.FloorLampFactory', 'lamp.LampFactory'],
#     "reading glasses": [],
#     "cash register": [],
#     "decorative items": ['decor.AquariumTankFactory', 'elements.NatureShelfTrinketsFactory', 'table_decorations.VaseFactory', 'wall_decorations.MirrorFactory', 'wall_decorations.WallArtFactory']
# }
# 1-to-1:
# Mapping results: {
#     "books": 'table_decorations.BookFactory',
#     "bookmarks": None,
#     "lamps": 'lamp.DeskLampFactory',
#     "reading glasses": None,
#     "cash register": None,
#     "decorative items": None
# }


#### 4. generate rule code


prompting_text_system = """
You are an experienced layout designer to design a 3D scene. 
Your goal is to write a python code to present the given designing rule.

You will receive:
1. The roomtype you need to design.
2. Rules to place the objects, including the relation between objets.
3. A partialy writen code with objects defined in the scene.

You need to return:
1. The completed python code to present the given designing rules and relations.
The relation should be writen as [cu.front_against, cu.front_to_front, cu.leftright_leftright, cu.side_by_side, cu.back_to_back] in python code.
Note the secondary rules need to 

* Here is the example: *

Roomtype: Bedroom
Big-object count: [1 beds, 1 desks, 2 sidetable, 2 nightstand]

Relation between big object:
[nightstand, beds, leftright_leftright]

Small object count and relation with big object:
[books, nightstand, on, 3]

* Completed code: *
rooms = cl.scene()[{Semantics.Room, -Semantics.Object}]
obj = cl.scene()[{Semantics.Object, -Semantics.Room}]
bedrooms = rooms[Semantics.Bedroom].excludes(cu.room_types)

constraints = OrderedDict()
score_terms = OrderedDict()

furniture = obj[Semantics.Furniture].related_to(rooms, cu.on_floor)
wallfurn = furniture.related_to(rooms, cu.against_wall)

beds_obj = wallfurn[seating.BedFactory]
desks_obj = wallfurn[shelves.SimpleDeskFactory]
nightstand_obj = wallfurn[shelves.SingleCabinetFactory]

floor_lamps_obj = obj[lamp.FloorLampFactory].related_to(rooms, cu.on_floor).related_to(rooms, cu.against_wall)
books_obj = obj[table_decorations.BookStackFactory]

constraints["bedroom"] = bedrooms.all(
    lambda r: (
        beds_obj.related_to(r).count().in_range(1, 1)
        * (
            nightstand_obj.related_to(r)
            .related_to(beds_obj.related_to(r), cu.leftright_leftright)
            .count()
            .in_range(2, 2)
        )
        * desks_obj.related_to(r).count().in_range(1, 1)
        * floor_lamps_obj.related_to(r).count().in_range(1, 1)
        * nightstand_obj.related_to(r).all(
            lambda s: (
                books_obj.related_to(s, cu.on).count().in_range(3,3)
                * (books_obj.related_to(s, cu.on).count() >= 0)
            )
        )
    )
)


"""
prompting_text_user = """
*Here is the roomtype and object info:*

Roomtype: Bookstore
Big-object count: [1 checkout counter, 5 bookshelves, 2 reading tables, 8 chairs]

Relation between big object:
[chair, reading tables, front_against]

Small object count and relation with big object:
[books, bookshelves, on, 50]
[books, reading tables, on, 5]
[lamps, reading tables, ontop, 4]

* Here is the code you need to write constraints: *

rooms = cl.scene()[{Semantics.Room, -Semantics.Object}]
obj = cl.scene()[{Semantics.Object, -Semantics.Room}]
bookstore = rooms[Semantics.Bookstore].excludes(cu.room_types)

constraints = OrderedDict()
score_terms = OrderedDict()

furniture = obj[Semantics.Furniture].related_to(rooms, cu.on_floor)
wallfurn = furniture.related_to(rooms, cu.against_wall)

bookshelves_obj = wallfurn[shelves.SimpleBookcaseFactory]
checkout_counter_obj = furniture[shelves.SidetableDeskFactory]
reading_tables_obj = furniture[tables.TableDiningFactory]
chairs_obj = furniture[seating.ChairFactory].related_to(reading_tables_obj, cu.front_against)

books_obj = furniture[table_decorations.BookFactory]
lamps_obj = furniture[lamp.DeskLampFactory]


* Here is your response: *
"""

gpt = GPT()
prompt_payload = gpt.get_payload(prompting_text_system, prompting_text_user)
gpt_text_response = gpt(payload=prompt_payload, verbose=True)
print(gpt_text_response)


import json
import re


def extract_json(input_string):
    # Using regex to identify the JSON structure in the string
    json_match = re.search(r"{.*}", input_string, re.DOTALL)
    if json_match:
        extracted_json = json_match.group(0)
        try:
            # Convert the extracted JSON string into a Python dictionary
            json_dict = json.loads(extracted_json)
            # json_dict = check_dict(json_dict)
            return json_dict
        except json.JSONDecodeError:
            print(input_string)
            print("Error while decoding the JSON.")
            return None
    else:
        print("No valid JSON found.")
        return None


# print(prompt)


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
