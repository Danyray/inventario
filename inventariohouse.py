import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inventario Ignacio-House", layout="wide")

# --- DISEÑO MINIMALISTA Y ELEGANTE (CSS) ---
st.markdown("""
    <style>
    /* Fuente y fondo general */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Estilo de las métricas (Totales) */
    [data-testid="stMetricValue"] { font-size: 28px !important; color: #1E1E1E; }
    
    /* Personalización de los expanders (Formulario) */
    .st-expander { border: 1px solid #E0E0E0 !important; border-radius: 12px !important; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
    
    /* Botones de acción */
    .stButton>button {
        border-radius: 8px !important;
        transition: all 0.3s ease;
        border: none !important;
        height: 2.8em !important;
        font-weight: 600 !important;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    
    /* Estilo para los Títulos dentro de Tabs */
    .section-title {
        padding: 10px 0px;
        border-bottom: 2px solid;
        margin-bottom: 20px;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
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
                    st.error("Credenciales incorrectas")
        return False
    return True

# --- LÓGICA PRINCIPAL ---
if login():
    # Encabezado limpio
    c_title, c_user = st.columns([4, 1])
    with c_title:
        st.title("📦 Gestión de Inventario")
    with c_user:
        st.write(f"👤 **{st.session_state.user}**")
        if st.button("Cerrar Sesión"):
            st.session_state.auth = False
            st.rerun()

    # --- AGREGAR PRODUCTO (Diseño Compacto) ---
    with st.expander("➕ Registrar Nuevo Producto", expanded=False):
        c1, c2, c3 = st.columns([2, 2, 1])
        mod = c1.selectbox("Ubicación", ["Comida", "Hogar", "Por Comprar"])
        nom = c2.text_input("¿Qué vas a agregar?")
        pre = c3.number_input("Precio ($)", min_value=0.0, step=0.1)
        can = st.slider("Cantidad", 1, 50, 1)

        if st.button("🚀 GUARDAR EN BASE DE DATOS", use_container_width=True):
            if nom:
                n_cap = nom.strip().capitalize()
                ahora = datetime.now()
                supabase.table("productos").insert({
                    "modulo": mod, "nombre": n_cap, "precio": pre, 
                    "cantidad": can, "created_at": ahora.isoformat()
                }).execute()
                st.success(f"Guardado: {n_cap} ({ahora.strftime('%H:%M')})")
                time.sleep(1)
                st.rerun()

    st.write("") # Espaciador

    # --- CARGA Y PESTAÑAS ---
    response = supabase.table("productos").select("*").order("id").execute()
    df_all = pd.DataFrame(response.data)

    # Pestañas con nombres claros
    tabs = st.tabs(["🍕 Comida", "🏠 Hogar", "🛒 Lista de Compras"])
    configs = {
        "Comida": {"color": "#E74C3C", "label": "DESPENSA"},
        "Hogar": {"color": "#3498DB", "label": "ARTÍCULOS DEL HOGAR"},
        "Por Comprar": {"color": "#27AE60", "label": "NOTAS DE COMPRA"}
    }

    for i, tab in enumerate(tabs):
        m_key = list(configs.keys())[i]
        conf = configs[m_key]
        
        with tab:
            # Título elegante con borde de color
            st.markdown(f"""<div class='section-title' style='color: {conf['color']}; border-color: {conf['color']};'>
                        {conf['label']}</div>""", unsafe_allow_html=True)
            
            if not df_all.empty:
                df = df_all[df_all['modulo'] == m_key].copy()
            else:
                df = pd.DataFrame()

            if not df.empty:
                # Formatear fecha para humanos
                df['fecha_f'] = pd.to_datetime(df['created_at']).dt.strftime('%d %b, %H:%M')
                
                # Configuración de tabla
                col_cfg = {
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "nombre": st.column_config.TextColumn("Producto", width="medium"),
                    "precio": st.column_config.NumberColumn("Precio", format="$%.2f"),
                    "cantidad": st.column_config.NumberColumn("Cant."),
                    "fecha_f": st.column_config.TextColumn("📅 Registro", disabled=True)
                }
                
                # Editor de datos
                df_v = df[["id", "nombre", "precio", "cantidad", "fecha_f"]]
                edit_df = st.data_editor(df_v, column_config=col_cfg, use_container_width=True, hide_index=True, key=f"editor_{m_key}")

                # Botones de gestión en una fila
                c_save, c_del, c_mov = st.columns([2, 2, 2])
                
                if c_save.button(f"💾 Guardar Cambios en {m_key}", use_container_width=True):
                    for _, row in edit_df.iterrows():
                        supabase.table("productos").update({
                            "precio": row['precio'], "cantidad": row['cantidad']
                        }).eq("id", row['id']).execute()
                    st.toast("Cambios guardados")
                    st.rerun()

                id_del = c_del.number_input("ID Borrar", min_value=0, key=f"del_{m_key}", step=1, label_visibility="collapsed")
                if c_del.button(f"🗑️ Borrar ID {id_del}", use_container_width=True):
                    supabase.table("productos").delete().eq("id", id_del).execute()
                    st.rerun()
                
                if m_key == "Por Comprar":
                    id_m = c_mov.number_input("ID Mover", min_value=0, key="mov_val", step=1, label_visibility="collapsed")
                    if c_mov.button(f"🚚 Mover {id_m} a Comida", use_container_width=True):
                        supabase.table("productos").update({"modulo": "Comida"}).eq("id", id_m).execute()
                        st.rerun()

                # Métricas al pie
                total_val = (df['precio'] * df['cantidad']).sum()
                st.divider()
                st.metric(label=f"Inversión Total en {m_key}", value=f"${total_val:,.2f}")
            else:
                st.info(f"No hay registros en {m_key}.")
