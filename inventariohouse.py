import streamlit as st
import pandas as pd
import time
import requests
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inventario MI❤️AMOR JYI", layout="wide")

# --- FUNCIÓN PARA LA IA DEL CHEF (INTELIGENTE Y FORMATEADA) ---
def llamar_ia_chef(ingredientes_lista):
    if "HUGGINGFACE_TOKEN" not in st.secrets:
        return "⚠️ Configura el Token en Secrets."

    # Filtramos condimentos para que la IA y el respaldo no digan locuras
    condimentos = ["Azucar", "Sal", "Aceite", "Mayonesa", "Mavesa", "Vinagre", "Salsa", "Pimienta"]
    ing_reales = [i for i in ingredientes_lista if not any(c.lower() in i.lower() for c in condimentos)]
    
    # Si después de filtrar no queda nada sólido, usamos un genérico
    base_ing = ing_reales if ing_reales else ingredientes_lista
    
    url = "https://api-inference.huggingface.co/models/google/flan-t5-large"
    token = st.secrets["HUGGINGFACE_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}
    
    prompt = f"Ingredients: {', '.join(base_ing)}. Suggest 3 realistic food recipes."
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            res_json = response.json()
            texto = res_json[0].get('generated_text', '').replace('.', '').split(',')
            
            res_final = "### 👨‍🍳 Menú Recomendado\n"
            for p in texto:
                if p.strip():
                    res_final += f"* ✅ **{p.strip().capitalize()}**\n"
            return res_final
    except:
        pass

    # --- RESPALDO INTELIGENTE (No más ensaladas de azúcar) ---
    plato_principal = base_ing[0] if base_ing else "lo disponible"
    return f"""
    ### 👨‍🍳 Sugerencia del Chef (Modo Seguro)
    * ✅ **Especial de la casa con {plato_principal}**
    * ✅ **Combinado rápido JYI**
    * ✅ **Bowl creativo con ingredientes de la despensa**
    """

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
    <style>
    button[data-baseweb="tab"] { font-size: 20px; font-weight: bold; }
    .stButton>button[key^="s_Comida"] { background-color: #FF4B4B; color: white; border-radius: 10px; }
    .stButton>button[key^="s_Hogar"] { background-color: #0083B8; color: white; border-radius: 10px; }
    .stButton>button[key^="s_PorComprar"] { background-color: #28a745; color: white; border-radius: 10px; }
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
                else: st.error("Acceso denegado")
        return False
    return True

# --- LÓGICA PRINCIPAL ---
if login():
    st.title("📦 INVENTARIO MI❤️AMOR JYI")
    
    # Obtener datos
    res = supabase.table("productos").select("*").order("id").execute()
    df_all = pd.DataFrame(res.data if res.data else [])

    # Pestañas
    t1, t2, t3 = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])
    listas = ["Comida", "Hogar", "Por Comprar"]
    
    for i, tab in enumerate([t1, t2, t3]):
        m_name = listas[i]
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
            else: st.info("Vacío")

    # --- CHEF IA ---
    st.divider()
    st.subheader("👨‍🍳 Chef IA")
    if not df_all.empty:
        comida = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]
        ing = comida['nombre'].tolist()
        if ing:
            if st.button("🪄 Generar Menú del Día", use_container_width=True):
                with st.spinner("Cocinando..."):
                    st.markdown(llamar_ia_chef(ing))
