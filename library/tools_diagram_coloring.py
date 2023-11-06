import base64
import json
import os
import re
import sys
import uuid
import xml.etree.ElementTree as ET
import zlib

from pathlib import Path
from typing import Tuple
from urllib.parse import unquote

from library.tools import get_project_root


# light_pink = "#f8cecc;"
# dark_pink = "#b85450;"
light_green = "#d5e8d4;"
dark_green = "#82b366;"

light_blue = "#dae8fc;"
dark_blue = "#006EAF;"
stroke_width = "3;"

nodes_ids = []
arrows_ids = []
added_nodes = []
added_arrows = []
nodes_in_the_path = []
arrows_in_the_path = []


def color_gameplay_on_diagram(gameplay_file_path: str, diagram_file_path: str) -> str:
    """
    Colors the given gameplay in the corresponding diagram; new productions are drawn in the diagram if there are no
    matching ones.
    :param gameplay_file_path: path to json file with gameplay
    :param diagram_file_path: path to xml/drawio file with diagram
    :return: name of the created xml file with the colored diagram
    """
    diagram_extension = diagram_file_path.rpartition('.')[2]

    # diagram_err, diagram_warn = yulia_diagram_validator(diagram_file_path, production_list)



    diagram_file = open(diagram_file_path, encoding="utf-8").read()
    if "root" not in diagram_file:
        diagram_file = decompress_diagram(diagram_file)

    diagram_file = diagram_file.replace("&amp;nbsp;", " ")
    diagram_file = diagram_file.replace("&nbsp;", " ")

    file_content = ET.fromstring(diagram_file)
    root = file_content.find('.//root')

    possible_locations = get_possible_locations_in_diagram(root)
    possible_productions = get_all_productions_in_diagram(root)
    automatic_productions = get_automatic_productions(possible_productions)
    array_of_moves, array_of_characters, game_end_reason = get_gameplay_from_json_file(gameplay_file_path, automatic_productions, possible_locations)
    get_all_arrows_and_nodes_ids(root)
    minimum_x_coordinate = get_minimum_x_coordinate(root)

    previous_node_id, minimum_x_coordinate = get_next_node(root, "", [], array_of_moves[0], array_of_characters[0], minimum_x_coordinate)

    for i in range(1, len(array_of_moves)):
        next_move = array_of_moves[i]
        next_characters = array_of_characters[i]
        connected_nodes = get_connected_nodes(root, previous_node_id)
        next_node_id, minimum_x_coordinate = get_next_node(root, previous_node_id, connected_nodes, next_move, next_characters, minimum_x_coordinate)
        previous_node_id = next_node_id

    set_ending_circle(root, previous_node_id, game_end_reason)
    set_nodes_and_arrows_styles(root)

    gameplay_file_name = os.path.split(gameplay_file_path)[1].split('.')[0]
    output_location = os.path.split(gameplay_file_path)[0]
    diagram_file_name = os.path.split(diagram_file_path)[1].split('.')[0]
    output_file_name = diagram_file_name + "_" + gameplay_file_name + "." + diagram_extension

    tree = ET.ElementTree(file_content)
    tree.write(output_location + os.sep + output_file_name, encoding="utf-8")

    return output_file_name


def decompress_diagram(diagram_file: str) -> str:
    """
    Decompresses given xml/drawio file.
    https://crashlaker.github.io/programming/2020/05/17/draw.io_decompress_xml_python.html
    :param diagram_file: file opened as a string
    :return: string with decompressed file
    """
    diagram_part = re.search("<diagram.*>[\s\S]*?</diagram>", diagram_file)
    part_to_decode = re.sub("</diagram>", "", diagram_part[0])
    part_to_decode = re.sub("<diagram.*>", "", part_to_decode)
    decompress = zlib.decompressobj(-15)
    decompressed_data = decompress.decompress(base64.b64decode(part_to_decode))
    decompressed_data += decompress.flush()
    decoded_diagram = unquote(decompressed_data.decode())
    return decoded_diagram


def get_possible_locations_in_diagram(diagram_root: ET.Element) -> list:
    """
    Reads names of the characters and locations in every "Location change" production in the diagram.
    :param diagram_root: root of the xml file
    :return: list of lists containing names from every "Location change" production
    """
    possible_locations = []
    loc_change = "Location change / Zmiana lokacji"
    for node in diagram_root:
        node_value = node.get('value')
        if type(node_value) == str and loc_change in re.sub("<[\s\S]*?>", "", node_value):
            locations_in_node = re.sub("<[\s\S]*?>", "", node_value).split("(", 1)[1].split(")", 1)[0].split(", ")
            possible_locations.append(locations_in_node)
    return possible_locations


def get_all_productions_in_diagram(diagram_root: ET.Element) -> list:
    """
    Reads all the names of the productions appearing in the diagram with the corresponding names of locations and characters.
    :param diagram_root: root of the xml file
    :return: list of all productions from the diagram
    """
    possible_productions = []
    for node in diagram_root:
        node_value = node.get('value')
        if type(node_value) == str:
            possible_productions.append(re.sub("<[\s\S]*?>", "", node_value))
    return possible_productions


def get_automatic_productions(possible_productions_on_diagram: list) -> list:
    """
    Gives all of the defined automatic productions names unless they appear in the diagram.
    :param possible_productions_on_diagram: list of productions in the diagram
    :return: list of automatic productions that do not appear in the diagram
    """
    automatic_productions = []
    path_root = get_project_root() / Path('examples')
    json_file_name = 'produkcje_automatyczne.json'
    json_file_path = str(path_root) + os.sep + json_file_name
    with open(json_file_path, "r", encoding="utf-8") as data_file:
        data = json.load(data_file)
        for production in data:
            title = f"{production['Title']}"
            production_is_on_diagram = False
            for possible_production in possible_productions_on_diagram:
                if title in possible_production:
                    production_is_on_diagram = True
            if not production_is_on_diagram:
                automatic_productions.append(title)
    return automatic_productions


def get_gameplay_from_json_file(json_file_path: str, automatic_productions: list, possible_locations: list) -> Tuple[list, list, str]:
    """
    Reads the whole gameplay from the given json file and creates a list of consecutive moves excluding automatic
    productions that do not appear in the diagram and multiple location changes directly following each other (only
    the last location change is saved to the list of moves); teleportations to locations that are present in the diagram
    are converted to location changes.
    :param json_file_path: path to json file with gameplay
    :param automatic_productions: list of automatic productions
    :param possible_locations: list of lists containing names from every "Location change" production
    :return: list of moves, list of corresponding characters and locations, reason for ending the game
    """
    array_of_moves = []
    array_of_characters = []
    loc_change = "Location change / Zmiana lokacji"
    teleportation = "Teleportation / Teleportacja"
    with open(json_file_path, "r", encoding="utf-8") as data_file:
        data = json.load(data_file)
        moves = data["Moves"]
        previous_move = ""
        for nr, move in enumerate(moves):
            production_name = f"{move['ProductionTitle']}"
            production_match = []
            for m in move['LSMatching']:
                if production_name == loc_change or production_name == teleportation:
                    if m["LSNodeRef"] == "Bohater" or m["LSNodeRef"] == "Lokacja_B":
                        character = f"{m['WorldNodeName']}"
                        production_match.append(character)
                else:
                    character = f"{m['WorldNodeName']}"
                    production_match.append(character)
            if production_name == teleportation:
                for locations in possible_locations:
                    if set(locations).issubset(set(production_match)):
                        production_name = loc_change
                        break
            if production_name not in automatic_productions:
                if production_name == loc_change and previous_move == loc_change:
                    array_of_moves.pop()
                    array_of_characters.pop()
                array_of_moves.append(production_name)
                array_of_characters.append(production_match)
                previous_move = production_name

        if "EndDecisionExplanation" in data:
            game_end_reason = "Player's decision"
        else:
            game_end_reason = "Death"

    return array_of_moves, array_of_characters, game_end_reason


def get_all_arrows_and_nodes_ids(diagram_root: ET.Element) -> None:
    """
    Saves all of the nodes (productions) and arrows from the diagram in the global arrays.
    :param diagram_root: root of the xml file
    :return:
    """
    for arrow in diagram_root.findall("./mxCell[@edge='1']"):
        arrows_ids.append(arrow.attrib["id"])
    for node in diagram_root.findall("./mxCell[@vertex='1']"):
        if node.attrib["value"] != "" and "fillColor=#fff2cc;" not in node.attrib["style"]:
            nodes_ids.append(node.attrib["id"])


def get_minimum_x_coordinate(diagram_root: ET.Element) -> int:
    """
    Checks what is the minimum x coordinate of the nodes in the diagram.
    :param diagram_root: root of the xml file
    :return: value of the minimum x coordinate
    """
    minimum_x_coordinate = sys.maxsize
    for node_id in nodes_ids + added_nodes:
        node_path = './mxCell[@id="' + node_id + '"]'
        node = diagram_root.find(node_path)
        node_x = int(float(node.find("./mxGeometry").get('x')))
        if minimum_x_coordinate > node_x:
            minimum_x_coordinate = node_x
    return minimum_x_coordinate


def get_first_node(diagram_root: ET.Element) -> str:
    """
    Checks which node in the diagram is the first one (there are no other nodes that lead to it or it is the highest one).
    :param diagram_root: root of the xml file
    :return: id of the first node in the diagram
    """
    nodes_y_coordinate = {}
    nodes_entering_arrows = {}
    nodes_exiting_arrows = {}

    for node_id in nodes_ids:
        node_path = './mxCell[@id="' + node_id + '"]'
        node = diagram_root.find(node_path)
        nodes_y_coordinate[node_id] = int(float(node.find("./mxGeometry").get('y')))
        nodes_entering_arrows[node_id] = 0
        nodes_exiting_arrows[node_id] = 0

    for arrow_id in arrows_ids:
        arrow_path = './mxCell[@id="' + arrow_id + '"]'
        arrow = diagram_root.find(arrow_path)
        source_node_id = arrow.get("source")
        target_node_id = arrow.get("target")
        if target_node_id in nodes_entering_arrows.keys():
            nodes_entering_arrows[target_node_id] += 1
        if source_node_id in nodes_exiting_arrows.keys():
            nodes_exiting_arrows[source_node_id] += 1

    if 0 in list(nodes_entering_arrows.values()):
        first_node_id = list(nodes_entering_arrows.keys())[list(nodes_entering_arrows.values()).index(0)]
    else:
        first_node_id = min(nodes_y_coordinate, key=nodes_y_coordinate.get)
        while nodes_exiting_arrows[first_node_id] == 0:
            nodes_y_coordinate.pop(first_node_id)
            first_node_id = min(nodes_y_coordinate, key=nodes_y_coordinate.get)

    return first_node_id


def add_first_node(diagram_root: ET.Element, move: str, characters: list, minimum_x: int, highest_node_y: int) -> Tuple[str, int]:
    """
    Adds first node to the diagram and sets its value (move and corresponding names of the characters and locations) and style
    :param diagram_root: root of the xml file
    :param move: first move from the gameplay
    :param characters: names of the characters and locations corresponding to the first move
    :param minimum_x: minimum of x coordinates
    :param highest_node_y: y coordinate of the highest node in a diagram
    :return: id of the next node in the diagram, updated minimum of x coordinates
    """

    new_node_x = minimum_x - 300
    new_node_y = highest_node_y - 300

    new_node_id = str(uuid.uuid4())
    new_node_characters = "("
    for character in characters:
        new_node_characters = new_node_characters + character + ", "
    new_node_value = str(move) + "; " + new_node_characters[:len(new_node_characters) - 2] + ")"
    new_node_style = "rounded=0;whiteSpace=wrap;html=1;strokeColor=#6c8ebf;align=center;fontSize=14;fontFamily=Helvetica;fillColor=" + light_blue + "strokeColor=" + dark_blue
    attrib_node = {"id": new_node_id, "value": new_node_value, "style": new_node_style, "parent": "1", "vertex": "1"}
    attrib_node_geo = {"x": str(new_node_x), "y": str(new_node_y), "width": "260", "height": "60", "as": "geometry"}
    my_node = ET.SubElement(diagram_root, "mxCell", attrib_node)
    ET.SubElement(my_node, "mxGeometry", attrib_node_geo)
    added_nodes.append(new_node_id)
    minimum_x = new_node_x

    return new_node_id, minimum_x


def get_connected_nodes(diagram_root: ET.Element, node_id: str) -> list:
    """
    Checks which nodes in the diagram are the targets of the arrows coming out of a given node.
    :param diagram_root: root of the xml file
    :param node_id: id of the given node
    :return: list of the ids of the connected nodes
    """
    connected_nodes = []
    for arrow_id in arrows_ids:
        arrow_path = './mxCell[@id="' + arrow_id + '"]'
        arrow = diagram_root.find(arrow_path)
        if arrow.get("source") == node_id:
            connected_nodes.append(arrow.get("target"))
    return connected_nodes


def get_next_node(diagram_root: ET.Element, previous_node_id: str, connected_nodes: list, move: str, characters: list, minimum_x: int) -> Tuple[str, int]:
    """
    Searches for the next node from the diagram that corresponds to the given move from the gameplay; if there is no
    connection between the previous node and the next one, the arrow is created; if there is no node in the diagram
    with the value containing move from the gameplay, the new node is created with the adequate new arrow.
    :param diagram_root: root of the xml file
    :param previous_node_id: id of the node corresponding to the previous move
    :param connected_nodes: list of nodes connected to the previous node
    :param move: current move from the gameplay
    :param characters: names of the characters and locations corresponding to the move
    :param minimum_x: current minimum of x coordinates of the nodes in the diagram
    :return: id of the next node in the diagram, updated minimum of x coordinates
    """
    for node_id in connected_nodes:
        node_path = './mxCell[@id="' + node_id + '"]'
        node = diagram_root.find(node_path)
        node_value = node.get('value')
        if type(node_value) == str and move in re.sub("<[\s\S]*?>", "", node_value) and node_id in nodes_ids:
            node_value = re.sub("<[\s\S]*?>", "", node_value)
            if ("(" in node_value and check_number_of_compatible_characters(node_value, characters)) or "(" not in node_value:
                next_node_id = node_id
                for arrow_id in arrows_ids:
                    arrow_path = './mxCell[@id="' + arrow_id + '"]'
                    arrow = diagram_root.find(arrow_path)
                    if arrow.get("source") == previous_node_id and arrow.get("target") == node_id:
                        nodes_ids.remove(next_node_id)
                        nodes_in_the_path.append(next_node_id)
                        if previous_node_id in (nodes_in_the_path + added_nodes):
                            arrows_ids.remove(arrow_id)
                            arrows_in_the_path.append(arrow_id)
                        return next_node_id, minimum_x

    for node_id in nodes_ids:
        node_path = './mxCell[@id="' + node_id + '"]'
        node = diagram_root.find(node_path)
        node_value = node.get('value')
        if type(node_value) == str and move in re.sub("<[\s\S]*?>", "", node_value):
            node_value = re.sub("<[\s\S]*?>", "", node_value)
            if ("(" in node_value and check_number_of_compatible_characters(node_value, characters)) or "(" not in node_value:
                next_node_id = node_id
                nodes_in_the_path.append(next_node_id)
                nodes_ids.remove(next_node_id)
                if previous_node_id != "":
                    add_new_arrow(diagram_root, previous_node_id, next_node_id)
                return next_node_id, minimum_x

    if previous_node_id != "":
        new_node_id, new_arrow_style, minimum_x = add_new_node(diagram_root, previous_node_id, move, characters, minimum_x)
        add_new_arrow(diagram_root, previous_node_id, new_node_id, new_arrow_style)
    else:
        first_node_id = get_first_node(diagram_root)
        first_node = diagram_root.find('./mxCell[@id="' + first_node_id + '"]')
        first_node_y = int(float(first_node.find("./mxGeometry").get('y')))
        new_node_id, minimum_x = add_first_node(diagram_root, move, characters, minimum_x, first_node_y)

    return new_node_id, minimum_x


def check_number_of_compatible_characters(node_value: str, characters_in_move: list) -> bool:
    """
    Checks if the names of the characters and locations in a given production in the diagram appear in the list of names
    of the characters and locations from the current move from the gameplay.
    :param node_value: node value containing production name and its characters and locations
    :param characters_in_move: list of names of the characters and locations from the current move from the gameplay
    :return: True when all of the names in a given production appear in the names from the gameplay; otherwise False
    """
    number_of_compatible_characters = 0
    response = False
    characters_in_node = node_value.split("(", 1)[1].split(")", 1)[0]
    characters_in_node = re.sub("<[\s\S]*?>", "", characters_in_node)
    array_of_characters_in_node = characters_in_node.split(",")
    for character in array_of_characters_in_node:
        character = character.strip()
        if "/" not in character and character in characters_in_move:
            number_of_compatible_characters += 1
        elif "/" in character:
            alternative_characters = character.split("/")
            for alternative in alternative_characters:
                if alternative in characters_in_move:
                    number_of_compatible_characters += 1
    if number_of_compatible_characters == len(array_of_characters_in_node):
        response = True
    return response


def add_new_arrow(diagram_root: ET.Element, from_node: str, to_node: str, new_arrow_style: str = None) -> None:
    """
    Adds new arrow to the diagram connecting two given nodes and sets its style if it was not passed.
    :param diagram_root: root of the xml file
    :param from_node: id of the source node
    :param to_node: id of the target node
    :param new_arrow_style: optional custom arrow style
    :return:
    """
    if (from_node not in nodes_in_the_path) and (from_node not in added_nodes):
        return

    added_arrow_colors = "fillColor=" + light_blue + "strokeColor=" + dark_blue + "strokeWidth=" + stroke_width
    if new_arrow_style is None:
        if from_node in added_nodes:
            new_arrow_style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.2;entryDx=0;entryDy=0;" + added_arrow_colors
        else:
            new_arrow_style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=0;exitY=0.8;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" + added_arrow_colors

    new_arrow_id = str(uuid.uuid4())
    attrib_arrow = {"id": new_arrow_id, "style": new_arrow_style, "source": from_node, "target": to_node, "parent": "1",
                    "edge": "1"}
    attrib_arrow_geo = {"relative": "1", "as": "geometry"}
    my_arrow = ET.SubElement(diagram_root, "mxCell", attrib_arrow)
    ET.SubElement(my_arrow, "mxGeometry", attrib_arrow_geo)
    added_arrows.append(new_arrow_id)


def add_new_node(diagram_root: ET.Element, previous_node_id: str, move: str, characters: list, minimum_x: int) -> Tuple[str, str, int]:
    """
    Adds new node to the diagram and sets its value (move and corresponding names of the characters and locations) and style
    :param diagram_root: root of the xml file
    :param previous_node_id: id of the node corresponding to the previous move
    :param move: current move from the gameplay
    :param characters: names of the characters and locations corresponding to the move
    :param minimum_x: current minimum of x coordinates
    :return: id of the next node in the diagram, style of the new arrow that needs to be added, updated minimum of x coordinates
    """
    previous_node_path = './mxCell[@id="' + previous_node_id + '"]'
    previous_node = diagram_root.find(previous_node_path)

    if previous_node_id in added_nodes:
        new_node_x = int(float(previous_node.find("./mxGeometry").get('x')))
        new_node_y = int(float(previous_node.find("./mxGeometry").get('y'))) + 120
        new_arrow_style = "rounded=0;orthogonalLoop=1;jettySize=auto;html=1;entryX=0.5;entryY=0;entryDx=0;entryDy=0;fontSize=14;fillColor=" + light_blue + "strokeColor=" + dark_blue + "strokeWidth=" + stroke_width
    else:
        new_node_x = minimum_x - 300
        new_node_y = int(float(previous_node.find("./mxGeometry").get('y'))) + 80
        new_arrow_style = None

    new_node_id = str(uuid.uuid4())
    new_node_characters = "("
    for character in characters:
        new_node_characters = new_node_characters + character + ", "
    new_node_value = str(move) + "; " + new_node_characters[:len(new_node_characters) - 2] + ")"
    new_node_style = "rounded=0;whiteSpace=wrap;html=1;strokeColor=#6c8ebf;align=center;fontSize=14;fontFamily=Helvetica;fillColor=" + light_blue + "strokeColor=" + dark_blue
    new_node_height = 60 if len(new_node_value) < 120 else 80
    attrib_node = {"id": new_node_id, "value": new_node_value, "style": new_node_style, "parent": "1", "vertex": "1"}
    attrib_node_geo = {"x": str(new_node_x), "y": str(new_node_y), "width": "260", "height": str(new_node_height), "as": "geometry"}
    my_node = ET.SubElement(diagram_root, "mxCell", attrib_node)
    ET.SubElement(my_node, "mxGeometry", attrib_node_geo)
    added_nodes.append(new_node_id)

    if minimum_x > new_node_x:
        minimum_x = new_node_x

    return new_node_id, new_arrow_style, minimum_x


def set_ending_circle(diagram_root: ET.Element, previous_node_id: str, game_end_reason: str) -> None:
    connected_nodes_ids = get_connected_nodes(diagram_root, previous_node_id)
    black_circle_style = "ellipse;whiteSpace=wrap;html=1;aspect=fixed;fontSize=14;align=center;fillColor=#000000;fontColor=#ffffff;"
    pink_circle_style = "ellipse;whiteSpace=wrap;html=1;aspect=fixed;fontSize=12;align=center;fillColor=" + light_green + "fontColor=#000000;"
    blue_circle_style = "ellipse;whiteSpace=wrap;html=1;aspect=fixed;fontSize=12;align=center;fillColor=" + light_blue + "fontColor=#000000;"
    for node_id in connected_nodes_ids:
        node_path = './mxCell[@id="' + node_id + '"]'
        node = diagram_root.find(node_path)
        node_style = node.get('style')
        if "ellipse" in node_style and node.get('value') == "":
            for arrow_id in arrows_ids:
                arrow_path = './mxCell[@id="' + arrow_id + '"]'
                arrow = diagram_root.find(arrow_path)
                if arrow.get("source") == previous_node_id and arrow.get("target") == node_id:
                    node.set('value', game_end_reason)
                    node_height = int(float(node.find("./mxGeometry").get('height')))
                    new_height = 50
                    if node_height < new_height:
                        node.find("./mxGeometry").set("height", str(new_height))
                        node.find("./mxGeometry").set("width", str(new_height))
                        node.find("./mxGeometry").set("x", str(int(float(node.find("./mxGeometry").get("x"))) - ((new_height - node_height)/2)))
                    if game_end_reason == "Death":
                        node.set('style', black_circle_style)
                    else:
                        node.set('style', pink_circle_style)
                    arrows_in_the_path.append(arrow_id)
                    return

    previous_node_path = './mxCell[@id="' + previous_node_id + '"]'
    previous_node = diagram_root.find(previous_node_path)
    previous_node_width = int(float(previous_node.find("./mxGeometry").get('width')))

    new_node_y_int = int(float(previous_node.find("./mxGeometry").get('y'))) + 100
    new_node_x_int = int(float(previous_node.find("./mxGeometry").get('x'))) + previous_node_width/2 - 25
    ending_circle_id = str(uuid.uuid4())

    if game_end_reason == "Death":
        new_node_style = black_circle_style
    else:
        new_node_style = blue_circle_style

    attrib_node = {"id": ending_circle_id, "value": game_end_reason, "style": new_node_style, "parent": "1", "vertex": "1"}
    attrib_node_geo = {"x": str(new_node_x_int), "y": str(new_node_y_int), "width": "50", "height": "50", "as": "geometry"}
    my_node = ET.SubElement(diagram_root, "mxCell", attrib_node)
    ET.SubElement(my_node, "mxGeometry", attrib_node_geo)

    new_arrow_style = "rounded=0;orthogonalLoop=1;jettySize=auto;html=1;entryX=0.5;entryY=0;entryDx=0;entryDy=0;fontSize=14;fillColor=" + light_blue + "strokeColor=" + dark_blue + "strokeWidth=" + stroke_width
    add_new_arrow(diagram_root, previous_node_id, ending_circle_id, new_arrow_style)


def set_nodes_and_arrows_styles(diagram_root: ET.Element) -> None:
    """
    Sets various attributes of the style of the nodes and arrows that were present on the diagram and are part of the gameplay
    :param diagram_root: root of the xml file
    :return:
    """
    for element in nodes_in_the_path + arrows_in_the_path:
        set_attribute_style(diagram_root, element, "fillColor=", light_green)
        set_attribute_style(diagram_root, element, "strokeColor=", dark_green)
    for arrow in arrows_in_the_path:
        set_attribute_style(diagram_root, arrow, "strokeWidth=", stroke_width)


def set_attribute_style(diagram_root: ET.Element, element_id: str, attribute_name: str, new_attribute_style: str) -> None:
    """
    Sets given attribute of the element (node or arrow) to the given style
    :param diagram_root: root of the xml file
    :param element_id: id of the given node or arrow
    :param attribute_name: name of the attribute to set
    :param new_attribute_style: new style of the given attribute
    :return:
    """
    element_path = './mxCell[@id="' + element_id + '"]'
    element = diagram_root.find(element_path)
    element_style = element.get('style')
    if attribute_name in element_style:
        divided_style = element_style.split(attribute_name)
        after_first_delimiter = divided_style[1].split(";", 1)[1]
        my_style = divided_style[0] + attribute_name + new_attribute_style + after_first_delimiter
    else:
        my_style = element_style + attribute_name + new_attribute_style
    element.set('style', my_style)
