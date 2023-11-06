
import datetime
import logging
import sys
from copy import deepcopy
import os

from config.config import path_root
from library.tools import *

from library.tools_process import cut_unnecessary_world_elements, save_world, add_node, \
    find_node_from_input, add_attributes_from_input, remove_node, find_layer_from_input
from library.tools_visualisation import draw_graph
from library.tools_validation import name_in_allowed_names, get_jsons_storygraph_validated


logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s', stream=sys.stdout)

dir_name = 'world' #
json_path = f'{path_root}/{dir_name}'
script_root_path = os.getcwd().rsplit("/", 1)[0]


# jsons_OK, jsons_schema_OK, errors = import_jsons(dir_name, schema_name, '*.json', only_schema= True)
jsons_OK, jsons_schema_OK, errors, warnings = get_jsons_storygraph_validated(json_path)

######################################
# Tutaj ustalamy parametry wejściowe #
######################################

for world_source in jsons_schema_OK:

    # Definiowanie świata

    # world_source = jsons_schema_OK[get_quest_nr(world_name, jsons_schema_OK)]
    world = world_source['json'][0]["LSide"]["Locations"]
    world_name = world_source['json'][0]["Title"]

    if not destinations_change_to_nodes(world, world=True):
        exit(1)

    modification_date = datetime.now()
    date_folder = str(modification_date.strftime("%Y%m%d%H%M%S"))

    mandatory_attr = {'Characters': {"HP": 100, "Money": 10}, 'Items': {"Value": 5}}

    # gv = GraphVisualizer()
    comments = None
    decision_nr = 0
    decision_list = []
    layers_to_draw = ["Pusta"]  # ["Characters", "Narration"]


    # print(f"Wizualizacje zmian znajdują się w katalogu: ../{json_path}/{world_name}_{date_folder}. Widok końcowy będzie "
    #       f"w katalogu ../{json_path}.")

    d_title = world_name
    d_desc = f'Stan świata w dniu {modification_date.strftime("%d.%m.%Y godz. %H:%M:%S")}'
    d_file = f'{world_name}_{decision_nr:03d}_original'
    d_dir = f'{json_path}/{world_name}_{date_folder}'
    draw_graph(world, d_title, d_desc, d_file, d_dir, allowed_layers=layers_to_draw)
