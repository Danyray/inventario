import streamlit as st
import pandas as pd
import time
import requests  # Importante para la nueva forma de llamar a la IA
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inventario MI❤️AMOR JYI", layout="wide")

# --- FUNCIÓN PARA LLAMAR A GEMINI (MÉTODO DIRECTO) ---
def llamar_gemini_api(prompt):
    """Llamada directa vía REST para evitar el error 404 de v1beta"""
    if "GEMINI_API_KEY" not in st.secrets:
        return "Error: No se encontró la clave GEMINI_API_KEY"
    
    api_key = st.secrets["GEMINI_API_KEY"]
    # Forzamos el uso de la versión v1 (Estable)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error de Google (Código {response.status_code}): {response.text}"
    except Exception as e:
        return f"Error de conexión: {str(e)}"

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
    <style>
    button[data-baseweb="tab"] { font-size: 20px; font-weight: bold; }
    .stButton>button[key^="s_Comida"] { background-color: #FF4B4B; color: white; border-radius: 10px; }
    .st-expanderHeader { background-color: #f0f2f6; border-radius: 10px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

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
                    st.error("Usuario o clave incorrectos")
        return False
    return True

# --- LÓGICA DE LA APP ---
if login():
    st.title("📦 INVENTARIO MI❤️AMOR JYI")
    
    # --- FORMULARIO AGREGAR ---
    with st.expander("➕ AGREGAR NUEVO PRODUCTO", expanded=False):
        c1, c2 = st.columns(2)
        mod = c1.selectbox("¿A qué lista pertenece?", ["Comida", "Hogar", "Por Comprar"])
        nom = c1.text_input("Nombre del Producto")
        pre = c2.number_input("Precio Unitario ($)", min_value=0.0, step=0.1)
        can = c2.number_input("Cantidad Actual", min_value=1, step=1)

        if st.button("🚀 GUARDAR EN LA NUBE", use_container_width=True):
            if nom:
                n_cap = nom.strip().capitalize()
                supabase.table("productos").insert({
                    "modulo": mod, "nombre": n_cap, "precio": pre, 
                    "cantidad": can, "created_at": datetime.now().isoformat()
                }).execute()
                st.toast(f"¡{n_cap} guardado!")
                time.sleep(1)
                st.rerun()

    # --- PESTAÑAS ---
    response = supabase.table("productos").select("*").order("id").execute()
    df_all = pd.DataFrame(response.data if response.data else [])

    tabs = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])
    nombres_tabs = ["Comida", "Hogar", "Por Comprar"]

    for i, tab in enumerate(tabs):
        m_name = nombres_tabs[i]
        with tab:
            df = df_all[df_all['modulo'] == m_name].copy() if not df_all.empty else pd.DataFrame()
            if not df.empty:
                df['fecha_f'] = pd.to_datetime(df['created_at']).dt.strftime('%d/%m %H:%M')
                cfg = {"id": st.column_config.NumberColumn("🆔", disabled=True)}
                edit_df = st.data_editor(df[["id", "nombre", "precio", "cantidad", "fecha_f"]], column_config=cfg, use_container_width=True, hide_index=True, key=f"ed_{m_name}")

                if st.button(f"💾 Guardar {m_name}", key=f"s_{m_name}"):
                    for _, row in edit_df.iterrows():
                        supabase.table("productos").update({"precio": row['precio'], "cantidad": row['cantidad']}).eq("id", row['id']).execute()
                    st.rerun()
            else:
                st.info("Lista vacía.")

    # --- SECCIÓN: CHEF IA (ESTABLE) ---
    st.divider()
    st.subheader("👨‍🍳 Chef IA")
    with st.expander("Sugerencias de recetas", expanded=True):
        if not df_all.empty:
            df_comida = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]
            ingredientes = df_comida['nombre'].tolist()
            if ingredientes:
                st.write(f"**Tienes:** {', '.join(ingredientes)}")
                if st.button("🪄 Generar Recetas Ahora", use_container_width=True):
                    with st.spinner("Conectando con el Chef..."):
                        prompt = f"Actúa como chef. Tengo: {', '.join(ingredientes)}. Dame 3 recetas rápidas con pasos cortos."
                        resultado = llamar_gemini_api(prompt)
                        st.markdown(resultado)
            else:
                st.warning("No hay comida en el inventario.")
