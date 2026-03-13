import streamlit as st
import pandas as pd
import requests

# 1. CONFIGURACIÓN Y CREDENCIALES
st.set_page_config(page_title="Fidegas Smart Control", layout="wide")

ID_HOJA = "1grw6hICGLD-k4F1LFCmdLX9vaPEYTK20V9GnP6M6O_Y"
URL_API_GOOGLE = "https://script.google.com/macros/s/AKfycbxwIdQN5QKtpzkWC8KWk26gU4cNlZzcwUywQBjNfbtcKJhgtnCBWp3TwE94uNz6wIQgqg/exec" # <--- No olvides poner tu URL /exec aquí

USUARIOS = {
    "admin": "123",
    "mantenimiento": "456"
}

# 2. LÓGICA DE SESIÓN Y LOGIN
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

def login():
    st.title("🛡️ Acceso Fidegas PoC")
    usuario = st.text_input("Usuario")
    clave = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if usuario in USUARIOS and USUARIOS[usuario] == clave:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

if not st.session_state["autenticado"]:
    login()
    st.stop()

# 3. CARGA DE DATOS (LECTURA)
@st.cache_data(ttl=2)
def cargar_datos():
    url_csv = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/export?format=csv"
    try:
        return pd.read_csv(url_csv)
    except:
        return pd.DataFrame()

df = cargar_datos()

# 4. INTERFAZ DE USUARIO (DASHBOARD)
st.sidebar.title(f"Bienvenido")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state["autenticado"] = False
    st.rerun()

st.title("🚀 Fidegas Smart Control")

if not df.empty:
    st.subheader("🛠️ Gestión de Mantenimiento")
    st.write("Modifica los datos y pulsa el botón de abajo para sincronizar.")
    
    # Tabla editable
    df_editado = st.data_editor(df, use_container_width=True, key="editor_vitoria")
    
    st.divider()
    
    # BOTÓN DE GUARDADO
    if st.button("💾 GUARDAR CAMBIOS EN GOOGLE SHEETS", use_container_width=True):
        try:
            # Extraemos Num_Serie y Estado_Revision de la primera fila
            sonda_id = str(df_editado.iloc[0]['Num_Serie'])
            nuevo_status = str(df_editado.iloc[0]['Estado_Revision'])
            
            payload = {
                "num_serie": sonda_id,
                "nuevo_estado": nuevo_status
            }
            
            with st.spinner('Enviando datos a la nube...'):
                response = requests.post(URL_API_GOOGLE, json=payload)
                
                if response.text == "OK":
                    st.success(f"✅ ¡Sonda {sonda_id} actualizada!")
                    st.balloons()
                else:
                    st.error(f"Error de Google: {response.text}")
        except Exception as e:
            st.error(f"Error en la conexión: {e}")
else:
    st.warning("No se pudieron cargar los datos. Verifica la conexión con la hoja.")
