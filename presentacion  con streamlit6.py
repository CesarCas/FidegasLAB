import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Fidegas Smart Control", layout="wide")

ID_HOJA = "1grw6hICGLD-k4F1LFCmdLX9vaPEYTK20V9GnP6M6O_Y"
URL_API_GOOGLE = "TU_URL_DE_APPS_SCRIPT_AQUÍ" 

USUARIOS = {"admin": "123", "mantenimiento": "456"}

# Mapas de configuración para la lógica automática
MAPA_VIDA_UTIL = {"O2": 24, "CO": 24, "H2": 48, "NH3": 24, "H2S": 24}

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

# 3. CARGA Y LÓGICA DE INTELIGENCIA
@st.cache_data(ttl=2)
def cargar_datos():
    url = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/export?format=csv"
    try:
        df = pd.read_csv(url)
        # Limpieza inicial de fechas
        df['Fecha_Instalacion'] = pd.to_datetime(df['Fecha_Instalacion'].astype(str).str.replace('#', ''), errors='coerce')
        
        # Aplicamos la lógica de vida útil según el gas
        df['Vida_Util_Meses'] = df['Tipo_Gas'].map(MAPA_VIDA_UTIL).fillna(24)
        
        # Calculamos la Caducidad: Instalación + Vida Útil (meses * 30 días aprox)
        df['Caducidad'] = df.apply(lambda x: x['Fecha_Instalacion'] + timedelta(days=x['Vida_Util_Meses']*30) if pd.notnull(x['Fecha_Instalacion']) else pd.NaT, axis=1)
        
        # Calculamos Días Restantes
        hoy = datetime.now()
        df['Días Restantes'] = (df['Caducidad'] - hoy).dt.days.fillna(0).astype(int)
        
        return df
    except:
        return pd.DataFrame()

df = cargar_datos()

# 4. FUNCIÓN PARA COLOREAR FILAS
def color_filas(val):
    if val < 45:
        return 'background-color: #ff4b4b; color: white' # Rojo
    elif 45 <= val <= 100:
        return 'background-color: #ffa500; color: black' # Naranja
    else:
        return 'background-color: #28a745; color: white' # Verde

# 5. INTERFAZ
st.title("🚀 Gestión Inteligente Fidegas")

if not df.empty:
    # Mostramos la tabla con configuración de desplegables
    st.subheader("🛠️ Panel de Mantenimiento")
    
    df_editado = st.data_editor(
        df,
        use_container_width=True,
        column_config={
            "Tipo_Gas": st.column_config.SelectboxColumn(
                "Tipo de Gas",
                options=["O2", "CO", "H2", "NH3", "H2S"],
                required=True
            ),
            "Estado_Revision": st.column_config.SelectboxColumn(
                "Estado Revisión",
                options=["OK", "KO", "KO Calibrar"],
                required=True
            ),
            "Días Restantes": st.column_config.NumberColumn("Días Límite", format="%d d"),
            "Fecha_Instalacion": st.column_config.DateColumn("Fecha Instalación"),
            "Caducidad": st.column_config.DateColumn("Fecha Caducidad")
        },
        disabled=["Vida_Util_Meses", "Caducidad", "Días Restantes"] # Campos automáticos
    )

    # Aplicamos visualización de colores solo para referencia visual debajo
    st.divider()
    st.write("### 🚦 Vista de Prioridades")
    st.dataframe(df_editado.style.applymap(color_filas, subset=['Días Restantes']), use_container_width=True)

    if st.button("💾 SINCRONIZAR CAMBIOS", use_container_width=True):
        # Aquí enviarías los datos a Google Sheets (puedes ampliar el JSON del POST)
        st.success("Sincronizando cambios con la lógica de Gas y Estados...")
        st.balloons()
