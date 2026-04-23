import streamlit as st
import sqlite3
import pandas as pd
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inventario Ignacio-House", layout="wide")

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

# --- FUNCIONES DE BASE DE DATOS ---
def conectar():
    return sqlite3.connect('inventario.db', check_same_thread=False)

def crear_db():
    conn = conectar()
    conn.execute('''CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modulo TEXT, nombre TEXT, precio REAL, cantidad INTEGER)''')
    conn.commit()
    conn.close()

def db_query(sql, params=()):
    conn = conectar()
    res = pd.read_sql_query(sql, conn, params=params) if "SELECT" in sql.upper() else conn.execute(sql, params)
    conn.commit()
    conn.close()
    return res

# --- LÓGICA DE LA APP ---
if login():
    crear_db()
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
                # Verificar duplicados
                exist = db_query("SELECT id FROM productos WHERE nombre=? AND modulo=?", (n_cap, mod))
                if not exist.empty:
                    st.warning("Ese producto ya existe en esta lista.")
                else:
                    db_query("INSERT INTO productos (modulo, nombre, precio, cantidad) VALUES (?,?,?,?)", (mod, n_cap, pre, can))
                    st.toast("¡Guardado!")
                    st.success("✨ LISTO")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Falta el nombre.")

    st.divider()

    # Pestañas de Visualización
    df_all = db_query("SELECT * FROM productos")
    nombres_tabs = ["Comida", "Hogar", "Por Comprar"]
    tabs = st.tabs(["🍕 Comida", "🏠 Hogar", "🛒 Por Comprar"])

    for i, tab in enumerate(tabs):
        m_name = nombres_tabs[i]
        with tab:
            df = df_all[df_all['modulo'] == m_name].copy()
            if not df.empty:
                # Editor de datos
                cfg = {
                    "id": st.column_config.NumberColumn("🆔 ID", disabled=True),
                    "nombre": st.column_config.TextColumn("Producto", disabled=True),
                    "precio": st.column_config.NumberColumn("Precio", min_value=0, format="$%.2f"),
                    "cantidad": st.column_config.NumberColumn("Cant", min_value=0)
                }
                # Dividimos la línea del editor para que no de error de sintaxis
                df_v = df[["id", "nombre", "precio", "cantidad"]]
                k_ed = f"editor_{m_name.replace(' ', '')}"
                
                edit_df = st.data_editor(df_v, column_config=cfg, use_container_width=True, hide_index=True, key=k_ed)

                if st.button(f"💾 Guardar cambios {m_name}", key=f"s_{m_name}"):
                    for _, r in edit_df.iterrows():
                        db_query("UPDATE productos SET precio=?, cantidad=? WHERE id=?", (r['precio'], r['cantidad'], r['id']))
                    st.toast("Actualizado")
                    st.rerun()

                st.divider()
                cx, cy = st.columns(2)
                id_d = cx.number_input("ID a borrar", min_value=0, key=f"d_{m_name}", step=1)
                if cx.button(f"🗑️ Eliminar {id_d}", key=f"bd_{m_name}"):
                    db_query("DELETE FROM productos WHERE id=?", (id_d,))
                    st.rerun()
                
                if m_name == "Por Comprar":
                    id_m = cy.number_input("ID a Inventario", min_value=0, key="m_pc", step=1)
                    if cy.button("🚚 Traspasar", key="bm_pc"):
                        db_query("UPDATE productos SET modulo='Comida' WHERE id=?", (id_m,))
                        st.rerun()

                df['Sub'] = df['precio'] * df['cantidad']
                st.metric(f"Total {m_name}", f"${df['Sub'].sum():,.2f}")
            else:
                st.info("Sin productos registrados.")
