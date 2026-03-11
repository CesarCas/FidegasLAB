import streamlit as st
import pandas as pd
import plotly.express as px
import os
from PIL import Image

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Fidegas Smart Control", layout="wide")

# --- BASE DE DATOS DE USUARIOS ---
# Aquí puedes añadir a quien quieras con su respectivo rol
USUARIOS = {
    "admin": {"password": "AdminFidegas", "rol": "Jefe de Planta"},
    "mantenimiento": {"password": "MantVitoria", "rol": "Mantenedor"},
    "prevencion": {"password": "Prev2026", "rol": "Prevención"}
}

def check_password():
    def login_form():
        with st.form("Login"):
            st.title("🛡️ Control de Acceso")
            if os.path.exists(ruta_logo):
                st.image(Image.open(ruta_logo), width=150)
            
            user = st.text_input("Usuario")
            pw = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Entrar")
            
            if submit:
                if user in USUARIOS and USUARIOS[user]["password"] == pw:
                    st.session_state["password_correct"] = True
                    st.session_state["usuario_actual"] = user
                    st.session_state["rol_actual"] = USUARIOS[user]["rol"]
                    st.rerun()
                else:
                    st.error("⚠️ Usuario o contraseña incorrectos")

    if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
        login_form()
        return False
    return True

# Rutas de archivos (definidas fuera para que el login las use si necesita el logo)
base_path = os.path.dirname(__file__)
ruta_excel = os.path.join(base_path, "inventario_completo_42_sondas.xlsx")
ruta_logo = os.path.join(base_path, "logo.png")

if check_password():
    # 2. CARGA DE DATOS
    @st.cache_data
    def cargar_datos():
        if os.path.exists(ruta_excel):
            df = pd.read_excel(ruta_excel)
            if 'Planta' in df.columns:
                df['Planta'] = pd.to_numeric(df['Planta'], errors='coerce').fillna(0).astype(int)
            return df
        return pd.DataFrame()

    df = cargar_datos()

    # 3. INTERFAZ (Ya autenticada)
    # Mostramos quién está conectado en la barra lateral
    st.sidebar.success(f"Conectado como: **{st.session_state['usuario_actual']}**")
    st.sidebar.info(f"Rol: {st.session_state['rol_actual']}")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["password_correct"] = False
        st.rerun()

    if not df.empty:
        st.title("Panel de Control de Seguridad Atmosférica")
        
        # --- LÓGICA DE PERMISOS ---
        # Si el usuario es 'prevencion', quizá no debería poder editar
        puede_editar = st.session_state["usuario_actual"] != "prevencion"

        # (Métricas y selectores iguales que antes...)
        col_f, _ = st.columns([1, 3])
        with col_f:
            meses = ["Abril 2026", "Mayo 2026", "Junio 2026", "Julio 2026"] # Simplificado para el ejemplo
            mes_sel = st.selectbox("📅 Mes de Próxima Revisión:", meses)

        st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["📊 Análisis Visual", "📋 Gestión de Mantenimiento", "📜 Inventario Total"])

        with tab1:
            st.subheader("Estado Crítico por Planta")
            # (Aquí va tu lógica de cuadrícula de gráficos que ya funciona perfecto)
            plantas = sorted(df['Planta'].unique())
            for i in range(0, len(plantas), 2):
                cols_graficos = st.columns(2)
                for j in range(2):
                    if i + j < len(plantas):
                        p_actual = plantas[i + j]
                        df_p = df[df['Planta'] == p_actual].sort_values('Num_Serie')
                        with cols_graficos[j]:
                            fig = px.bar(df_p, x='Num_Serie', y='Días Restantes', color='Días Restantes',
                                         title=f"Planta {p_actual}", color_continuous_scale='RdYlGn', 
                                         range_color=[0, 100], template='plotly_dark')
                            fig.update_layout(height=350, showlegend=False)
                            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Panel de Gestión")
            if puede_editar:
                st.info(f"Hola {st.session_state['usuario_actual']}, puedes modificar los estados aquí.")
                # (Aquí va tu st.data_editor de antes)
                edited_df = st.data_editor(df, num_rows="dynamic", key="editor_v5")
                if st.button("💾 Guardar Cambios"):
                    edited_df.to_excel(ruta_excel, index=False)
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.warning("⚠️ Tu perfil de 'Prevención' es de SOLO LECTURA. No puedes sincronizar cambios.")
                st.dataframe(df) # Mostramos tabla normal, no editable

        with tab3:
            st.subheader("Inventario Completo")
            st.dataframe(df)
