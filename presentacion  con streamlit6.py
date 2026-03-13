import streamlit as st
import pandas as pd
import plotly.express as px
import os
import requests

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Control de  Sondas de Gases", layout="wide")

# --- RELLENA ESTOS DOS DATOS ---
ID_HOJA = "1grw6hICGLD-k4F1LFCmdLX9vaPEYTK20V9GnP6M6O_Y"
URL_API_GOOGLE = "https://script.google.com/macros/s/AKfycbxwIdQN5QKtpzkWC8KWk26gU4cNlZzcwUywQBjNfbtcKJhgtnCBWp3TwE94uNz6wIQgqg/exec"


# --- USUARIOS ---
USUARIOS = {"admin": "123", "mantenimiento": "456"}

# 2. SISTEMA DE LOGIN
if "autenticado" not in st.session_state:
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

# 3. CARGA DE DATOS (LECTURA)
CSV_URL = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/export?format=csv"

@st.cache_data(ttl=5)
def cargar_datos():
    try:
        df_sheets = pd.read_csv(CSV_URL)
        if 'Planta' in df_sheets.columns:
            df_sheets['Planta'] = pd.to_numeric(df_sheets['Planta'], errors='coerce').fillna(0).astype(int)
        return df_sheets
    except:
        return pd.DataFrame()

df = cargar_datos()
st.write("Columnas detectadas:", df.columns.tolist())
st.write("¿Está vacío el archivo?:", df.empty)
# 4. INTERFAZ DE LA APP
if os.path.exists("logo.png"):
    st.image("logo.png", width=120)

if not df.empty:
    st.title("Panel de Control - Fidegas")
    
    tab1, tab2 = st.tabs(["📊 Visualización", "🛠️ Gestión y Guardado"])

    with tab1:
        fig = px.bar(df, x='Num_Serie', y='Días Restantes', color='Días Restantes',
                     color_continuous_scale='RdYlGn', title="Estado de Sondas")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Edición de Datos")
        # Aquí permitimos editar la tabla
        df_editado = st.data_editor(df, use_container_width=True, key="editor_vitoria")
        
        st.divider()
        
        # BOTÓN MÁGICO PARA GUARDAR
        if st.button("💾 GUARDAR CAMBIOS EN GOOGLE SHEETS"):
            try:
                # Tomamos la primera fila como prueba
                sonda_id = str(df_editado.iloc[0]['Num_Serie'])
                nuevo_status = str(df_editado.iloc[0]['Estado_Revision'])
                
                datos_para_google = {"num_serie": sonda_id, "nuevo_estado": nuevo_status}
                
                # Enviamos el dato a Google
                res = requests.post(URL_API_GOOGLE, json=datos_para_google)
                
                if res.text == "OK":
                    st.success(f"¡Sonda {sonda_id} actualizada en la nube!")
                    st.balloons()
                else:
                    st.error(f"Google dice: {res.text}")
            except Exception as e:
                st.error(f"Error técnico: {e}")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state.clear()
    st.rerun()

