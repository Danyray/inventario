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

# --- INTERFAZ LATERAL ---
st.sidebar.header("Añadir Producto")
modulo_sel = st.sidebar.selectbox("Elegir Módulo", ["Comida", "Hogar", "Por Comprar"])
nombre_input = st.sidebar.text_input("Nombre del producto")
precio_input = st.sidebar.number_input("Precio ($)", min_value=0.0, step=0.1)
cantidad_input = st.sidebar.number_input("Cantidad", min_value=1, step=1)

if st.sidebar.button("Guardar en Inventario"):
    if nombre_input:
        nombre_cap = nombre_input.strip().capitalize()
        fue_guardado = guardar_producto(modulo_sel, nombre_cap, precio_input, cantidad_input)
        
        if fue_guardado:
            st.sidebar.success(f"✅ LISTO: {nombre_cap} guardado.")
            st.rerun()
        else:
            st.sidebar.warning(f"⚠️ El producto '{nombre_cap}' ya existe en {modulo_sel}.")
    else:
        st.sidebar.error("Escribe un nombre")

# --- CUERPO PRINCIPAL ---
df_total = leer_datos()
tab1, tab2, tab3 = st.tabs(["🍕 Comida", "🏠 Hogar", "🛒 Por Comprar"])

def mostrar_pestaña(nombre_modulo, pestaña):
    with pestaña:
        df = df_total[df_total['modulo'] == nombre_modulo].copy()
        if not df.empty:
            st.subheader(f"Listado de {nombre_modulo}")
            
            # CONFIGURACIÓN DE COLUMNAS: Ahora el ID es visible y está marcado como "ID #"
            columnas_config = {
                "id": st.column_config.NumberColumn("🆔 ID", disabled=True, format="%d"),
                "modulo": None, # Ocultamos la columna módulo porque ya estamos en su pestaña
                "nombre": st.column_config.TextColumn("Producto", disabled=True),
                "precio": st.column_config.NumberColumn("Precio ($)", min_value=0, format="$%.2f"),
                "cantidad": st.column_config.NumberColumn("Cantidad", min_value=0),
            }
            
            # Reordenamos las columnas para que el ID sea lo primero que se vea
            df = df[["id", "nombre", "precio", "cantidad"]]

            edited_df = st.data_editor(
                df, 
                column_config=columnas_config, 
                use_container_width=True, 
                hide_index=True, 
                key=f"editor_{nombre_modulo}"
            )

            if st.button(f"Confirmar cambios en {nombre_modulo}", key=f"save_{nombre_modulo}"):
                for index, row in edited_df.iterrows():
                    actualizar_dato(row['id'], 'precio', row['precio'])
                    actualizar_dato(row['id'], 'cantidad', row['cantidad'])
                st.success("Cambios aplicados correctamente.")
                st.rerun()

            st.divider()
            col_del, col_move = st.columns(2)
            
            with col_del:
                st.write("### 🗑️ Eliminar")
                id_borrar = st.number_input(f"Ingresa el ID para borrar", min_value=0, key=f"del_id_{nombre_modulo}", step=1)
                if st.button(f"Eliminar Producto con ID {id_borrar}", key=f"btn_del_{nombre_modulo}"):
                    borrar_producto(id_borrar)
                    st.rerun()

            if nombre_modulo == "Por Comprar":
                with col_move:
                    st.write("### 🚚 Traspasar")
                    id_mover = st.number_input(f"Ingresa el ID para pasar a Comida", min_value=0, key="move_id", step=1)
                    if st.button(f"Mover ID {id_mover} a Comida", key="btn_move"):
                        mover_a_comida(id_mover)
                        st.success("Producto movido.")
                        st.rerun()
            
            st.divider()
            df['Subtotal'] = df['precio'] * df['cantidad']
            total = df['Subtotal'].sum()
            st.metric("Inversión Total en el módulo", f"${total:,.2f}")
        else:
            st.info(f"No hay nada en {nombre_modulo}")

mostrar_pestaña("Comida", tab1)
mostrar_pestaña("Hogar", tab2)
mostrar_pestaña("Por Comprar", tab3)
