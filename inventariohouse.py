import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inventario Local", layout="wide")
st.title("📦 INVENTARIO IGNACIO-HOUSE")

# --- FUNCIONES DE BASE DE DATOS (SQLite) ---
def conectar_db():
    conn = sqlite3.connect('inventario.db', check_same_thread=False)
    return conn

def crear_tabla():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modulo TEXT,
            nombre TEXT,
            precio REAL,
            cantidad INTEGER
        )
    ''')
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
    cursor.execute("INSERT INTO productos (modulo, nombre, precio, cantidad) VALUES (?, ?, ?, ?)", (m, n, p, c))
    conn.commit()
    conn.close()

def borrar_producto(id_prod):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE id = ?", (id_prod,))
    conn.commit()
    conn.close()

# Inicializar la base de datos al abrir
crear_tabla()

# --- INTERFAZ LATERAL ---
st.sidebar.header("Añadir Producto")
modulo_sel = st.sidebar.selectbox("Elegir Módulo", ["Comida", "Hogar", "Por Comprar"])
nombre_input = st.sidebar.text_input("Nombre del producto")
precio_input = st.sidebar.number_input("Precio ($)", min_value=0.0, step=0.1)
cantidad_input = st.sidebar.number_input("Cantidad", min_value=1, step=1)

if st.sidebar.button("Guardar en SQL"):
    if nombre_input:
        guardar_producto(modulo_sel, nombre_input.capitalize(), precio_input, cantidad_input)
        st.sidebar.success(f"¡{nombre_input} guardado!")
        st.rerun()
    else:
        st.sidebar.error("Escribe un nombre")

# --- CUERPO PRINCIPAL ---
tab1, tab2, tab3 = st.tabs(["🍕 Comida", "🏠 Hogar", "🛒 Por Comprar"])
df_total = leer_datos()

def mostrar_pestaña(nombre_modulo, pestaña):
    with pestaña:
        if not df_total.empty:
            df = df_total[df_total['modulo'] == nombre_modulo].copy()
            if not df.empty:
                df['Subtotal'] = df['precio'] * df['cantidad']
                st.dataframe(df.drop(columns=['modulo']), use_container_width=True, hide_index=True)
                
                total = df['Subtotal'].sum()
                st.metric("Total", f"${total:,.2f}")
                
                id_borrar = st.number_input(f"ID a borrar en {nombre_modulo}", min_value=0, key=f"id_{nombre_modulo}")
                if st.button(f"Eliminar", key=f"btn_{nombre_modulo}"):
                    borrar_producto(id_borrar)
                    st.rerun()
            else:
                st.info(f"No hay nada en {nombre_modulo}")
        else:
            st.info("La base de datos está vacía.")

mostrar_pestaña("Comida", tab1)
mostrar_pestaña("Hogar", tab2)
mostrar_pestaña("Por Comprar", tab3)
