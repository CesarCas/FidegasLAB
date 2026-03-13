import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# 1. CONFIGURACIÓN Y DATOS
st.set_page_config(page_title="Fidegas Smart Control", layout="wide")

ID_HOJA = "1grw6hICGLD-k4F1LFCmdLX9vaPEYTK20V9GnP6M6O_Y"
URL_API_GOOGLE = "TU_URL_AQUÍ" # <--- Pon tu URL /exec aquí

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

# 3. CARGA Y PROCESADO DE DATOS
@st.cache_data(ttl=2)
def cargar_datos():
    url = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/export?format=csv"
    df = pd.read_csv(url)
    # Limpieza de datos para que los gráficos no fallen
    if 'Días Restantes' in df.columns:
        df['Días Restantes'] = pd.to_numeric(df['Días Restantes'], errors='coerce').fillna(0)
    return df

df = cargar_datos()

# 4. INTERFAZ VISUAL
st.sidebar.title("Fidegas Control")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state["autenticado"] = False
    st.rerun()

st.title("🚀 Dashboard de Sondas - Fidegas")

tab1, tab2 = st.tabs(["📊 Análisis Visual", "🛠️ Gestión y Sincronización"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Estado de Caducidad")
        fig_bar = px.bar(df, x='Num_Serie', y='Días Restantes', color='Días Restantes',
                         color_continuous_scale='RdYlGn', title="Días hasta revisión")
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        st.subheader("Mapa de Calor (Urgencia)")
        # Creamos una matriz simple para el Heatmap
        fig_heat = px.density_heatmap(df, x="Planta", y="Tipo_Gas", z="Días Restantes",
                                      color_continuous_scale='Viridis', title="Concentración por Riesgo")
        st.plotly_chart(fig_heat, use_container_width=True)

with tab2:
    st.subheader("Edición de Datos en Tiempo Real")
    # Mostramos el editor y guardamos los cambios en 'df_editado'
    df_editado = st.data_editor(df, use_container_width=True, key="editor_vitoria")
    
    st.divider()
    
    if st.button("💾 SINCRONIZAR TODOS LOS CAMBIOS", use_container_width=True):
        # Buscamos qué filas han cambiado comparando con el original
        cambios_detectados = 0
        for i in range(len(df)):
            if df.iloc[i]['Estado_Revision'] != df_editado.iloc[i]['Estado_Revision']:
                sonda_id = str(df_editado.iloc[i]['Num_Serie'])
                nuevo_status = str(df_editado.iloc[i]['Estado_Revision'])
                
                # Enviamos cada cambio a Google
                requests.post(URL_API_GOOGLE, json={"num_serie": sonda_id, "nuevo_estado": nuevo_status})
                cambios_detectados += 1
        
        if cambios_detectados > 0:
            st.success(f"✅ ¡{cambios_detectados} cambios guardados en la nube!")
            st.balloons()
            st.cache_data.clear() # Forzamos recarga
        else:
            st.info("No se detectaron cambios en la columna 'Estado_Revision'.")
