# Imports
from openai import OpenAI
from datetime import datetime
import pandas as pd
import streamlit as st
# session_state: es una facultad que permite conservar informacion al momento de interactuar
# con la pagina, dado que cada interaccion ejecuta el script desde el principio

ignorar = [""]
api_key_st = st.secrets["openai_api_key"]
assistant_id_st = st.secrets["assistant_id_hvac"]

# Configurar las crendeciales del api y el id del asistente
client = OpenAI(api_key=api_key_st)
assistant_id = assistant_id_st

# Titulo de la pagina
st.set_page_config(
    page_title="Jarvis",
    page_icon="🤖"
)
st.title("Main page")
st.write("Lista de archivos cargados al sistema \n(el conocimiento del sistema se basa y limita en estos archivos)")
# ---------------------------------------------
# -------------inicio funciones----------------
# ---------------------------------------------


# lista de archivos cargados
def files_names():
    archives = client.files.list()
    files = archives.data
    files_sorted = sorted(files, key=lambda x: x.created_at)
    names = [file_obj.filename for file_obj in files_sorted]
    df = pd.DataFrame(names, columns=["Nombre del archivo"])
    table_names = st.table(df)
    return table_names

# Creacion hilo
if 'thread' not in st.session_state:
    st.session_state['thread'] = client.beta.threads.create()

# Id del hilo
def thread_id():
    return st.session_state['thread'].id

# ----------------------------------------------------------------
# ---------------------inicio opciones/lectura---------------------
# ----------------------------------------------------------------

def main():
    
    if 'show_files' not in st.session_state:
        st.session_state['show_files'] = False

    if st.button("mostrar/ocultar archivos"):
        st.session_state['show_files'] = not st.session_state['show_files']

    if st.session_state['show_files']:
        st.write("archivos cargados")
        files_names()



if __name__ == "__main__":
    main()