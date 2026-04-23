import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inventario Ignacio-House", layout="wide")
st.title("📦 INVENTARIO IGNACIO-HOUSE")

# --- FUNCIONES DE BASE DE DATOS ---
def conectar_db():
    return sqlite3.connect('inventario.db', check_same_thread=False)

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
    cursor.execute("SELECT id FROM productos WHERE nombre = ? AND modulo = ?", (n, m))
    existe = cursor.fetchone()
    if existe:
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

# Inicializar DB
crear_tabla()

# --- FORMULARIO DE AGREGAR (CENTRAL Y VISIBLE) ---
with st.expander("➕ HACER CLIC AQUÍ PARA AGREGAR NUEVO PRODUCTO", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        modulo_sel = st.selectbox("¿En qué lista?", ["Comida", "Hogar", "Por Comprar"])
        nombre_input = st.text_input("Nombre del producto")
    with col2:
        precio_input = st.number_input("Precio ($)", min_value=0.0, step=0.1)
        cantidad_input = st.number_input("Cantidad", min_value=1, step=1)

    if st.button("🚀 GUARDAR PRODUCTO", use_container_width=True):
        if nombre_input:
            nombre_cap = nombre_input.strip().capitalize()
            if guardar_producto(modulo_sel, nombre_cap, precio_input, cantidad_input):
                st.success(f"✅ LISTO: {nombre_cap} guardado.")
                st.rerun()
            else:
                st.warning(f"⚠️ '{nombre_cap}' ya existe en {modulo_sel}.")
        else:
            st.error("Escribe un nombre.")

st.divider()

# --- TABLAS Y CONTENIDO ---
df_total = leer_datos()
tabs = st.tabs(["🍕 Comida", "🏠 Hogar", "🛒 Por Comprar"])
nombres_modulos = ["Comida", "Hogar", "Por Comprar"]

for i, tab in enumerate(tabs):
    nombre_mod = nombres_modulos[i]
    with tab:
        df = df_total[df_total['modulo'] == nombre_mod].copy()
        if not df.empty:
            st.subheader(f"Listado de {nombre_mod}")
            
            # Configuración de edición
            columnas_config = {
                "id": st.column_config.NumberColumn("🆔 ID", disabled=True, format="%d"),
                "modulo": None,
                "nombre": st.column_config.TextColumn("Producto", disabled=True),
                "precio": st.column_config.NumberColumn("Precio ($)", min_value=0, format="$%.2f"),
                "cantidad": st.column_config.NumberColumn("Cantidad", min_value=0),
            }
            
            df_vista = df[["id", "nombre", "precio", "cantidad"]]
            edited_df = st.data_editor(
                df_vista, 
                column_config=columnas_config, 
                use_container_width=True, 
                hide_index=True, 
                key=f"ed_{nombre_mod}"
            )

            if st.button(f"💾 Guardar cambios en {nombre_mod}", key=f"btn_save_{nombre_mod}"):
                for _, row in edited_df.iterrows():
                    actualizar_dato(row['id'], 'precio', row['precio'])
                    actualizar_dato(row['id'], 'cantidad', row['cantidad'])
                st.success("Cambios aplicados.")
                st.rerun()

            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                id_del = st.number_input("ID para borrar", min_value=0, key=f"id_del_{nombre_mod}", step=1)
                if st.button(f"🗑️ Eliminar ID {id_del}", key=f"btn_del_{nombre_mod}"):
                    borrar_producto(id_del)
                    st.rerun()
            
            if nombre_mod == "Por Comprar":
                with c2:
                    id_mov = st.number_input("ID para mover a Comida", min_value=0, key="id_mov", step=1)
                    if st.button(f"🚚 Mover ID {id_mov}", key="btn_mov"):
                        mover_a_comida(id_mov)
                        st.rerun()

            st.divider()
            df['Subtotal'] = df['precio'] * df['cantidad']
            st.metric(f"Total {nombre_mod}", f"${df['Subtotal'].sum():,.2f}")
        else:
            st.info(f"No hay productos en {nombre_mod}.")
