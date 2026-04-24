import streamlit as st
import pandas as pd
import time
import requests
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inventario MI❤️AMOR JYI", layout="wide")

# --- FUNCIÓN PARA LA IA DEL CHEF (MODELO DE ALTA DISPONIBILIDAD) ---
def llamar_ia_chef(ingredientes_lista):
    if "HUGGINGFACE_TOKEN" not in st.secrets:
        return "⚠️ Falta el token HUGGINGFACE_TOKEN en los Secrets."

    # Modelo ligero de Google (FLAN-T5): Menos propenso a errores 404/503
    url = "https://api-inference.huggingface.co/models/google/flan-t5-large"
    token = st.secrets["HUGGINGFACE_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}
    
    prompt = f"Tengo estos ingredientes: {', '.join(ingredientes_lista)}. Dime 3 nombres de platos deliciosos que puedo cocinar."
    payload = {"inputs": prompt}
    
    # Intentos de conexión
    for intento in range(2):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                res_json = response.json()
                if isinstance(res_json, list) and len(res_json) > 0:
                    return f"👨‍🍳 **Sugerencia del Chef:** {res_json[0].get('generated_text')}"
            elif response.status_code == 503:
                time.sleep(5)
                continue
        except:
            continue
    
    # --- SISTEMA DE RESPALDO (FALLBACK) ---
    # Si la IA falla, el código genera una respuesta lógica basada en tus ingredientes
    sugerencias_locales = [
        f"Salteado de {ingredientes_lista[0]}",
        f"Ensalada mixta con {ingredientes_lista[-1]}",
        "Pasta o Arroz con los ingredientes disponibles"
    ]
    return f"👨‍🍳 **Sugerencia rápida (Modo Offline):** {', '.join(sugerencias_locales)}"

# --- ESTILOS PERSONALIZADOS (CSS) ---
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
                    st.success(f"Bienvenido/a {st.session_state.user}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Usuario o clave incorrectos")
        return False
    return True

# --- LÓGICA DE LA APP ---
if login():
    st.title("📦 INVENTARIO MI❤️AMOR JYI")
    
    st.sidebar.write(f"Usuario: **{st.session_state.user}**")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

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
                fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
                exist = supabase.table("productos").select("id").eq("nombre", n_cap).eq("modulo", mod).execute()
                
                if len(exist.data) > 0:
                    st.warning("⚠️ Ese producto ya existe en esta lista.")
                else:
                    supabase.table("productos").insert({
                        "modulo": mod, "nombre": n_cap, "precio": pre, 
                        "cantidad": can, "created_at": datetime.now().isoformat()
                    }).execute()
                    st.toast(f"¡{n_cap} guardado!", icon="✅")
                    st.success(f"✨ REGISTRADO EL {fecha_hoy}")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Por favor, escribe un nombre.")

    st.divider()

    # --- VISUALIZACIÓN POR PESTAÑAS ---
    response = supabase.table("productos").select("*").order("id").execute()
    df_all = pd.DataFrame(response.data if response.data else [])

    nombres_tabs = ["Comida", "Hogar", "Por Comprar"]
    tabs = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

    for i, tab in enumerate(tabs):
        m_name = nombres_tabs[i]
        with tab:
            df = df_all[df_all['modulo'] == m_name].copy() if not df_all.empty else pd.DataFrame()

            if not df.empty:
                df['fecha_f'] = pd.to_datetime(df['created_at']).dt.strftime('%d/%m %H:%M')
                cfg = {
                    "id": st.column_config.NumberColumn("🆔", disabled=True),
                    "nombre": st.column_config.TextColumn("Producto", disabled=True),
                    "precio": st.column_config.NumberColumn("Precio ($)", format="$%.2f"),
                    "cantidad": st.column_config.NumberColumn("Cant"),
                    "fecha_f": st.column_config.TextColumn("📅 Agregado", disabled=True)
                }
                df_v = df[["id", "nombre", "precio", "cantidad", "fecha_f"]]
                k_ed = f"ed_{m_name.replace(' ', '')}"
                edit_df = st.data_editor(df_v, column_config=cfg, use_container_width=True, hide_index=True, key=k_ed)

                if st.button(f"💾 Guardar cambios en {m_name}", key=f"s_{m_name.replace(' ', '')}"):
                    for index, row in edit_df.iterrows():
                        supabase.table("productos").update({"precio": row['precio'], "cantidad": row['cantidad']}).eq("id", row['id']).execute()
                    st.toast("Sincronizado con éxito")
                    st.rerun()

                st.divider()
                cx, cy = st.columns(2)
                id_d = cx.number_input("ID para borrar", min_value=0, key=f"d_{m_name}", step=1)
                if cx.button(f"🗑️ Eliminar permanentemente", key=f"bd_{m_name}"):
                    supabase.table("productos").delete().eq("id", id_d).execute()
                    st.rerun()
                
                if m_name == "Por Comprar":
                    id_m = cy.number_input("ID para mover a Comida", min_value=0, key="m_pc", step=1)
                    if cy.button("🚚 Mover a Despensa", key="bm_pc"):
                        supabase.table("productos").update({"modulo": "Comida"}).eq("id", id_m).execute()
                        st.rerun()

                df['Sub'] = df['precio'] * df['cantidad']
                st.metric(f"Inversión en {m_name}", f"${df['Sub'].sum():,.2f}")
            else:
                st.info(f"La lista de {m_name} está vacía por ahora.")

    # --- SECCIÓN: CHEF IA ---
    st.divider()
    st.subheader("👨‍🍳 Chef IA")
    with st.expander("Ideas para cocinar con lo que tienes", expanded=False):
        if not df_all.empty:
            df_comida = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]
            ing = df_comida['nombre'].tolist()
            
            if ing:
                st.write(f"**Ingredientes:** {', '.join(ing)}")
                if st.button("🪄 Generar Sugerencias", use_container_width=True):
                    with st.spinner("Consultando al Chef..."):
                        resultado = llamar_ia_chef(ing)
                        st.markdown(resultado)
            else:
                st.warning("No tienes alimentos registrados.")
        else:
            st.info("Agrega productos para activar al Chef.")
