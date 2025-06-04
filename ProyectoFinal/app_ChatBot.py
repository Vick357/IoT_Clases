import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime
import numpy as np
from gtts import gTTS
import os
import base64
from streamlit_mic_recorder import speech_to_text

# Configuración
st.set_page_config(
    page_title="Clasificador de Monedas + ChatBot IoT",
    page_icon="🪙",
    layout="wide"
)

# Paleta de colores moderna
COLORS = {
    'primary': '#6366F1',    # Indigo vibrante
    'secondary': '#EC4899',  # Rosa intenso
    'tertiary': '#10B981',   # Verde esmeralda
    'accent': '#F59E0B',     # Ámbar
    'dark': '#1F2937',       # Gris oscuro
    'light': '#F3F4F6',      # Gris claro
    'gradient': ['#667eea', '#764ba2', '#f093fb']
}

# URLs y configuración
FIREBASE_URL = "https://clasificador-d7264-default-rtdb.firebaseio.com/IoT.json"
API_KEY = 'sk-53751d5c6f344a5dbc0571de9f51313e'
API_URL = 'https://api.deepseek.com/v1/chat/completions'

# Especificaciones técnicas completas de las monedas colombianas
ESPECIFICACIONES_MONEDAS = {
    "50_nueva": {"diametro": "17 mm", "espesor": "1.17 mm", "peso": "2 g", "denominacion": "50 pesos nueva"},
    "50_vieja": {"diametro": "21 mm", "espesor": "1.3 mm", "peso": "4 g", "denominacion": "50 pesos vieja"},
    "200_nueva": {"diametro": "22.4 mm", "espesor": "2.1 mm", "peso": "4.61 g", "denominacion": "200 pesos nueva"},
    "200_vieja": {"diametro": "24.4 mm", "espesor": "1.7 mm", "peso": "7.1 g", "denominacion": "200 pesos vieja"},
    "1000": {"diametro": "26.7 mm", "espesor": "2.2 mm", "peso": "9.95 g", "denominacion": "1000 pesos"}
}

@st.cache_data(ttl=30)
def obtener_datos_firebase():
    try:
        response = requests.get(FIREBASE_URL, timeout=10)
        return response.json() if response.status_code == 200 and response.json() else {}
    except:
        return {}

def obtener_respuesta_especializada(mensaje, datos_sistema):
    """Función especializada para el chatbot del proyecto IoT"""
    valor_total = (datos_sistema.get('Monedas1000', 0) * 1000 + 
                   datos_sistema.get('Monedas200', 0) * 200 + 
                   datos_sistema.get('Monedas50', 0) * 50)
    
    # Crear contexto super específico del proyecto
    contexto_proyecto = f"""
    Eres el asistente especializado del Sistema Clasificador IoT de Monedas Colombianas desarrollado por estudiantes de Ingeniería Electrónica.
    
    DATOS EN TIEMPO REAL DEL SISTEMA:
    - Total de monedas clasificadas exitosamente: {datos_sistema.get('ConteoGlobal', 0)}
    - Monedas de 1000 pesos colombianos: {datos_sistema.get('Monedas1000', 0)} unidades
    - Monedas de 200 pesos colombianos: {datos_sistema.get('Monedas200', 0)} unidades  
    - Monedas de 50 pesos colombianos: {datos_sistema.get('Monedas50', 0)} unidades
    - Valor total acumulado: {valor_total:,} pesos colombianos (COP)
    - Errores de clasificación detectados: {datos_sistema.get('Error', 0)}
    - Peso actual Caja 1 (monedas 1000 pesos): {datos_sistema.get('PesoCaja1', 0):.2f} gramos
    - Peso actual Caja 2 (monedas 200 pesos): {datos_sistema.get('PesoCaja2', 0):.2f} gramos
    - Peso actual Caja 3 (monedas 50 pesos): {datos_sistema.get('PesoCaja3', 0):.2f} gramos
    
    DESGLOSE DETALLADO NUEVAS VS VIEJAS:
    - Monedas 1000 pesos NUEVAS: {datos_sistema.get('Monedas1000Nuevas', 0)} unidades
    - Monedas 1000 pesos VIEJAS: {datos_sistema.get('Monedas1000Viejas', 0)} unidades (siempre 0)
    - Monedas 200 pesos NUEVAS: {datos_sistema.get('Monedas200Nuevas', 0)} unidades
    - Monedas 200 pesos VIEJAS: {datos_sistema.get('Monedas200Viejas', 0)} unidades
    - Monedas 50 pesos NUEVAS: {datos_sistema.get('Monedas50Nuevas', 0)} unidades
    - Monedas 50 pesos VIEJAS: {datos_sistema.get('Monedas50Viejas', 0)} unidades
    
    ESPECIFICACIONES TÉCNICAS EXACTAS DE MONEDAS COLOMBIANAS:
    - 50 pesos NUEVA: Diámetro 17mm, Espesor 1.17mm, Peso teórico 2g
    - 50 pesos VIEJA: Diámetro 21mm, Espesor 1.3mm, Peso teórico 4g
    - 200 pesos NUEVA: Diámetro 22.4mm, Espesor 2.1mm, Peso teórico 4.61g
    - 200 pesos VIEJA: Diámetro 24.4mm, Espesor 1.7mm, Peso teórico 7.1g
    - 1000 pesos: Diámetro 26.7mm, Espesor 2.2mm, Peso teórico 9.95g
    
    ARQUITECTURA DEL SISTEMA IoT:
    Hardware:
    - Microcontrolador: ESP32 (WiFi integrado)
    - 3 Sensores de peso: HX711 con celdas de carga
      * Sensor 1: GPIO 17-18 (escala 200) → Monedas 1000 pesos
      * Sensor 2: GPIO 19-21 (escala 200) → Monedas 200 pesos y 50 viejas
      * Sensor 3: GPIO 22-23 (escala 280) → Monedas 50 nuevas
    - 3 Sensores infrarrojos de detección:
      * GPIO 16 → Detección monedas 1000 pesos
      * GPIO 4 → Detección monedas 200 pesos / 50 viejas
      * GPIO 15 → Detección monedas 50 nuevas
    
    Conectividad:
    - Red WiFi: "WUSTA" con contraseña "USTA8600"
    - Base de datos: Firebase Realtime Database
    - URL: https://clasificador-d7264-default-rtdb.firebaseio.com/IoT.json
    
    Software:
    - Dashboard: Streamlit con gráficos Plotly
    - Lenguaje: Python (dashboard) y MicroPython (ESP32)
    - Visualizaciones: Barras, tendencias, velocímetro
    
    ALGORITMO DE CLASIFICACIÓN PASO A PASO:
    1. Sensor infrarrojo detecta inserción de moneda
    2. Sistema ejecuta sleep(1) para estabilización física
    3. Sensor HX711 toma 3 lecturas consecutivas con get_units(times=3)
    4. Calcula peso promedio dinámico: peso_total/cantidad_monedas
    5. Aplica rangos de clasificación programados:
       - 1000 pesos: 3.0g - 13.0g (solo nuevas)
       - 200 pesos: 4.7g - 9.0g (nuevas <6.0g, viejas >6.0g)
       - 50 pesos nuevas: 0g - 16.0g (sensor 3)
       - 50 pesos viejas: 2.0g - 4.3g (sensor 2)
    6. Incrementa contadores específicos (nuevas/viejas)
    7. Distingue automáticamente nuevas vs viejas por límites de peso
    8. Actualiza variables: ConteoGlobal, Monedas1000, Monedas200, Monedas50, Error, PesoCaja1-3
    9. Actualiza contadores detallados: Monedas1000Nuevas/Viejas, Monedas200Nuevas/Viejas, Monedas50Nuevas/Viejas
    10. Envía datos a Firebase con urequests.patch()
    11. Dashboard actualiza métricas en tiempo real (TTL=30 segundos)
    
    TOLERANCIAS Y CALIBRACIÓN:
    - Tolerancia general: 15%
    - Tara automática al inicio: hx.tare()
    - Escalas calibradas: 200 (sensores 1,2) y 280 (sensor 3)
    - Límite separación 200 pesos: 6.0g
    - Límite separación 50 pesos: 3.5g
    - Comandos se envían cada 3 monedas: 'a' (1000), 's' (200), 'd' (50)
    
    IMPORTANTE: 
    - Siempre habla en PESOS COLOMBIANOS (COP), nunca dólares
    - Usa datos reales del sistema cuando estén disponibles
    - Sé específico sobre componentes y conexiones GPIO
    - Explica el proceso técnico de forma clara
    - Menciona detalles de programación cuando sea relevante
    - Incluye información de monedas nuevas vs viejas cuando sea pertinente
    
    Responde de forma natural, técnica y educativa sin asteriscos. Máximo 100 palabras por respuesta.
    """
    
    prompt = f"{contexto_proyecto}\n\nPregunta del usuario: {mensaje}"
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 150,
        'temperature': 0.7
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=15)
        if response.status_code == 200:
            texto = response.json()['choices'][0]['message']['content']
            texto = texto.replace('*', '').replace('**', '')
            return texto
        else:
            # Fallback con menos tokens
            data['max_tokens'] = 100
            response = requests.post(API_URL, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                texto = response.json()['choices'][0]['message']['content']
                return texto.replace('*', '').replace('**', '')
    except Exception as e:
        return f"Sistema ocupado. Estado actual: {datos_sistema.get('ConteoGlobal', 0)} monedas clasificadas, valor {valor_total:,} pesos colombianos."
    
    return "El clasificador IoT continúa operando correctamente."

def crear_audio(texto):
    """Crear audio usando gTTS"""
    try:
        tts = gTTS(texto, lang='es', slow=False)
        tts.save("respuesta.mp3")
        with open("respuesta.mp3", "rb") as f:
            audio_data = f.read()
        os.remove("respuesta.mp3")
        return base64.b64encode(audio_data).decode()
    except Exception as e:
        st.error(f"Error generando audio: {e}")
        return None

# Header
st.markdown("""
<div style='text-align: center; padding: 20px; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 30px;'>
    <h1 style='color: white; margin: 0;'>🪙 Sistema Clasificador IoT + 🎙️ ChatBot Especializado</h1>
    <p style='color: rgba(255,255,255,0.8); margin: 5px 0 0 0;'>Monitoreo en Tiempo Real + Asistente Virtual de Proyecto</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Control del Sistema")
    
    if st.button("🔄 Actualizar Datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    auto_refresh = st.checkbox("Auto-actualizar", value=True)
    refresh_interval = st.slider("Intervalo (seg)", 5, 60, 10)
    
    st.markdown("---")
    st.markdown("### 🎙️ ChatBot IoT Especializado")
    st.write("*Experto en tu proyecto de clasificación*")
    
    # Estado del procesamiento
    if 'procesando_chatbot' not in st.session_state:
        st.session_state.procesando_chatbot = False
    
    # Obtener datos para el chatbot
    datos_chat = obtener_datos_firebase()
    if not datos_chat:
        datos_chat = {
            'ConteoGlobal': 5, 'Monedas1000': 4, 'Monedas200': 1, 'Monedas50': 0,
            'Error': 1, 'PesoCaja1': 32.28, 'PesoCaja2': 8.22, 'PesoCaja3': 0,
            'Monedas1000Nuevas': 4, 'Monedas1000Viejas': 0,
            'Monedas200Nuevas': 0, 'Monedas200Viejas': 1,
            'Monedas50Nuevas': 0, 'Monedas50Viejas': 0
        }
    
    # Micrófono para input por voz
    st.markdown("**🎤 Habla con el asistente:**")
    texto_voz = speech_to_text(
        language="es", 
        key="mic_clasificador",
        start_prompt="🎙️ Presiona para hablar",
        stop_prompt="⏹️ Parar grabación", 
        just_once=True,
        use_container_width=True
    )
    
    # Función para procesar con audio automático
    def procesar_con_audio(pregunta):
        if pregunta and not st.session_state.procesando_chatbot:
            st.session_state.procesando_chatbot = True
            
            with st.spinner("🤖 El asistente IoT está analizando..."):
                respuesta = obtener_respuesta_especializada(pregunta, datos_chat)
                
                # Mostrar respuesta
                st.success("🗣️ **Respuesta del Especialista:**")
                st.info(respuesta)
                
                # Generar y reproducir audio automáticamente
                with st.spinner("🔊 Creando audio..."):
                    audio_b64 = crear_audio(respuesta)
                    if audio_b64:
                        st.audio(base64.b64decode(audio_b64), format='audio/mp3', autoplay=True)
                        st.success("✅ Audio reproducido automáticamente")
                    else:
                        st.warning("⚠️ Audio no disponible")
            
            st.session_state.procesando_chatbot = False
    
    # Procesar automáticamente al detectar voz
    if texto_voz and not st.session_state.procesando_chatbot:
        procesar_con_audio(texto_voz)
    
    # Estado del chatbot
    if st.session_state.procesando_chatbot:
        st.warning("⏳ Procesando consulta...")
    else:
        st.success("✅ Listo para consultas")
    
    st.markdown("---")
    st.markdown("**💡 Consultas Expertas:**")
    
    if st.button("📊 Estado del sistema", use_container_width=True, disabled=st.session_state.procesando_chatbot):
        procesar_con_audio("¿Cuál es el estado actual del sistema clasificador con todos los datos?")
    
    if st.button("🪙 Especificaciones monedas", use_container_width=True, disabled=st.session_state.procesando_chatbot):
        procesar_con_audio("¿Cuáles son las especificaciones exactas de diámetro, espesor y peso de todas las monedas?")
    
    if st.button("⚙️ Componentes IoT", use_container_width=True, disabled=st.session_state.procesando_chatbot):
        procesar_con_audio("Explícame los componentes del sistema: ESP32, sensores HX711, GPIO y conexiones")
    
    if st.button("🔍 Algoritmo clasificación", use_container_width=True, disabled=st.session_state.procesando_chatbot):
        procesar_con_audio("¿Cómo funciona exactamente el algoritmo de clasificación paso a paso?")
    
    if st.button("🔢 Desglose nuevas/viejas", use_container_width=True, disabled=st.session_state.procesando_chatbot):
        procesar_con_audio("¿Cuántas monedas nuevas y viejas hay de cada denominación? Dame el desglose completo.")

# Datos principales
datos = obtener_datos_firebase()

# Estado conexión
conexion_ok = bool(datos)
if conexion_ok:
    st.sidebar.info("✅ Conectado a Firebase")
    st.sidebar.info(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
else:
    st.sidebar.error("❌ Desconectado - Datos Demo")
    # Datos demo
    datos = {
        'ConteoGlobal': 5, 'Monedas1000': 4, 'Monedas200': 1, 'Monedas50': 0,
        'Error': 1, 'PesoCaja1': 32.28, 'PesoCaja2': 8.22, 'PesoCaja3': 0,
        'Monedas1000Nuevas': 4, 'Monedas1000Viejas': 0,
        'Monedas200Nuevas': 0, 'Monedas200Viejas': 1,
        'Monedas50Nuevas': 0, 'Monedas50Viejas': 0
    }

# Cálculos
valor_total = (datos.get('Monedas1000', 0) * 1000 + 
               datos.get('Monedas200', 0) * 200 + 
               datos.get('Monedas50', 0) * 50)
peso_total = sum([datos.get(f'PesoCaja{i}', 0) for i in range(1, 4)])

# KPIs principales (quitamos eficiencia)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🪙 Monedas", datos.get('ConteoGlobal', 0), 
              delta=f"+{datos.get('ConteoGlobal', 0) - 80}" if conexion_ok else None)

with col2:
    st.metric("💰 Valor", f"${valor_total:,}", 
              delta=f"+${valor_total - 150000:,}" if conexion_ok else None)

with col3:
    st.metric("⚖️ Peso", f"{peso_total:.1f}g", 
              delta=f"+{peso_total - 400:.1f}g" if conexion_ok else None)

with col4:
    st.metric("❌ Errores", datos.get('Error', 0), 
              delta=f"-{8 - datos.get('Error', 0)}" if conexion_ok else None)

st.markdown("---")

# Gráficos principales (quitamos el radar y ajustamos distribución)
col1, col2 = st.columns([3, 2])

with col1:
    # Gráfico de barras horizontales mejorado
    fig_horizontal = go.Figure()
    
    denominaciones = ['$1000', '$200', '$50']
    cantidades = [datos.get('Monedas1000', 0), datos.get('Monedas200', 0), datos.get('Monedas50', 0)]
    valores = [datos.get('Monedas1000', 0) * 1000, datos.get('Monedas200', 0) * 200, datos.get('Monedas50', 0) * 50]
    
    colors = [COLORS['primary'], COLORS['secondary'], COLORS['tertiary']]
    
    for i, (denom, cant, val, color) in enumerate(zip(denominaciones, cantidades, valores, colors)):
        fig_horizontal.add_trace(go.Bar(
            y=[denom],
            x=[cant],
            orientation='h',
            name=denom,
            marker=dict(
                color=color,
                line=dict(color='white', width=2)
            ),
            text=f'{cant}',
            textposition='outside',
            textfont=dict(color=color, size=14, family="Arial Black"),
            hovertemplate=f'<b>{denom}</b><br>Cantidad: {cant}<br>Valor: ${val:,}<extra></extra>'
        ))
    
    fig_horizontal.update_layout(
        title="📊 Cantidad por Denominación",
        xaxis_title="Número de Monedas",
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(range=[0, max(cantidades) * 1.2 if max(cantidades) > 0 else 10])
    )
    
    fig_horizontal.update_xaxes(showgrid=True, gridcolor='lightgray', gridwidth=1)
    fig_horizontal.update_yaxes(showgrid=False)
    
    st.plotly_chart(fig_horizontal, use_container_width=True)

with col2:
    # Velocímetro de peso ajustado para datos reales
    peso_total_real = sum([datos.get(f'PesoCaja{i}', 0) for i in range(1, 4)])
    fig_velocimetro = go.Figure(go.Indicator(
        mode="gauge+number",
        value=peso_total_real,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "⚖️ Peso Total del Sistema"},
        number={'suffix': "g", 'font': {'size': 20}},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': COLORS['tertiary']},
            'steps': [
                {'range': [0, 30], 'color': "#FEE2E2"},
                {'range': [30, 60], 'color': "#FEF3C7"},
                {'range': [60, 100], 'color': "#D1FAE5"}
            ],
            'threshold': {
                'line': {'color': COLORS['secondary'], 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    fig_velocimetro.update_layout(height=400)
    st.plotly_chart(fig_velocimetro, use_container_width=True)

# Gráfico combinado de pesos y cantidades
st.markdown("### 📈 Análisis Comparativo: Peso vs Cantidad")

fig_combo = make_subplots(
    specs=[[{"secondary_y": True}]],
    subplot_titles=("Relación Peso-Cantidad por Denominación",)
)

denominaciones = ['$1000', '$200', '$50']
pesos = [datos.get('PesoCaja1', 0), datos.get('PesoCaja2', 0), datos.get('PesoCaja3', 0)]
cantidades = [datos.get('Monedas1000', 0), datos.get('Monedas200', 0), datos.get('Monedas50', 0)]

# Barras de peso
fig_combo.add_trace(
    go.Bar(x=denominaciones, y=pesos, name="Peso (g)", 
           marker_color=COLORS['primary'], opacity=0.7,
           text=[f"{p:.1f}g" for p in pesos], textposition='outside'),
    secondary_y=False,
)

# Línea de cantidad
fig_combo.add_trace(
    go.Scatter(x=denominaciones, y=cantidades, mode='lines+markers+text',
               name="Cantidad", line=dict(color=COLORS['secondary'], width=4),
               marker=dict(size=12, color=COLORS['secondary']),
               text=cantidades, textposition='top center'),
    secondary_y=True,
)

fig_combo.update_xaxes(title_text="Denominación")
fig_combo.update_yaxes(title_text="Peso (g)", secondary_y=False)
fig_combo.update_yaxes(title_text="Cantidad de Monedas", secondary_y=True)

fig_combo.update_layout(height=400, hovermode='x unified')

st.plotly_chart(fig_combo, use_container_width=True)

# Nueva sección: Análisis de Monedas Nuevas vs Viejas
st.markdown("### 🆚 Análisis Detallado: Monedas Nuevas vs Viejas")

col1, col2 = st.columns(2)

with col1:
    # Gráfico de barras apiladas para nuevas vs viejas
    fig_nuevas_viejas = go.Figure()
    
    denominaciones_nv = ['$1000', '$200', '$50']
    
    # Datos de monedas nuevas y viejas
    nuevas = [
        datos.get('Monedas1000Nuevas', 0),
        datos.get('Monedas200Nuevas', 0), 
        datos.get('Monedas50Nuevas', 0)
    ]
    viejas = [
        datos.get('Monedas1000Viejas', 0),
        datos.get('Monedas200Viejas', 0),
        datos.get('Monedas50Viejas', 0)
    ]
    
    # Barras para monedas nuevas
    fig_nuevas_viejas.add_trace(go.Bar(
        name='Nuevas',
        x=denominaciones_nv,
        y=nuevas,
        marker_color=COLORS['tertiary'],
        text=nuevas,
        textposition='inside',
        textfont=dict(color='white', size=12, family="Arial Black"),
        hovertemplate='<b>%{x} Nuevas</b><br>Cantidad: %{y}<extra></extra>'
    ))
    
    # Barras para monedas viejas
    fig_nuevas_viejas.add_trace(go.Bar(
        name='Viejas',
        x=denominaciones_nv,
        y=viejas,
        marker_color=COLORS['accent'],
        text=viejas,
        textposition='inside',
        textfont=dict(color='white', size=12, family="Arial Black"),
        hovertemplate='<b>%{x} Viejas</b><br>Cantidad: %{y}<extra></extra>'
    ))
    
    fig_nuevas_viejas.update_layout(
        title="📊 Distribución Nuevas vs Viejas",
        xaxis_title="Denominación",
        yaxis_title="Cantidad de Monedas",
        barmode='stack',
        height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig_nuevas_viejas, use_container_width=True)

with col2:
    # Gráfico de pastel para el total de nuevas vs viejas
    total_nuevas = sum(nuevas)
    total_viejas = sum(viejas)
    
    if total_nuevas > 0 or total_viejas > 0:
        fig_pastel = go.Figure(data=[go.Pie(
            labels=['Monedas Nuevas', 'Monedas Viejas'],
            values=[total_nuevas, total_viejas],
            hole=0.4,
            marker_colors=[COLORS['tertiary'], COLORS['accent']],
            textinfo='label+percent+value',
            textfont_size=12,
            hovertemplate='<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>'
        )])
        
        fig_pastel.update_layout(
            title="🥧 Proporción Total: Nuevas vs Viejas",
            height=350,
            annotations=[dict(text=f'Total<br>{total_nuevas + total_viejas}', x=0.5, y=0.5, font_size=16, showarrow=False)]
        )
        
        st.plotly_chart(fig_pastel, use_container_width=True)
    else:
        # Mensaje cuando no hay datos
        st.info("🔄 **Sin datos suficientes**\n\nInserta monedas para ver la distribución de nuevas vs viejas")

# Tabla detallada de monedas nuevas vs viejas
st.markdown("### 📋 Tabla Detallada: Estado por Denominación")

# Crear DataFrame para la tabla
df_detalle = pd.DataFrame({
    'Denominación': ['$1000', '$200', '$50'],
    'Nuevas': [
        datos.get('Monedas1000Nuevas', 0),
        datos.get('Monedas200Nuevas', 0),
        datos.get('Monedas50Nuevas', 0)
    ],
    'Viejas': [
        datos.get('Monedas1000Viejas', 0),
        datos.get('Monedas200Viejas', 0),
        datos.get('Monedas50Viejas', 0)
    ],
    'Total': [
        datos.get('Monedas1000', 0),
        datos.get('Monedas200', 0),
        datos.get('Monedas50', 0)
    ],
    'Valor Total': [
        f"${datos.get('Monedas1000', 0) * 1000:,}",
        f"${datos.get('Monedas200', 0) * 200:,}",
        f"${datos.get('Monedas50', 0) * 50:,}"
    ]
})

# Agregar fila de totales
df_detalle.loc[len(df_detalle)] = [
    'TOTAL',
    sum([datos.get('Monedas1000Nuevas', 0), datos.get('Monedas200Nuevas', 0), datos.get('Monedas50Nuevas', 0)]),
    sum([datos.get('Monedas1000Viejas', 0), datos.get('Monedas200Viejas', 0), datos.get('Monedas50Viejas', 0)]),
    datos.get('ConteoGlobal', 0),
    f"${valor_total:,}"
]

# Mostrar la tabla con estilo
st.dataframe(
    df_detalle,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Denominación": st.column_config.TextColumn("💰 Denominación", width="medium"),
        "Nuevas": st.column_config.NumberColumn("🆕 Nuevas", width="small"),
        "Viejas": st.column_config.NumberColumn("📿 Viejas", width="small"),
        "Total": st.column_config.NumberColumn("📊 Total", width="small"),
        "Valor Total": st.column_config.TextColumn("💵 Valor", width="medium")
    }
)

# Resumen en tarjetas
st.markdown("### 📋 Resumen Ejecutivo")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['secondary']}); 
                padding: 20px; border-radius: 10px; color: white; text-align: center;'>
        <h3>🏆 Denominación Líder</h3>
        <h2>${max(['1000', '200', '50'], key=lambda x: datos.get(f'Monedas{x}', 0))}</h2>
        <p>Moneda más clasificada</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    peso_promedio = peso_total / max(datos.get('ConteoGlobal', 1), 1)
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {COLORS['tertiary']}, {COLORS['accent']}); 
                padding: 20px; border-radius: 10px; color: white; text-align: center;'>
        <h3>⚖️ Peso Promedio</h3>
        <h2>{peso_promedio:.2f}g</h2>
        <p>Por moneda clasificada</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    valor_promedio = valor_total / max(datos.get('ConteoGlobal', 1), 1)
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {COLORS['accent']}, {COLORS['primary']}); 
                padding: 20px; border-radius: 10px; color: white; text-align: center;'>
        <h3>💰 Valor Promedio</h3>
        <h2>${valor_promedio:.0f}</h2>
        <p>Por moneda clasificada</p>
    </div>
    """, unsafe_allow_html=True)

# Auto-refresh
if auto_refresh:
    import time
    time.sleep(refresh_interval)
    st.rerun()

# Footer
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; padding: 20px; 
                background: linear-gradient(90deg, {COLORS['primary']}, {COLORS['secondary']}); 
                border-radius: 10px; margin-top: 30px;'>
        <p style='color: white; margin: 0;'>
            🎓 <b>Sistema IoT Clasificador de Monedas + ChatBot Especializado</b> | 
            🚀 <b>v3.0 AI Enhanced</b> | 
            ⏱️ <b>Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}</b>
        </p>
    </div>
    """, 
    unsafe_allow_html=True
)