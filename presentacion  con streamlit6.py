import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Fidegas Smart Control", layout="wide")

ID_HOJA = "1grw6hICGLD-k4F1LFCmdLX9vaPEYTK20V9GnP6M6O_Y"
# ¡ASEGÚRATE DE QUE ESTA URL ES LA CORRECTA!
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

# 3. LÓGICA DE NEGOCIO Y CARGA
MAPA_VIDA_UTIL = {"O2": 24, "CO": 24, "H2": 48, "NH3": 24, "H2S": 24}

@st.cache_data(ttl=2)
def cargar_datos():
    url = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/export?format=csv"
    try:
        df = pd.read_csv(url)
        hoy = datetime.now()
        df['Fecha_Instalacion'] = pd.to_datetime(df['Fecha_Instalacion'].astype(str).str.replace('#', ''), errors='coerce')
        df['Vida_Util_Meses'] = df['Tipo_Gas'].map(MAPA_VIDA_UTIL).fillna(24)
        df['Caducidad'] = df.apply(
            lambda x: x['Fecha_Instalacion'] + timedelta(days=int(x['Vida_Util_Meses'] * 30.44)) 
            if pd.notnull(x['Fecha_Instalacion']) else pd.NaT, axis=1
        )
        df['Días Restantes'] = (df['Caducidad'] - hoy).dt.days.fillna(0).astype(int)
        return df
    except:
        return pd.DataFrame()

df_original = cargar_datos()

# 4. FUNCIÓN DE COLOR
def style_semaforo(row):
    dias = row['Días Restantes']
    color = 'background-color: #28a745; color: white' # Verde
    if dias < 45: color = 'background-color: #ff4b4b; color: white' # Rojo
    elif dias <= 100: color = 'background-color: #ffa500; color: black' # Naranja
    return [color] * len(row)

# 5. INTERFAZ
st.title("🚀 Gestión de Sondas Laboratorios")

if not df_original.empty:
    tab1, tab2 = st.tabs(["📊 Análisis Visual", "🛠️ Editor de Campo"])

    with tab1:
        fig = px.bar(df_original, x='Num_Serie', y='Días Restantes', color='Días Restantes',
                     color_continuous_scale=['red', 'orange', 'green'])
        st.plotly_chart(fig, use_container_width=True)
        st.write("### Vista de Prioridades")
        st.dataframe(df_original.style.apply(style_semaforo, axis=1), use_container_width=True)

    with tab2:
        st.subheader("Modificar Datos")
        # Mostramos el editor y guardamos el resultado
        df_editado = st.data_editor(
            df_original,
            use_container_width=True,
            column_config={
                "Tipo_Gas": st.column_config.SelectboxColumn("Gas", options=["O2", "CO", "H2", "NH3", "H2S"]),
                "Estado_Revision": st.column_config.SelectboxColumn("Estado", options=["OK", "KO", "KO Calibrar"]),
                "Fecha_Instalacion": st.column_config.DateColumn("Instalación")
            },
            key="editor_vitoria_v6"
        )

        if st.button("💾 SINCRONIZAR CAMBIOS", use_container_width=True):
            if "script.google.com" not in URL_API_GOOGLE:
                st.error("Falta la URL del Apps Script.")
            else:
                cambios_enviados = 0
                with st.spinner('Actualizando Google Sheets...'):
                    for i in range(len(df_original)):
                        # Detectamos si ha cambiado el Estado o el Gas
                        if (str(df_original.iloc[i]['Estado_Revision']) != str(df_editado.iloc[i]['Estado_Revision'])) or \
                           (str(df_original.iloc[i]['Tipo_Gas']) != str(df_editado.iloc[i]['Tipo_Gas'])):
                            
                            payload = {
                                "num_serie": str(df_editado.iloc[i]['Num_Serie']),
                                "nuevo_estado": str(df_editado.iloc[i]['Estado_Revision']),
                                "nuevo_gas": str(df_editado.iloc[i]['Tipo_Gas']) # Añadimos el gas por si lo cambias
                            }
                            
                            try:
                                res = requests.post(URL_API_GOOGLE, json=payload, timeout=10)
                                if res.text == "OK":
                                    cambios_enviados += 1
                            except Exception as e:
                                st.error(f"Error en sonda {payload['num_serie']}: {e}")

                if cambios_enviados > 0:
                    st.success(f"✅ ¡{cambios_enviados} cambios guardados en el Excel!")
                    st.balloons()
                    st.cache_data.clear() # Limpiamos caché para ver los cambios
                else:
                    st.info("No se detectaron cambios pendientes.")
else:
    st.info("Conectando con la base de datos de Vitoria...")
