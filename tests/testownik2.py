from json_validation.json_schema import schema

# print(schema)

import datetime
import logging
import sys
from copy import deepcopy
import os

from config.config import path_root
from library.tools import *
from library.tools_diagram_coloring import color_gameplay_on_diagram

from library.tools_process import cut_unnecessary_world_elements, save_world, add_node, \
    find_node_from_input, add_attributes_from_input, remove_node, find_layer_from_input
from library.tools_visualisation import draw_graph
from library.tools_validation import name_in_allowed_names, get_jsons_storygraph_validated


logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s', stream=sys.stdout)

dir_name = '' #
json_path = f'{path_root}/world'
script_root_path = os.getcwd().rsplit("/", 1)[0]


# color_gameplay_on_diagram("D:\GitHub\StoryGraphPython\gameplays\gameplay_quest_PolowanieNaBandyte_world_PolowanieNaBandyte_20230303213844_Matthew.json", "D:\GitHub\StoryGraphPython\examples\q2022-01\zespół 13\quest2023-13_diagram_Hunt_for_a_bandit.drawio")
gp_dir = f"..{os.sep}gameplays"
gp_name = "gameplay_quest2023-06_Paddleboat_to_beautiful_voyage_world_PWK2022_06_poprawki_20230326204854_IGG.json"
diag_name = "quest2023-06_diagram_Paddleboat_to_beautiful_voyage.drawio"
color_gameplay_on_diagram(find_file(gp_dir, gp_name), find_file(path_root, diag_name))

# jsons_OK, jsons_schema_OK, errors = import_jsons(dir_name, schema_name, '*.json', only_schema= True)
jsons_OK, jsons_schema_OK, errors, warnings = get_jsons_storygraph_validated(json_path)
import os
import textwrap
from typing import List, Union

import graphviz
from PIL import Image, ImageOps
from graphviz.graphs import BaseGraph

# print("LOKACJE")
# for w in jsons_OK:
#     print(" ----------------------",w["file_path"])
#     jw = w["json"][0]["LSide"]["Locations"]
#     for l in jw:
#         print(l["Name"], l.get("Attributes"), sep="\t")

# print("POSTACI")
# for w in jsons_OK:
#     print(" ----------------------",w["file_path"])
#     jw = w["json"][0]["LSide"]["Locations"]
#
#     for l in jw:
#         if "Characters" in l:
#             for c in l["Characters"]:
#                 print(c["Name"], c.get("Attributes"), sep="\t")


print("PRZEDMIOTY W LOKACJACH")
for w in jsons_OK:
    print(" ----------------------",w["file_path"])
    jw = w["json"][0]["LSide"]["Locations"]

    for l in jw:
        if "Items" in l:
            for i in l["Items"]:
                print(l["Name"], i["Name"], i.get("Attributes"), sep="\t")

print("PRZEDMIOTY U POSTACI")
for w in jsons_OK:
    print(" ----------------------",w["file_path"])
    jw = w["json"][0]["LSide"]["Locations"]

    for l in jw:
        if "Characters" in l:
            for c in l["Characters"]:
                # print(c["Name"], c.get("Attributes"), sep="\t")
                if "Items" in c:
                    for i in c["Items"]:
                        print(c["Name"], i["Name"], i.get("Attributes"), sep="\t")



exit()











world = world_source['json'][0]["LSide"]["Locations"]
if not destinations_change_to_nodes(world, world=True):
    exit(1)


d_title = world_name
d_desc = f'fgdfg'
d_file = f'{world_name}_{decision_nr:03d}_original'
d_dir = f'./'
draw_graph(world, d_title, d_desc, d_file, d_dir)



def draw_graph(graph, t, d, file, dr, r_n=None, r_e=None, c=None, w=True, f='png', clean=True, draw_id=True, map_style=False):
    if type(graph) == list:
        graph = {"Locations": graph}
    gv = GraphVisualizer()
    try:
        gv.visualise(graph, title=t, description=d, world=w, emph_nodes_ids=r_n, emph_edges=r_e, comments=c, draw_id=draw_id, map_style=map_style).render(
            format=f, filename=file, directory=dr, cleanup=clean)
    except Exception:
        pass




class GraphVisualizer:
    def __init__(self):
        self._vertex_counter = 1

    def visualise(self, what: Union[list, dict], title: str = None, description: str = None,
                  world: bool = False, emph_nodes_ids: list = None, emph_edges: list = None, comments: dict = None,
                  draw_id=True, map_style=False) -> BaseGraph:
        """
        Visualize left or right side as graph.
        :param emph_edges:
        :param emph_nodes_ids:
        :param comments:
        :param what: for example production side
        :param title:
        :param description:
        :param world:
        :return:
        """
        if not emph_nodes_ids:
            emph_nodes_ids = []
        if not emph_edges:
            emph_edges = []
        if not comments:
            comments = {}
        world = False
        if world:
            graph = graphviz.Digraph(engine='neato')  # neato
        else:
            graph = graphviz.Digraph(engine='dot')
        graph.attr(overlap='false')
        graph.attr(splines='true')
        graph.attr(dpi='150')
        graph.attr(ratio='fill')
        graph.attr(labelloc='t')
        graph.attr(rankdir='LR')

        full_desc = f'< {title}<BR/><BR/>'
        desc_formatted = ''
        if description:
            desc_formatted = '<BR/>'.join(textwrap.wrap(text=description, width=100))
            desc_formatted = f'<FONT POINT-SIZE="10">{desc_formatted}</FONT>'

        full_desc += desc_formatted
        full_desc += '<BR/> >'

        graph.attr(label=full_desc)

        if not world:
            graph.node('root', '', color='white')

        self._vertex_counter = 1
        node_list = self._visualise_process(what, 'root', '', graph, emph_nodes_ids, comments, world=world, draw_id=draw_id,
                                            map_style=map_style)  # sprawdzić, czy root czy Root

        for node in node_list:
            try:
                for destination in node['node_conn']:
                    conn = None
                    for node2 in node_list:
                        try:
                            if node2['node_dict'] is destination[
                                "Destination"]:  # zm # było: if node2['node_name'] == destination["Destination"]:
                                conn = node2
                                break
                        except:
                            pass

                    if conn:
                        if (id(node['node_dict']), id(conn['node_dict'])) in emph_edges:
                            graph.edge(node['node_nr'], conn['node_nr'], color='red', penwidth="3", constraint='false')
                        else:
                            graph.edge(node['node_nr'], conn['node_nr'], constraint='false')
            except:
                pass

        return graph