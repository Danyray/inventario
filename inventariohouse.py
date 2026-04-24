import streamlit as st
import pandas as pd
import time
import requests
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inventario MI❤️AMOR JYI", layout="wide")

# --- FUNCIÓN PARA LA IA (MODELO LIBRE DE BLOQUEOS) ---
def llamar_ia_chef(prompt):
    # Usaremos un modelo de Mistral AI que es gratuito y no tiene bloqueo regional
    # No necesitas API Key para esta prueba rápida, pero lo ideal es registrar una en Mistral.ai
    url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
    
    # Si quieres usar tu clave de Hugging Face, ponla en secrets. Si no, usa esta pública temporal:
    headers = {"Authorization": "Bearer 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"} # Ejemplo
    
    payload = {"inputs": f"<s>[INST] {prompt} [/INST]"}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            resultado = response.json()[0]['generated_text']
            return resultado.split("[/INST]")[-1] # Limpiamos la respuesta
        else:
            return "El Chef IA está tomando un descanso (Servidor saturado). Intenta en 10 segundos."
    except:
        return "Error de conexión con el Chef."

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def conectar_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = conectar_supabase()

# --- AUTENTICACIÓN ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Acceso al Sistema")
    with st.form("login"):
        u = st.text_input("Usuario").lower().strip()
        p = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            if (u == "ignacio" or u == "joseilys") and p == "yosa0325":
                st.session_state.auth = True
                st.session_state.user = u.capitalize()
                st.rerun()
            else: st.error("Clave incorrecta")
else:
    st.title(f"📦 INVENTARIO - {st.session_state.user}")
    
    # Cargar datos
    res = supabase.table("productos").select("*").order("id").execute()
    df_all = pd.DataFrame(res.data if res.data else [])

    # Pestañas
    tab1, tab2, tab3 = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 COMPRAS"])
    listas = ["Comida", "Hogar", "Por Comprar"]
    for i, t in enumerate([tab1, tab2, tab3]):
        with t:
            df = df_all[df_all['modulo'] == listas[i]] if not df_all.empty else pd.DataFrame()
            st.dataframe(df, use_container_width=True)

    # --- CHEF IA ---
    st.divider()
    st.subheader("👨‍🍳 Chef IA (Sin bloqueos regionales)")
    
    if not df_all.empty:
        comida = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]
        ing = comida['nombre'].tolist()
        if ing:
            st.write(f"**Ingredientes:** {', '.join(ing)}")
            if st.button("🪄 ¡Chef, dame ideas!", use_container_width=True):
                with st.spinner("Pensando recetas para ti..."):
                    p = f"Tengo {', '.join(ing)}. Dime 3 nombres de platos rápidos que puedo cocinar."
                    st.markdown(llamar_ia_chef(p))
