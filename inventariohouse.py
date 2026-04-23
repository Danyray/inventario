import streamlit as st
import sqlite3
import pandas as pd
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inventario Ignacio-House", layout="wide")

# --- SISTEMA DE AUTENTICACIÓN ---
def login():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 Acceso al Sistema")
        usuarios_validos = {"ignacio": "yosa0325", "joseilys": "yosa0325"}

        with st.form("login_form"):
            user = st.text_input("Usuario").lower().strip()
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Entrar")

            if submit:
                if user in usuarios_validos and usuarios_validos[user] == password:
                    st.session_state.authenticated = True
                    st.session_state.user = user.capitalize()
                    st.success(f"Bienvenido/a {st.session_state.user}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
        return False
    return True

# --- FUNCIONES DE BASE DE DATOS ---
def conectar_db():
    return sqlite3.connect('inventario.db', check_same_thread=False)

def crear_tabla():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modulo TEXT, nombre TEXT, precio REAL, cantidad INTEGER)''')
    conn.commit()
    conn.close()

def leer_datos():
    conn = conectar_db()
    df = pd.read_sql_query("SELECT * FROM productos", conn)
    conn.close()
    return df

def guardar_producto(m, n, p, c):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM productos WHERE nombre = ? AND modulo = ?", (n, m))
    if cursor.fetchone():
        conn.close()
        return False 
    cursor.execute("INSERT INTO productos (modulo, nombre, precio, cantidad) VALUES (?, ?, ?, ?)", (m, n, p, c))
    conn.commit()
    conn.close()
    return True

def actualizar_dato(id_prod, columna, nuevo_valor):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE productos SET {columna} = ? WHERE id = ?", (nuevo_valor, id_prod))
    conn.commit()
    conn.close()

def mover_a_comida(id_prod):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE productos SET modulo = 'Comida' WHERE id = ?", (id_prod,))
    conn.commit()
    conn.close()

def borrar_producto(id_prod):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE id = ?", (id_prod,))
    conn.commit()
    conn.close()

# --- LÓGICA PRINCIPAL ---
if login():
    crear_tabla()
    st.title("📦 INVENTARIO IGNACIO-HOUSE")
    st.sidebar.write(f"Sesión: **{st.session_state.user}**")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.authenticated = False
        st.rerun()

    # --- FORMULARIO AGREGAR ---
    with st.expander("➕ AGREGAR NUEVO PRODUCTO", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            mod_sel = st.selectbox("Lista", ["Comida", "Hogar", "Por Comprar"])
            nom_in = st.text_input("Nombre")
        with c2:
            pre_in = st.number_input("Precio ($)", min_value=0.0, step=0.1)
            can_in = st.number_input("Cantidad", min_value=1, step=1)

        if st.button("🚀 GUARDAR", use_container_width=True):
            if nom_in:
                nom_cap = nom_in.strip().capitalize()
                if guardar_producto(mod_sel, nom_cap, pre_in, can_in):
                    st.toast(f'¡{nom_cap} guardado!', icon='✅')
                    st.success("✨ GUARDADO EXITOSO")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning(f"⚠️ '{nom_cap}' ya existe en {mod_sel}.")
            else:
                st.error("Falta el nombre.")

    st.divider()

    # --- TABLAS ---
    df_total = leer_datos()
    nombres_mod = ["Comida", "Hogar", "Por Comprar"]
    tabs = st.tabs(["🍕 Comida", "🏠 Hogar", "🛒 Por Comprar"])

    for i, tab in enumerate(tabs):
        nombre_tab = nombres_mod[i]
        with tab:
            df = df_total[df_total['modulo'] == nombre_tab].copy()
            if not df.empty:
                col_cfg = {
                    "id": st.column_config.NumberColumn("🆔 ID", disabled=True, format="%d"),
                    "nombre": st.column_config.TextColumn("Producto", disabled=True),
                    "precio": st.column_config.NumberColumn("Precio ($)", min_value=0, format="$%.2f"),
                    "cantidad": st.column_config.NumberColumn("Cantidad", min_value=0),
                }
                
                df_v = df[["id", "nombre", "precio", "cantidad"]]
                edit_df = st.data_editor(df_v, column_config=col_cfg, use_container_width=True, hide_index=True, key=f"ed_{nombre_
