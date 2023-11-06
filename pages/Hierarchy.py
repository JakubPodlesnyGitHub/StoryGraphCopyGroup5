import streamlit as st
import logging
import os
import sys
from pathlib import Path
from library.tools import get_project_root
from library.tools import get_quest_nr, draw_production_tree_st, get_project_root
from library.tools_match import check_hierarchy, get_production_tree_new
from library.tools_validation import get_jsons_storygraph_validated
import graphviz

path_root = get_project_root() / Path('examples')



#################################################################
mask = '*.json'
# mask = 'Hackaton2023/*.json'
dir_name = ''
json_path = f'{path_root}/{dir_name}'
jsons_OK, jsons_schema_OK, errors, warnings = get_jsons_storygraph_validated(json_path)
mission_list = []
for element in jsons_OK:
    if "world" not in element["file_path"]:
        mission_list.append(element["file_path"])



st.set_page_config(page_title="StoryGraph – Productions hierarchy", layout="wide")
st.title('StoryGraph – Productions hierarchy')
# st.subheader('Main plot data settings!!')
# col1, col2, col3 = st.columns(3)
dpi = st.number_input(f'Rozdzielczosć rysunku', value=100, min_value=30, step=10)
mision_name = st.selectbox(
    'Wybierz misję', mission_list)

# Testy generowania drzewa produkcji ###################################################################################


jsons_list = []
for quest_json in jsons_schema_OK:
    if mision_name in quest_json["file_path"]:
        title_list_for_bold = []
        for p in quest_json["json"]:
            title_list_for_bold.append(p["Title"])

        prod_hierarchy, g, m = get_production_tree_new(jsons_schema_OK[get_quest_nr('produkcje_generyczne', jsons_schema_OK)], quest_json)

        if prod_hierarchy:
            graph_hierarchy = draw_production_tree_st(prod_hierarchy, missing=m, mission_name=f'hierarchia_produkcji_{quest_json["file_path"].split(os.sep)[-1].rsplit(".",1)[0]}', title_list_for_bold=title_list_for_bold)
            graph_hierarchy.attr(dpi=str(dpi))
            st.write("Przewiń w dół, aby zobaczyć wykres.")
            # graph_hierarchy.attr(bgcolor="lightblue")
            # graph_hierarchy.attr(margin="0")
            st.graphviz_chart(graph_hierarchy, use_container_width=False)
            st.write("Przewiń w górę, aby zobaczyć wykres.")





