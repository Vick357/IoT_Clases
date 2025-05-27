import streamlit as st
import requests

# Configuración de la página
st.set_page_config(
    page_title="DeepSeek",
    page_icon="",
    layout="centered"
)

# Reemplaza 'TU_API_KEY' con tu clave API de DeepSeek
API_KEY = 'sk-53751d5c6f344a5dbc0571de9f51313e' 
API_URL = 'https://api.deepseek.com/v1/chat/completions'

def enviar_mensaje(mensaje, modelo = 'deepseek-chat'):
    headers = {
        'Authorization' : f'Bearer {API_KEY}',
        'Content-Type' : 'application/json'
    }

    data = {
        'model' : modelo,
        'messages' : [{'role': 'user', 'content': mensaje}]
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status() #Lanza una excepción si hay un error HTTp
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.HTTPError as err:
        return f"Error de la API: {err}"
    except Exception as e:
        return f"Error inesperado: {e}"
    
# Inicializar el historial del chat
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Mostrar el historial de mensajes
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Widget de entrada de chat
if prompt := st.chat_input("Escribe tu mensaje..."):
    # Manejar comando 'salir'
    if prompt.lower() == 'salir':
        respuesta = "¡Hasta luego!"
    else:
        # Mostrar mensaje de usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Obtener y mostrar respuesta 
        respuesta = enviar_mensaje(prompt)

    # Mostrar respuesta del asistente
    with st.chat_message("assistant"):
        st.markdown(respuesta) 
        
    # Guardar respuesta en historial
    st.session_state.messages.append({"role": "assistant", "content": respuesta})

# CSS personalizado (opcional)
st.markdown("""
    <style>
    .stChatInput {
            position: fixed;
            bottom: 20px
            width: 70%;
            left: 50%;
            transform : translateX(-50%),
    }
            
    .stChatMessage {
            padding: 1.5rem;
            border-radius: 15px;
            margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)