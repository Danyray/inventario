import streamlit as st
import pandas as pd
import time
import requests
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inventario MI❤️AMOR JYI", layout="wide")

# --- FUNCIÓN PARA LLAMAR A LA IA (MODELO PRO COMPATIBLE) ---
def llamar_gemini_api(prompt):
    if "GEMINI_API_KEY" not in st.secrets:
        return "Error: No se encontró la clave API."
    
    api_key = st.secrets["GEMINI_API_KEY"]
    
    # Cambiamos a 'gemini-pro', que es el modelo con mayor disponibilidad global
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        res_json = response.json()
        
        if response.status_code == 200:
            # Estructura de respuesta estándar de Gemini
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            # Si gemini-pro también falla, intentamos la última ruta posible
            return f"Error técnico (Código {response.status_code}). El servidor de Google no reconoce el modelo en esta región."
    except Exception as e:
        return f"Error de conexión: {str(e)}"

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def conectar_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = conectar_supabase()

# --- SISTEMA DE AUTENTICACIÓN ---
def login():
    if "auth" not in st.session_state:
        st.session_state.auth = False
    if not st.session_state.auth:
        st.title("🔐 Acceso al Sistema")
        validos = {"ignacio": "yosa0325", "joseilys": "yosa0325"}
        with st.form("login_form"):
            u = st.text_input("Usuario").lower().strip()
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                if u in validos and validos[u] == p:
                    st.session_state.auth = True
                    st.session_state.user = u.capitalize()
                    st.rerun()
                else:
                    st.error("Acceso denegado")
        return False
    return True

# --- LÓGICA PRINCIPAL ---
if login():
    st.title("📦 INVENTARIO MI❤️AMOR JYI")
    
    # Recuperar datos de Supabase
    try:
        response = supabase.table("productos").select("*").order("id").execute()
        df_all = pd.DataFrame(response.data if response.data else [])
    except:
        df_all = pd.DataFrame()

    # Pestañas de Inventario
    tabs = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])
    for i, tab in enumerate(tabs):
        nombres = ["Comida", "Hogar", "Por Comprar"]
        m_name = nombres[i]
        with tab:
            df = df_all[df_all['modulo'] == m_name] if not df_all.empty else pd.DataFrame()
            if not df.empty:
                st.dataframe(df[["nombre", "precio", "cantidad"]], use_container_width=True)
            else:
                st.info("No hay productos.")

    # --- SECCIÓN CHEF IA ---
    st.divider()
    st.subheader("👨‍🍳 Chef IA (Modo Compatible)")
    
    if not df_all.empty:
        df_comida = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]
        ingredientes = df_comida['nombre'].tolist()
        
        if ingredientes:
            st.write(f"**Ingredientes:** {', '.join(ingredientes)}")
            if st.button("🪄 Generar Recetas", use_container_width=True):
                with st.spinner("Cocinando ideas con Gemini Pro..."):
                    prompt = f"Soy un chef. Tengo: {', '.join(ingredientes)}. Dame 3 recetas cortas y deliciosas."
                    resultado = llamar_gemini_api(prompt)
                    st.markdown(resultado)
        else:
            st.warning("Añade alimentos a la sección COMIDA para usar el Chef.")
