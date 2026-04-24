import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client
import google.generativeai as genai

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inventario MI❤️AMOR JYI", layout="wide")

# --- CONFIGURACIÓN DE GEMINI IA ---
# Se usa model_name explícito para evitar el error 404 en Streamlit Cloud
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel(model_name='gemini-1.5-flash')
else:
    st.error("Falta la clave GEMINI_API_KEY en los secretos de Streamlit.")

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
    
    # Barra lateral
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
                        "modulo": mod, 
                        "nombre": n_cap, 
                        "precio": pre, 
                        "cantidad": can,
                        "created_at": datetime.now().isoformat()
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
    df_all = pd.DataFrame(response.data)

    nombres_tabs = ["Comida", "Hogar", "Por Comprar"]
    tabs = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

    for i, tab in enumerate(tabs):
        m_name = nombres_tabs[i]
        with tab:
            if not df_all.empty:
                df = df_all[df_all['modulo'] == m_name].copy()
            else:
                df = pd.DataFrame()

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
                        supabase.table("productos").update({
                            "precio": row['precio'], 
                            "cantidad": row['cantidad']
                        }).eq("id", row['id']).execute()
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
    st.subheader("👨‍🍳 Chef IA: ¿Qué cocinamos hoy?")
    
    with st.expander("Sugerencias de recetas personalizadas", expanded=False):
        if not df_all.empty:
            df_comida = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]
            lista_ingredientes = df_comida['nombre'].tolist()
            
            if lista_ingredientes:
                st.write(f"**Ingredientes disponibles:** {', '.join(lista_ingredientes)}")
                
                if st.button("🪄 Generar Recetas", use_container_width=True):
                    with st.spinner("Consultando al Chef..."):
                        try:
                            prompt = f"""
                            Actúa como un chef creativo. Tengo estos ingredientes: {', '.join(lista_ingredientes)}.
                            Sugiere 3 recetas rápidas. Usa un tono amigable.
                            Formato: Título en negrita, ingredientes y pasos cortos.
                            """
                            # Llamada directa al modelo
                            response = model.generate_content(prompt)
                            st.markdown(response.text)
                        except Exception as e:
                            st.error(f"Error de conexión con la IA: {e}")
            else:
                st.warning("No hay ingredientes en 'Comida' para crear recetas.")
        else:
            st.info("Inventario vacío.")
