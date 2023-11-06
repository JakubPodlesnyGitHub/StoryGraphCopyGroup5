import locale

import streamlit as st

# locale.setlocale(locale.LC_ALL, "pl_PL")

st.set_page_config(
    page_title="Title",
    layout="wide"
)
st.title('Title')
st.write('test')
st.subheader('Test')
