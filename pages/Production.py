import json
import locale

import streamlit as st

# locale.setlocale(locale.LC_ALL, "pl_PL")
from config.config import path_root
from library.tools import find_file
from PIL import Image

from library.tools_validation import get_jsons_storygraph_validated

query_params = st.experimental_get_query_params()
try:
    title = query_params["title"][0]
    st.set_page_config(
        page_title="title",
        layout="wide"
    )
except:
    st.set_page_config(
        page_title="Produkcja",
        layout="wide"
    )
    title = st.text_input("Podaj nazwę produkcji")

if title:
    st.title(f'StoryGraph – {title}')
    # st.write('test')
    # st.subheader('Test')
    json_path = f'{path_root}/aktualne wizualizacje'
    # st.write(json_path)
    image_path = find_file(json_path, f'{title}.png')

    try:
        image = Image.open(image_path)
        st.image(image)

    except:
        st.write("Brakuje obrazka")




    json_path = f'{path_root}'
    jsons_sg_validated, jsons_schema_validated, errors, warnings = get_jsons_storygraph_validated(json_path)
    for element in jsons_sg_validated:

        for p in element["json"]:
            if title in p["Title"]:
                st.write(f'Nazwa misji: {element["file_path"]} (wybrana w zakładce Hierarchy)')
                # st.write(p["Title"])

                st.json(p, expanded=True)
                # st.text_area("Tekst produkcji do kopiowania", json.dumps(p, ensure_ascii=False).replace(",", ",\n"), height=5000)


    # st.write("Buuu")
    # st.write(jsons_sg_validated)


