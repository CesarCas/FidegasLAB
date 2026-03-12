import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Fidegas Panel", layout="wide")

# --- RELLENA SOLO ESTO ---
# El ID es el código largo de la URL de tu Google Sheet
ID_HOJA = "TU_ID_DE_GOOGLE_SHEETS_AQUI" 

# --- USUARIOS ---
USUARIOS = {"admin": "123", "mantenimiento": "456"}

# 2. LOGIN
if "autenticado" not in st.session_state:
    st.title("🛡️ Acceso Fidegas")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Error de acceso")
    st.stop()

# 3. CARGA DE DATOS (GOOGLE SHEETS)
CSV_URL = f"https://docs.google.com/spreadsheets/d/https://docs.google.com/spreadsheets/d/1grw6hICGLD-k4F1LFCmdLX9vaPEYTK20V9GnP6M6O_Y/edit?usp=drive_link/export?format=csv"

@st.cache_data(ttl=5) # Se actualiza muy rápido para pruebas
def cargar():
    try:
        df = pd.read_csv(CSV_URL)
        # Limpieza básica de datos
        if 'Planta' in df.columns:
            df['Planta'] = pd.to_numeric(df['Planta'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

df = cargar()

# 4. INTERFAZ
if os.path.exists("logo.png"):
    st.image("logo.png", width=120)

if not df.empty:
    st.title("Control de Sondas en Tiempo Real")
    
    # Métricas rápidas
    col1, col2 = st.columns(2)
    col1.metric("Sondas Activas", len(df))
    criticas = len(df[df['Días Restantes'] < 45])
    col2.metric("Alertas Críticas", criticas, delta=-criticas, delta_color="inverse")

    # Gráfico
    fig = px.bar(df, x='Num_Serie', y='Días Restantes', color='Días Restantes',
                 color_continuous_scale='RdYlGn', title="Estado del Inventario")
    st.plotly_chart(fig, use_container_width=True)

    # Tabla interactiva
    st.subheader("📋 Listado de Mantenimiento")
    st.data_editor(df, use_container_width=True)
else:
    st.warning("No se han podido cargar datos. Revisa el ID de la hoja y los permisos de compartir.")

if st.sidebar.button("Salir"):
    del st.session_state["autenticado"]
    st.rerun()

