import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inventario Ignacio-House", layout="wide")

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
    st.title("📦 INVENTARIO IGNACIO-HOUSE")
    
    # Barra lateral para cerrar sesión
    st.sidebar.write(f"Usuario: **{st.session_state.user}**")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

    # Formulario Agregar
    with st.expander("➕ AGREGAR PRODUCTO", expanded=False):
        c1, c2 = st.columns(2)
        mod = c1.selectbox("Lista", ["Comida", "Hogar", "Por Comprar"])
        nom = c1.text_input("Nombre")
        pre = c2.number_input("Precio ($)", min_value=0.0, step=0.1)
        can = c2.number_input("Cantidad", min_value=1, step=1)

        if st.button("🚀 GUARDAR", use_container_width=True):
            if nom:
                n_cap = nom.strip().capitalize()
                
                # Verificar duplicados en Supabase
                exist = supabase.table("productos").select("id").eq("nombre", n_cap).eq("modulo", mod).execute()
                
                if len(exist.data) > 0:
                    st.warning("Ese producto ya existe en esta lista.")
                else:
                    # Insertar en Supabase
                    supabase.table("productos").insert({
                        "modulo": mod, 
                        "nombre": n_cap, 
                        "precio": pre, 
                        "cantidad": can
                    }).execute()
                    st.toast("¡Guardado en la nube!")
                    st.success("✨ LISTO")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Falta el nombre.")

    st.divider()

    # Cargar todos los datos desde Supabase
    response = supabase.table("productos").select("*").order("id").execute()
    df_all = pd.DataFrame(response.data)

    nombres_tabs = ["Comida", "Hogar", "Por Comprar"]
    tabs = st.tabs(["🍕 Comida", "🏠 Hogar", "🛒 Por Comprar"])

    for i, tab in enumerate(tabs):
        m_name = nombres_tabs[i]
        with tab:
            if not df_all.empty:
                df = df_all[df_all['modulo'] == m_name].copy()
            else:
                df = pd.DataFrame()

            if not df.empty:
                cfg = {
                    "id": st.column_config.NumberColumn("🆔 ID", disabled=True),
                    "nombre": st.column_config.TextColumn("Producto", disabled=True),
                    "precio": st.column_config.NumberColumn("Precio", min_value=0, format="$%.2f"),
                    "cantidad": st.column_config.NumberColumn("Cant", min_value=0)
                }
                
                df_v = df[["id", "nombre", "precio", "cantidad"]]
                k_ed = f"editor_{m_name.replace(' ', '')}"
                
                edit_df = st.data_editor(df_v, column_config=cfg, use_container_width=True, hide_index=True, key=k_ed)

                if st.button(f"💾 Guardar cambios {m_name}", key=f"s_{m_name}"):
                    # Actualizar solo las filas que cambiaron (comparando con el original)
                    for index, row in edit_df.iterrows():
                        supabase.table("productos").update({
                            "precio": row['precio'], 
                            "cantidad": row['cantidad']
                        }).eq("id", row['id']).execute()
                    st.toast("Nube actualizada")
                    st.rerun()

                st.divider()
                cx, cy = st.columns(2)
                id_d = cx.number_input("ID a borrar", min_value=0, key=f"d_{m_name}", step=1)
                if cx.button(f"🗑️ Eliminar {id_d}", key=f"bd_{m_name}"):
                    supabase.table("productos").delete().eq("id", id_d).execute()
                    st.rerun()
                
                if m_name == "Por Comprar":
                    id_m = cy.number_input("ID a Inventario", min_value=0, key="m_pc", step=1)
                    if cy.button("🚚 Traspasar", key="bm_pc"):
                        supabase.table("productos").update({"modulo": "Comida"}).eq("id", id_m).execute()
                        st.rerun()

                df['Sub'] = df['precio'] * df['cantidad']
                st.metric(f"Total {m_name}", f"${df['Sub'].sum():,.2f}")
            else:
                st.info(f"Sin productos en {m_name}.")
