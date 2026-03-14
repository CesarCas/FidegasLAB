import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Fidegas Smart Control", layout="wide")

ID_HOJA = "1grw6hICGLD-k4F1LFCmdLX9vaPEYTK20V9GnP6M6O_Y"
URL_API_GOOGLE = "https://script.google.com/macros/s/AKfycbxwIdQN5QKtpzkWC8KWk26gU4cNlZzcwUywQBjNfbtcKJhgtnCBWp3TwE94uNz6wIQgqg/exec"
USUARIOS = {"admin": "123", "mantenimiento": "456"}

# 2. LOGIN
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🛡️ Acceso Fidegas PoC")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state["autenticado"] = True
            st.rerun()
    st.stop()

# 3. LÓGICA Y CARGA
MAPA_VIDA_UTIL = {"O2": 24, "CO": 24, "H2": 48, "NH3": 24, "H2S": 24}

@st.cache_data(ttl=5)
def cargar_datos():
    url = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/export?format=csv"
    try:
        df = pd.read_csv(url)
        hoy = datetime.now()
        
        # Limpiar y convertir fecha
        df['Fecha_Instalacion'] = pd.to_datetime(df['Fecha_Instalacion'].astype(str).str.replace('#', ''), errors='coerce')
        
        # Lógica de vida útil y caducidad
        df['Vida_Util_Meses'] = df['Tipo_Gas'].map(MAPA_VIDA_UTIL).fillna(24)
        df['Caducidad'] = df.apply(
            lambda x: x['Fecha_Instalacion'] + timedelta(days=int(x['Vida_Util_Meses'] * 30.44)) 
            if pd.notnull(x['Fecha_Instalacion']) else pd.NaT, axis=1
        )
        
        # Calcular Días Restantes
        df['Días Restantes'] = (df['Caducidad'] - hoy).dt.days.fillna(0).astype(int)
        
        return df
    except:
        return pd.DataFrame()

df = cargar_datos()

# 4. FUNCIÓN DE COLOR CORREGIDA (Para evitar el TypeError)
def style_semaforo(row):
    dias = row['Días Restantes']
    if dias < 45:
        color = 'background-color: #ff4b4b; color: white' # Rojo
    elif dias <= 100:
        color = 'background-color: #ffa500; color: black' # Naranja
    else:
        color = 'background-color: #28a745; color: white' # Verde
    
    # Aplicamos el color a toda la fila o solo a columnas específicas
    return [color] * len(row)

# 5. INTERFAZ
st.title("🚀 Gestión de Sondas Fidegas")

if not df.empty:
    tab1, tab2 = st.tabs(["📊 Análisis Visual", "🛠️ Editor de Campo"])

    with tab1:
        st.subheader("Estado de la Red")
        # Gráfico
        fig = px.bar(df, x='Num_Serie', y='Días Restantes', color='Días Restantes',
                     color_continuous_scale=['red', 'orange', 'green'])
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla con semáforo corregida
        st.write("### Vista de Prioridades")
        st.dataframe(df.style.apply(style_semaforo, axis=1), use_container_width=True)

    with tab2:
        st.subheader("Modificar Datos")
        # Editor
        df_editado = st.data_editor(
            df,
            use_container_width=True,
            column_config={
                "Tipo_Gas": st.column_config.SelectboxColumn("Gas", options=["O2", "CO", "H2", "NH3", "H2S"]),
                "Estado_Revision": st.column_config.SelectboxColumn("Estado", options=["OK", "KO", "KO Calibrar"]),
                "Fecha_Instalacion": st.column_config.DateColumn("Instalación")
            },
            key="editor_fidegas_final"
        )

        if st.button("💾 SINCRONIZAR CAMBIOS"):
            st.success("Enviando cambios...")
            st.balloons()
else:
    st.info("Cargando datos de Vitoria...")
