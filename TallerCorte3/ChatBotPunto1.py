from gtts import gTTS
import os
import base64
import streamlit as st
import requests
from streamlit_mic_recorder import speech_to_text

# API de DeepSeek
API_KEY = 'sk-53751d5c6f344a5dbc0571de9f51313e'
API_URL = 'https://api.deepseek.com/v1/chat/completions'

def obtener_respuesta(mensaje):
    prompt = f"Eres experto en IoT y emprendimientos. Habla de forma natural sin usar asteriscos. Responde en máximo 80 palabras sobre: {mensaje}"
    
    headers = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}
    data = {
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 120,  # Punto medio
        'temperature': 0.7  # Más natural
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=15)  # Más tiempo
        if response.status_code == 200:
            texto = response.json()['choices'][0]['message']['content']
            texto = texto.replace('*', '').replace('**', '')
            return texto
        else:
            # Si falla con muchos tokens, intentar con menos
            data['max_tokens'] = 80
            response = requests.post(API_URL, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                texto = response.json()['choices'][0]['message']['content']
                return texto.replace('*', '').replace('**', '')
    except:
        pass
    return "Error. Intenta de nuevo."

def crear_audio(texto):
    tts = gTTS(texto, lang='es')
    tts.save("respuesta.mp3")
    with open("respuesta.mp3", "rb") as f:
        audio_data = f.read()
    os.remove("respuesta.mp3")
    return base64.b64encode(audio_data).decode()

# Interfaz
st.title("🎙️ ChatBot IoT & Emprendimientos")
st.write("Habla sobre IoT o emprendimientos tecnológicos")

# Micrófono
texto = speech_to_text(language="es", key="mic")

if texto:
    with st.spinner("🤖 Procesando..."):
        respuesta = obtener_respuesta(texto)
        audio_b64 = crear_audio(respuesta)
    
    # Solo mostrar audio
    st.audio(base64.b64decode(audio_b64), format='audio/mp3', autoplay=True)