import streamlit as st
import pandas as pd
import plotly.express as px
import os
import smtplib
from email.mime.text import MIMEText
from PIL import Image

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Fidegas Smart Control", layout="wide")

# --- DATOS DE CONFIGURACIÓN (RELLENA ESTO) ---
ID_HOJA = "TU_ID_DE_GOOGLE_SHEETS_AQUI" # El código largo de la URL
MI_CORREO = "tu_usuario@gmail.com"
PASSWORD_APP = "abcd efgh ijkl mnop" # Las 16 letras de Google
DESTINATARIO = "correo_donde_recibes_avisos@ejemplo.com"

# --- USUARIOS DE PRUEBA ---
USUARIOS = {
    "admin": {"password": "123", "rol": "Jefe de Planta"},
    "mantenimiento": {"password": "456", "rol": "Mantenedor"},
}

# 2. FUNCIÓN DE CORREO
def enviar_correo_aviso(detalles):
    msg = MIMEText(f"Alerta de Mantenimiento Fidegas:\n\n{detalles}")
    msg['Subject'] = "⚠️ Alerta Sonda - Revisión Requerida"
    msg['From'] = MI_CORREO
    msg['To'] = DESTINATARIO
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(MI_CORREO, PASSWORD_APP)
        server.sendmail(MI_CORREO, DESTINATARIO, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error de envío: {e}")
        return False

# 3. SISTEMA DE LOGIN
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🛡️ Acceso Fidegas PoC")
        user = st.text_input("Usuario")
        pw = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if user in USUARIOS and USUARIOS[user]["password"] == pw:
                st.session_state["password_correct"] = True
                st.session_state["usuario_actual"] = user
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
        return False
    return True

if check_password():
    # 4. CARGA DE DATOS DESDE GOOGLE SHEETS
    CSV_URL = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/export?format=csv"
    
    @st.cache_data(ttl=10)
    def cargar_datos():
        try:
            df_sheets = pd.read_csv(CSV_URL)
            if 'Planta' in df_sheets.columns:
                df_sheets['Planta'] = pd.to_numeric(df_sheets['Planta'], errors='coerce').fillna(0).astype(int)
            return df_sheets
        except:
            return pd.DataFrame()

    df = cargar_datos()
    
    # 5. INTERFAZ PRINCIPAL
    if os.path.exists("logo.png"):
        st.image("logo.png", width=150)

    if not df.empty:
        st.title(f"Panel de {st.session_state['usuario_actual']}")
        
        # KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Sondas Totales", len(df))
        c2.metric("Críticas (<45d)", len(df[df['Días Restantes'] < 45]))
        c3.success("Conectado a Google Sheets ✅")

        tab1, tab2 = st.tabs(["📊 Gráficos", "🛠️ Mantenimiento"])

        with tab1:
            fig = px.bar(df, x='Num_Serie', y='Días Restantes', color='Días Restantes',
                         color_continuous_scale='RdYlGn', title="Estado de Sondas")
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Gestión de Sondas")
            config = {
                "Estado_Revision": st.column_config.SelectboxColumn(
                    "Estado", options=["OK", "KO Sustitución", "Pendiente"]
                )
            }
            df_editado = st.data_editor(df, column_config=config, key="editor_vitoria")
            
            # Botón de correo
            if st.button("📧 Enviar Alerta de esta Sonda"):
                # Cogemos la primera fila editada como ejemplo para la prueba
                datos_aviso = f"Sonda: {df_editado.iloc[0]['Num_Serie']} - Estado: {df_editado.iloc[0]['Estado_Revision']}"
                if enviar_correo_aviso(datos_aviso):
                    st.balloons()
                    st.success("¡Correo enviado a central!")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()
