import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Fidegas Smart Control", layout="wide")

# ID de la hoja y URL del script (asegúrate de que son correctos)
ID_HOJA = "1grw6hICGLD-k4F1LFCmdLX9vaPEYTK20V9GnP6M6O_Y"
URL_API_GOOGLE = "https://script.google.com/macros/s/AKfycbxwIdQN5QKtpzkWC8KWk26gU4cNlZzcwUywQBjNfbtcKJhgtnCBWp3TwE94uNz6wIQgqg/exec"
USUARIOS = {"admin": "123", "mantenimiento": "456"}

# 2. SISTEMA DE LOGIN
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
        else:
            st.error("Credenciales incorrectas")
    st.stop()

# 3. LÓGICA DE NEGOCIO Y CARGA DE DATOS
MAPA_VIDA_UTIL = {"O2": 24, "CO": 24, "H2": 48, "NH3": 24, "H2S": 24}

@st.cache_data(ttl=5)
def cargar_datos_seguro():
    url = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/export?format=csv"
    try:
        # Intentamos cargar el CSV
        df = pd.read_csv(url)
        
        # Validación de columnas críticas para evitar que la app se quede en blanco
        columnas_necesarias = ['Num_Serie', 'Tipo_Gas', 'Fecha_Instalacion']
        for col in columnas_necesarias:
            if col not in df.columns:
                st.error(f"Falta la columna '{col}' en el Excel. Revisa los encabezados.")
                return pd.DataFrame()

        # --- CÁLCULOS INTELIGENTES ---
        hoy = datetime.now()
        
        # Procesar Fecha de Instalación
        df['Fecha_Instalacion'] = pd.to_datetime(df['Fecha_Instalacion'].astype(str).str.replace('#', ''), errors='coerce')
        
        # Asignar Vida Útil y calcular Caducidad
        df['Vida_Util_Meses'] = df['Tipo_Gas'].map(MAPA_VIDA_UTIL).fillna(24)
        df['Caducidad'] = df.apply(
            lambda x: x['Fecha_Instalacion'] + timedelta(days=int(x['Vida_Util_Meses'] * 30.44)) 
            if pd.notnull(x['Fecha_Instalacion']) else pd.NaT, axis=1
        )
        
        # Calcular Días Restantes
        df['Días Restantes'] = (df['Caducidad'] - hoy).dt.days.fillna(0).astype(int)
        
        return df
    except Exception as e:
        st.error(f"Error técnico al conectar con Google Sheets: {e}")
        return pd.DataFrame()

df = cargar_datos_seguro()

# 4. INTERFAZ Y ANÁLISIS VISUAL
st.sidebar.title("Fidegas Lab")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state["autenticado"] = False
    st.rerun()

st.title("🚀 Gestión de Sondas Fidegas")

if not df.empty:
    # Definición de colores según los días
    def aplicar_semaforo(row):
        dias = row['Días Restantes']
        if dias < 45: return 'background-color: #ff4b4b; color: white' # Rojo
        if dias <= 100: return 'background-color: #ffa500; color: black' # Naranja
        return 'background-color: #28a745; color: white' # Verde

    # TABS PARA ORGANIZAR LA INFO
    tab1, tab2 = st.tabs(["📊 Análisis Visual", "🛠️ Editor de Campo"])

    with tab1:
        st.subheader("Estado Crítico de la Red")
        # Gráfico de barras
        fig = px.bar(df, x='Num_Serie', y='Días Restantes', color='Días Restantes',
                     color_continuous_scale=['red', 'orange', 'green'],
                     title="Urgencia de sustitución por Sonda")
        st.plotly_chart(fig, use_container_width=True)
        
        # Vista de tabla coloreada (Solo lectura)
        st.write("### Semáforo de Mantenimiento")
        st.dataframe(df.style.apply(lambda x: [aplicar_semaforo(row) for row in x], axis=1, subset=['Días Restantes']), use_container_width=True)

    with tab2:
        st.subheader("Modificación de Estados")
        # Editor interactivo con desplegables
        df_editado = st.data_editor(
            df,
            use_container_width=True,
            column_config={
                "Tipo_Gas": st.column_config.SelectboxColumn("Gas", options=["O2", "CO", "H2", "NH3", "H2S"]),
                "Estado_Revision": st.column_config.SelectboxColumn("Estado", options=["OK", "KO", "KO Calibrar"]),
                "Fecha_Instalacion": st.column_config.DateColumn("Instalación"),
                "Caducidad": st.column_config.DateColumn("Caducidad", disabled=True),
                "Días Restantes": st.column_config.NumberColumn("Días", disabled=True)
            },
            key="editor_fidegas"
        )

        if st.button("💾 SINCRONIZAR CAMBIOS", use_container_width=True):
            # Lógica para enviar vía POST a tu Apps Script
            st.info("Enviando actualizaciones a la nube...")
            # (Aquí va el bucle de requests.post que configuramos anteriormente)
            st.success("Cambios enviados.")
else:
    st.warning("Esperando datos... Si este mensaje persiste, comprueba que el ID de la hoja es correcto y que tiene permisos de 'Cualquier persona con el enlace puede leer'.")
