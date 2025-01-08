# Imports
from openai import OpenAI
from datetime import datetime
import pandas as pd
import streamlit as st
import tempfile
import streamlit.components.v1 as components
import uuid
import time

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
    page_title="Analisis de tickets con IA Iconstruye (IAcontruye)",
    page_icon="🤖"
)

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
    asistente = st.selectbox("Selecciona el asistente", ["JARVIS CES", "JARVIS HVAC"])
    
    # Update API key and assistant ID based on the selected assistant
    if asistente == "JARVIS CES":
        assistant_id = st.secrets["assistant_id_ces"]
    elif asistente == "JARVIS HVAC":
        assistant_id = st.secrets["assistant_id_hvac"]

    client = OpenAI(api_key=api_key_st)

    if st.button("ocultar/mostrar archivos"):
        st.write ("archivos cargados")
        files_names()

    print("Starting main function")  # Debugging identifier
    # Directly initialize the conversation
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        print("Initialized session_id")  # Debugging identifier

    if "run" not in st.session_state:
        st.session_state.run = {"status": None}
        print("Initialized run")  # Debugging identifier

    if "messages" not in st.session_state:
        st.session_state.messages = []
        print("Initialized messages")  # Debugging identifier

    if "retry_error" not in st.session_state:
        st.session_state.retry_error = 0
        print("Initialized retry_error")  # Debugging identifier

    # Initialize the thread
    if 'thread' not in st.session_state:
        st.session_state['thread'] = client.beta.threads.create(
            metadata={'session_id': st.session_state.session_id}
        )
        print("Initialized thread")  # Debugging identifier

    # se recupera la lista de mensajes de la conversacion entre el usuario y el bot, para imprimirse en pantalla
    elif hasattr(st.session_state.run, 'status') and st.session_state.run.status =="completed":
        print("Run status is completed")  # Debugging identifier
        st.session_state.all_messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread.id)
        with st.container(border=True, height=500):
            for message in reversed(st.session_state.all_messages.data):
                if message.role in ["user", "assistant"]:
                    role_text = "Usuario" if message.role == "user" else (f"JARVIS: {assistant_id}")
                    with st.chat_message(message.role):
                        for content_part in message.content:
                            if content_part.type == "text":
                                message_text = content_part.text.value

                                # hora y minuto del mensaje
                                message_time = datetime.fromtimestamp(message.created_at)
                                formatted_time = message_time.strftime('%H:%M')

                                # se muestra el nombre, la hora y el texto del mensaje
                                st.markdown(f"**{role_text}** - {formatted_time}")
                                st.markdown(message_text)
                            elif content_part.type == "image_file":
                                file_id = content_part.image_file.file_id
                                response = client.files.content(file_id)
                                image_data = response.read()  # Convertir a datos binarios
                                if isinstance(image_data, bytes):
                                    temp_image_file = tempfile.NamedTemporaryFile(delete=False)
                                    temp_image_file.write(image_data)
                                    temp_image_file.close()
                                    st.image(temp_image_file.name, caption=f"{role_text} - {formatted_time}", use_column_width=True)
                                else:
                                    st.error("Error: image_data no es un objeto de bytes")

    # logica de la conversacion
    if consulta := st.chat_input("¿En que puedo ayudarte?"):
        print("User input received")  # Debugging identifier
        with st.chat_message("user"):
            st.write(consulta)

        # se agregan los mesajes al hilo
        message = {
            "thread_id": st.session_state.thread.id,
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": consulta
                }
            ],
        }

        # id del hilo
        # def thread_id():
        # return st.session_state['thread'].id
        try:
            st.session_state.messages = client.beta.threads.messages.create(**message)
            print("Message created")  # Debugging identifier
        except TypeError as e:
            st.error(f"Ocurrio un error al crear el mensaje: {e}")

        st.session_state.run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread.id,
            assistant_id=assistant_id,
            tools=[{"type": "code_interpreter", "type": "file_search"}],
        )
        print("Run created")  # Debugging identifier

    # Retry logic
        if st.session_state.retry_error < 3:
            print("Retry logic triggered")  # Debugging identifier
            time.sleep(1)
            print("Before rerun")  # Debugging identifier
            st.rerun()
            print("After rerun")  # Debugging identifier

    # Check the status of the execution
    if hasattr(st.session_state.run, 'status'):
        if st.session_state.run.status == "running":
            with st.chat_message('assistant'):
                st.write("Cargando......")
            if st.session_state.retry_error < 3:
                time.sleep(1)
                print("Before rerun in running status")  # Debugging identifier
                st.rerun()
                print("After rerun in running status")  # Debugging identifier
        elif st.session_state.run.status == "failed":
            st.session_state.retry_error += 1
            with st.chat_message('assistant'):
                if st.session_state.retry_error < 3:
                    st.write("Proceso fallido, reintentando ......")
                    time.sleep(3)
                    print("Before rerun in failed status")  # Debugging identifier
                    st.rerun()
                    print("After rerun in failed status")  # Debugging identifier
                else:
                    st.error("Error: La api de Open AI actualmente esta procesando demasiadas consultas, intente otra vez dentro de un momento ......")
        elif st.session_state.run.status != "completed":
            st.session_state.run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread.id,
                run_id=st.session_state.run.id
            )
            if st.session_state.retry_error < 3:
                time.sleep(3)
                print("Before rerun in not completed status")  # Debugging identifier
                st.rerun()
                print("After rerun in not completed status")  # Debugging identifier

if __name__ == "__main__":
    main()