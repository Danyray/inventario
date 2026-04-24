import streamlit as st
import pandas as pd
import time
import requests
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inventario MI❤️AMOR JYI", layout="wide")

# --- FUNCIÓN PARA LA IA DEL CHEF (CON LÓGICA DE RECETAS REALES) ---
def llamar_ia_chef(ingredientes_lista):
    if "HUGGINGFACE_TOKEN" not in st.secrets:
        return "⚠️ Configura el Token en Secrets."

    # Filtramos para que la IA se enfoque en lo importante
    condimentos = ["Azucar", "Sal", "Aceite", "Mayonesa", "Mavesa", "Vinagre", "Salsa"]
    ing_reales = [i for i in ingredientes_lista if not any(c.lower() in i.lower() for c in condimentos)]
    base = ing_reales if ing_reales else ingredientes_lista

    url = "https://api-inference.huggingface.co/models/google/flan-t5-large"
    token = st.secrets["HUGGINGFACE_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Prompt más específico para que no dé respuestas vacías
        prompt = f"Recipes with {', '.join(base[:5])}. Give 3 specific meal names."
        response = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=10)
        
        if response.status_code == 200:
            res_json = response.json()
            texto = res_json[0].get('generated_text', '').replace('.', '').split(',')
            if len(texto) > 1:
                res_final = "### 👨‍🍳 Menú del Día\n"
                for p in texto:
                    if p.strip():
                        res_final += f"* ✅ **{p.strip().capitalize()}**\n"
                return res_final
    except:
        pass

    # --- RESPALDO CON LÓGICA DE COCINA REAL (FALLBACK) ---
    # Si la IA falla, armamos platos que sí tienen sentido
    p = base[0] if base else "Ingredientes varios"
    return f"""
    ### 👨‍🍳 Ideas de Cocina (Sugerencias Reales)
    * ✅ **Arepas rellenas** (usando tu {p})
    * ✅ **Salteado criollo** con los vegetales y {p}
    * ✅ **Bowl mixto JYI** (base de arroz/pasta con {p})
    """

# --- ESTILOS ---
st.markdown("""<style>
    button[data-baseweb="tab"] { font-size: 20px; font-weight: bold; }
    .stButton>button { border-radius: 10px; }
    </style>""", unsafe_allow_html=True)

# --- CONEXIÓN SUPABASE ---
@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar_supabase()

# --- LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔐 Acceso al Sistema")
    with st.form("login"):
        u = st.text_input("Usuario").lower().strip()
        p = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            if u in ["ignacio", "joseilys"] and p == "yosa0325":
                st.session_state.auth = True
                st.session_state.user = u.capitalize()
                st.rerun()
            else: st.error("Clave incorrecta")
    st.stop()

# --- APP PRINCIPAL ---
st.title("📦 INVENTARIO MI❤️AMOR JYI")

# 1. FORMULARIO PARA AGREGAR (Devuelto a su lugar)
with st.expander("➕ AGREGAR NUEVO PRODUCTO", expanded=False):
    c1, c2 = st.columns(2)
    mod_n = c1.selectbox("Lista", ["Comida", "Hogar", "Por Comprar"])
    nom_n = c1.text_input("Nombre")
    pre_n = c2.number_input("Precio $", min_value=0.0, step=0.1)
    can_n = c2.number_input("Cantidad", min_value=1, step=1)
    if st.button("🚀 GUARDAR PRODUCTO", use_container_width=True):
        if nom_n:
            supabase.table("productos").insert({
                "modulo": mod_n, "nombre": nom_n.capitalize(), 
                "precio": pre_n, "cantidad": can_n, "created_at": datetime.now().isoformat()
            }).execute()
            st.success("¡Guardado!")
            time.sleep(1)
            st.rerun()

# 2. PESTAÑAS DE INVENTARIO
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

tabs = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])
listas = ["Comida", "Hogar", "Por Comprar"]

for i, tab in enumerate(tabs):
    m_name = listas[i]
    with tab:
        df = df_all[df_all['modulo'] == m_name].copy() if not df_all.empty else pd.DataFrame()
        if not df.empty:
            df['fecha_f'] = pd.to_datetime(df['created_at']).dt.strftime('%d/%m %H:%M')
            edit_df = st.data_editor(df[["id", "nombre", "precio", "cantidad", "fecha_f"]], key=f"ed_{m_name}", use_container_width=True, hide_index=True)
            
            c1, c2 = st.columns(2)
            if c1.button(f"💾 Sincronizar {m_name}", key=f"btn_{m_name}"):
                for _, row in edit_df.iterrows():
                    supabase.table("productos").update({"precio": row['precio'], "cantidad": row['cantidad']}).eq("id", row['id']).execute()
                st.rerun()
            
            id_del = c2.number_input("ID a borrar", min_value=0, key=f"del_{m_name}", step=1)
            if c2.button(f"🗑️ Eliminar ID {id_del}", key=f"bdel_{m_name}"):
                supabase.table("productos").delete().eq("id", id_del).execute()
                st.rerun()
        else:
            st.info("No hay productos aquí.")

# 3. CHEF IA (Mejorado)
st.divider()
st.subheader("👨‍🍳 Chef IA")
if not df_all.empty:
    comida_list = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]['nombre'].tolist()
    if comida_list:
        if st.button("🪄 ¿Qué puedo cocinar hoy?", use_container_width=True):
            with st.spinner("Pensando recetas..."):
                st.markdown(llamar_ia_chef(comida_list))
