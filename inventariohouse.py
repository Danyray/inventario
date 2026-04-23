import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inventario Ignacio-House", layout="wide")

# --- CSS AVANZADO PARA COLORES (FORZADO) ---
st.markdown("""
    <style>
    /* Fondo general de la app */
    .stApp { background-color: #f8f9fa; }

    /* Colores para las PESTAÑAS (Tabs) */
    button[data-baseweb="tab"] {
        border-radius: 10px 10px 0px 0px !important;
        padding: 10px 20px !important;
        margin: 5px !important;
    }
    
    /* Color para pestaña COMIDA */
    button[id="tabs-bui3-tab-0"] { background-color: #ffe5e5 !important; color: #ff4b4b !important; }
    /* Color para pestaña HOGAR */
    button[id="tabs-bui3-tab-1"] { background-color: #e5f1ff !important; color: #0083b8 !important; }
    /* Color para pestaña POR COMPRAR */
    button[id="tabs-bui3-tab-2"] { background-color: #e5ffe5 !important; color: #28a745 !important; }

    /* Botones más grandes y llamativos */
    .stButton>button {
        width: 100%;
        border-radius: 8px !important;
        height: 3em !important;
        font-weight: bold !important;
    }

    /* Colores específicos para botones de guardado */
    button[key^="s_Comida"] { background-color: #ff4b4b !important; color: white !important; }
    button[key^="s_Hogar"] { background-color: #0083b8 !important; color: white !important; }
    button[key^="s_PorComprar"] { background-color: #28a745 !important; color: white !important; }
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
    st.title("📦 INVENTARIO PROFESIONAL")
    
    st.sidebar.write(f"Sesión: **{st.session_state.user}**")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

    # --- AGREGAR PRODUCTO (CON COLORES EN EL SELECTOR) ---
    with st.expander("➕ REGISTRAR NUEVO ÍTEM", expanded=False):
        c1, c2 = st.columns(2)
        # Diccionario para íconos
        icons = {"Comida": "🍕", "Hogar": "🏠", "Por Comprar": "🛒"}
        mod = c1.selectbox("¿Dónde lo guardamos?", ["Comida", "Hogar", "Por Comprar"])
        nom = c1.text_input("Nombre del Producto")
        pre = c2.number_input("Precio ($)", min_value=0.0, step=0.1)
        can = c2.number_input("Cantidad", min_value=1, step=1)

        if st.button(f"🚀 GUARDAR EN {mod.upper()}", use_container_width=True):
            if nom:
                n_cap = nom.strip().capitalize()
                # Fecha para mostrar
                ahora = datetime.now()
                
                # Insertar en Supabase
                supabase.table("productos").insert({
                    "modulo": mod, 
                    "nombre": n_cap, 
                    "precio": pre, 
                    "cantidad": can,
                    "created_at": ahora.isoformat()
                }).execute()
                
                st.success(f"✅ {n_cap} guardado el {ahora.strftime('%d/%m/%Y a las %H:%M')}")
                time.sleep(1)
                st.rerun()

    st.divider()

    # --- PESTAÑAS DE COLORES ---
    response = supabase.table("productos").select("*").order("id").execute()
    df_all = pd.DataFrame(response.data)

    # Nombres internos para la lógica
    secciones = ["Comida", "Hogar", "Por Comprar"]
    # Pestañas con Emojis para que resalten más
    tabs = st.tabs(["🍕 DESPENSA", "🏠 ART. HOGAR", "🛒 LISTA DE COMPRAS"])

    for i, tab in enumerate(tabs):
        m_name = secciones[i]
        with tab:
            # Color de encabezado manual para cada pestaña
            colores_titulos = {"Comida": "#ff4b4b", "Hogar": "#0083b8", "Por Comprar": "#28a745"}
            st.markdown(f"<h2 style='color: {colores_titulos[m_name]};'>{m_name.upper()}</h2>", unsafe_allow_html=True)
            
            if not df_all.empty:
                df = df_all[df_all['modulo'] == m_name].copy()
            else:
                df = pd.DataFrame()

            if not df.empty:
                # Formatear la fecha
                df['fecha_f'] = pd.to_datetime(df['created_at']).dt.strftime('%d/%m %H:%M')
                
                cfg = {
                    "id": st.column_config.NumberColumn("🆔", disabled=True),
                    "nombre": st.column_config.TextColumn("Producto", disabled=True),
                    "precio": st.column_config.NumberColumn("Precio ($)", format="$%.2f"),
                    "cantidad": st.column_config.NumberColumn("Cant."),
                    "fecha_f": st.column_config.TextColumn("📅 Agregado el", disabled=True)
                }
                
                df_v = df[["id", "nombre", "precio", "cantidad", "fecha_f"]]
                k_ed = f"ed_{m_name.replace(' ', '')}"
                
                # Tabla de edición
                edit_df = st.data_editor(df_v, column_config=cfg, use_container_width=True, hide_index=True, key=k_ed)

                # Botón con color asignado por CSS
                if st.button(f"💾 ACTUALIZAR {m_name.upper()}", key=f"s_{m_name.replace(' ', '')}"):
                    for _, row in edit_df.iterrows():
                        supabase.table("productos").update({
                            "precio": row['precio'], 
                            "cantidad": row['cantidad']
                        }).eq("id", row['id']).execute()
                    st.toast("Base de datos sincronizada")
                    st.rerun()

                st.divider()
                # Gestión de IDs
                c_del, c_mov = st.columns(2)
                with c_del:
                    id_d = st.number_input("ID para eliminar", min_value=0, key=f"d_{m_name}", step=1)
                    if st.button(f"🗑️ ELIMINAR ID {id_d}", key=f"bd_{m_name}"):
                        supabase.table("productos").delete().eq("id", id_d).execute()
                        st.rerun()
                
                if m_name == "Por Comprar":
                    with c_mov:
                        id_m = st.number_input("ID para mover", min_value=0, key="m_pc", step=1)
                        if st.button("🚚 TRASPASAR A COMIDA", key="bm_pc"):
                            supabase.table("productos").update({"modulo": "Comida"}).eq("id", id_m).execute()
                            st.rerun()

                # Resumen
                total = (df['precio'] * df['cantidad']).sum()
                st.subheader(f"💰 Total en esta lista: ${total:,.2f}")
            else:
                st.info(f"No hay nada en {m_name} todavía.")
