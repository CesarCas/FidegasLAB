import streamlit as st
import pandas as pd
import plotly.express as px
import os
from PIL import Image

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Fidegas Smart Control", layout="wide")

# --- USUARIOS DE PRUEBA ---
USUARIOS = {
    "admin": {"password": "123", "rol": "Jefe de Planta"},
    "mantenimiento": {"password": "456", "rol": "Mantenedor"},
}

# 2. SISTEMA DE LOGIN
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🛡️ Acceso Restringido")
        user = st.text_input("Usuario")
        pw = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if user in USUARIOS and USUARIOS[user]["password"] == pw:
                st.session_state["password_correct"] = True
                st.session_state["usuario_actual"] = user
                st.session_state["rol_actual"] = USUARIOS[user]["rol"]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
        return False
    return True

if check_password():
    # 3. CARGA DE DATOS (Ruta relativa para la nube)
  # Pega aquí el enlace que copiaste de "Compartir"
#URL_HOJA = "https://docs.google.com/spreadsheets/d/1grw6hICGLD-k4F1LFCmdLX9vaPEYTK20V9GnP6M6O_Y/edit?usp=sharing"

# Este truco transforma el enlace para que sea legible por código
#CSV_URL = URL_HOJA.split("/edit")[0] + "/export?format=csv"
# Busca el churro de letras y números entre /d/ y /edit de tu navegador
ID_HOJA = "https://docs.google.com/spreadsheets/d/1grw6hICGLD-k4F1LFCmdLX9vaPEYTK20V9GnP6M6O_Y/edit?usp=sharing" 
CSV_URL = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/export?format=csv"
@st.cache_data(ttl=10) # Se actualiza cada 10 segundos
def cargar_datos():
    try:
        # Leemos directamente de la nube de Google
        df_sheets = pd.read_csv(CSV_URL)
        if 'Planta' in df_sheets.columns:
            df_sheets['Planta'] = pd.to_numeric(df_sheets['Planta'], errors='coerce').fillna(0).astype(int)
        return df_sheets
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        # Si falla, intenta cargar el excel de reserva o devuelve vacío
        return pd.DataFrame()

# La variable 'ruta_logo' déjala igual si no la habías borrado
ruta_logo = "logo.png"
    # 4. LOGO Y CABECERA (Solo tras login)
    if os.path.exists(ruta_logo):
        st.image(Image.open(ruta_logo), width=180)

    if not df.empty:
        st.title("Panel de Control - Vitoria-Gasteiz")
        
        # --- BLOQUE DE KPIs (RESTABLECIDO) ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Sondas", len(df))
        m2.metric("En Alerta (<45d)", len(df[df['Días Restantes'] < 45]))
        m3.metric("Plantas Activas", df['Planta'].nunique())
        m4.metric("Estado General", "Operativo")

        st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["📊 Análisis Visual", "📋 Gestión", "📜 Inventario"])

        # Función para colores
        def colorear_semaforo(row):
            dias = row['Días Restantes']
            if dias < 45: return ['background-color: #ffc7ce; color: #9c0006'] * len(row)
            elif 45 <= dias <= 60: return ['background-color: #ffeb9c; color: #9c6500'] * len(row)
            else: return ['background-color: #c6efce; color: #006100'] * len(row)

        with tab1:
            st.subheader("Estado Crítico por Planta")
            plantas = sorted(df['Planta'].unique())
            for i in range(0, len(plantas), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(plantas):
                        p = plantas[i + j]
                        df_p = df[df['Planta'] == p].sort_values('Num_Serie')
                        with cols[j]:
                            fig = px.bar(df_p, x='Num_Serie', y='Días Restantes', color='Días Restantes',
                                         title=f"Planta {p}", color_continuous_scale='RdYlGn', 
                                         range_color=[0, 100], template='plotly_dark')
                            fig.update_layout(height=300, showlegend=False)
                            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Gestión de Mantenimiento")
            # --- EDITOR RESTABLECIDO CON DESPLEGABLE ---
            config_columnas = {
                "Estado_Revision": st.column_config.SelectboxColumn(
                    "Estado de Inspección",
                    options=["OK", "KO Calibración", "KO Sustitución", "Pendiente"],
                    required=True
                )
            }
            # Importante: num_rows="fixed" suele ir mejor en móvil para evitar saltos
            df_editado = st.data_editor(df, column_config=config_columnas, key="editor_vitoria")
            
            if st.button("💾 Sincronizar"):
                # Nota: En GitHub esto es solo temporal
                df_editado.to_excel(archivo_excel, index=False)
                st.cache_data.clear()
                st.success("Cambios sincronizados en memoria.")

        with tab3:
            st.subheader("Inventario Total")
            st.dataframe(df.style.apply(colorear_semaforo, axis=1), use_container_width=True)

    # Botón lateral para salir
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()


