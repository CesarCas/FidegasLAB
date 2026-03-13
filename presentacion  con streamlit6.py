import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# 1. CONFIGURACIÓN Y DATOS
st.set_page_config(page_title="Fidegas Smart Control", layout="wide")

ID_HOJA = "1grw6hICGLD-k4F1LFCmdLX9vaPEYTK20V9GnP6M6O_Y"
# REEMPLAZA ESTO CON TU URL /exec
URL_API_GOOGLE = "TU_URL_DE_APPS_SCRIPT_AQUÍ" 

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
        else:
            st.error("Credenciales incorrectas")
    st.stop()

# 3. CARGA Y PROCESADO DE DATOS (CON CORRECCIÓN DE FECHAS)
@st.cache_data(ttl=2)
def cargar_datos():
    url = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/export?format=csv"
    try:
        df = pd.read_csv(url)
        
        # --- ARREGLO DE FECHAS ---
        # Convertimos las columnas de fecha a texto legible (YYYY-MM-DD) para evitar los #
        columnas_fecha = ['Fecha_Instalacion', 'Ultima_Revision', 'Caducidad']
        for col in columnas_fecha:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # Limpieza de días restantes para los gráficos
        if 'Días Restantes' in df.columns:
            df['Días Restantes'] = pd.to_numeric(df['Días Restantes'], errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

df = cargar_datos()

# 4. INTERFAZ VISUAL
st.sidebar.title("Fidegas Control")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state["autenticado"] = False
    st.rerun()

st.title("🚀 Dashboard de Sondas - Fidegas")

if not df.empty:
    tab1, tab2 = st.tabs(["📊 Análisis Visual", "🛠️ Gestión y Sincronización"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Días hasta Revisión")
            fig_bar = px.bar(df, x='Num_Serie', y='Días Restantes', color='Días Restantes',
                             color_continuous_scale='RdYlGn', title="Urgencia por Sonda")
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            st.subheader("Mapa de Riesgo")
            fig_heat = px.density_heatmap(df, x="Planta", y="Tipo_Gas", z="Días Restantes",
                                          color_continuous_scale='Viridis', title="Concentración por Ubicación")
            st.plotly_chart(fig_heat, use_container_width=True)

    with tab2:
        st.subheader("Edición de Datos en Tiempo Real")
        # Editor con configuración de ancho de columnas para las fechas
        df_editado = st.data_editor(
            df, 
            use_container_width=True, 
            key="editor_vitoria",
            column_config={
                "Fecha_Instalacion": st.column_config.Column(width="medium"),
                "Ultima_Revision": st.column_config.Column(width="medium"),
                "Caducidad": st.column_config.Column(width="medium")
            }
        )
        
        st.divider()
        
        if st.button("💾 SINCRONIZAR TODOS LOS CAMBIOS", use_container_width=True):
            if "script.google.com" not in URL_API_GOOGLE:
                st.error("❌ URL de Google Apps Script no configurada o inválida.")
            else:
                cambios_detectados = 0
                for i in range(len(df)):
                    # Solo enviamos si el estado ha cambiado
                    if str(df.iloc[i]['Estado_Revision']) != str(df_editado.iloc[i]['Estado_Revision']):
                        sonda_id = str(df_editado.iloc[i]['Num_Serie'])
                        nuevo_status = str(df_editado.iloc[i]['Estado_Revision'])
                        
                        try:
                            # Timeout para que no se cuelgue si falla la red
                            requests.post(URL_API_GOOGLE, json={"num_serie": sonda_id, "nuevo_estado": nuevo_status}, timeout=10)
                            cambios_detectados += 1
                        except Exception as e:
                            st.error(f"Error al enviar sonda {sonda_id}: {e}")
                
                if cambios_detectados > 0:
                    st.success(f"✅ ¡{cambios_detectados} cambios sincronizados!")
                    st.balloons()
                    st.cache_data.clear()
                else:
                    st.info("No se detectaron cambios en la columna 'Estado_Revision'.")
else:
    st.warning("La hoja está vacía o no se ha podido leer.")
