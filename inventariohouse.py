import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inventario Cloud", layout="wide")
st.title("📦 Mi Inventario en la Nube (Google Sheets)")

# URL de tu Google Sheet (Copia tu link aquí)
URL_HOJA = "TU_URL_DE_GOOGLE_SHEET_AQUI"

# 1. CONEXIÓN A GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_datos():
    # Leemos la hoja completa
    df = conn.read(spreadsheet=URL_HOJA)
    return df.dropna(how="all") # Limpia filas vacías

# --- BARRA LATERAL PARA AÑADIR ---
st.sidebar.header("Añadir Producto")
modulo_sel = st.sidebar.selectbox("Elegir Módulo", ["Comida", "Hogar", "Por Comprar"])
nombre_input = st.sidebar.text_input("Nombre del producto")
precio_input = st.sidebar.number_input("Precio ($)", min_value=0.0, step=0.1)
cantidad_input = st.sidebar.number_input("Cantidad", min_value=1, step=1)

if st.sidebar.button("Guardar"):
    if nombre_input:
        df_actual = leer_datos()
        
        # Generar nuevo ID
        nuevo_id = int(df_actual["id"].max() + 1) if not df_actual.empty else 1
        
        # Crear nueva fila
        nueva_fila = pd.DataFrame([{
            "id": nuevo_id,
            "modulo": modulo_sel,
            "nombre": nombre_input.capitalize(),
            "precio": precio_input,
            "cantidad": cantidad_input
        }])
        
        # Concatenar y actualizar nube
        df_final = pd.concat([df_actual, nueva_fila], ignore_index=True)
        conn.update(spreadsheet=URL_HOJA, data=df_final)
        
        st.sidebar.success(f"¡{nombre_input} guardado!")
        st.rerun()
    else:
        st.sidebar.error("Escribe un nombre")

# --- CUERPO PRINCIPAL CON PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["🍕 Comida", "🏠 Hogar", "🛒 Por Comprar"])

def mostrar_contenido(nombre_modulo, pestaña):
    with pestaña:
        df_all = leer_datos()
        # Filtrar por módulo
        df = df_all[df_all['modulo'] == nombre_modulo].copy()

        if not df.empty:
            # Calculamos subtotal y total
            df['Subtotal'] = df['precio'] * df['cantidad']
            
            # Renombrar columnas para la vista del usuario
            vista_df = df[['id', 'nombre', 'precio', 'cantidad', 'Subtotal']].rename(
                columns={'nombre': 'Producto', 'precio': 'Precio', 'cantidad': 'Cantidad'}
            )
            
            st.dataframe(vista_df.drop(columns=['id']), use_container_width=True)
            
            total = df['Subtotal'].sum()
            st.metric(label=f"Valor Total en {nombre_modulo}", value=f"${total:,.2f}")

            # Opción para eliminar
            id_a_borrar = st.number_input(f"ID para eliminar en {nombre_modulo}", min_value=0, key=f"del_{nombre_modulo}")
            if st.button(f"Eliminar ID {id_a_borrar}", key=f"btn_{nombre_modulo}"):
                df_final = df_all[df_all['id'] != id_a_borrar]
                conn.update(spreadsheet=URL_HOJA, data=df_final)
                st.rerun()
        else:
            st.info(f"No hay productos registrados en {nombre_modulo}.")

# Llamar a la función para cada pestaña
mostrar_contenido("Comida", tab1)
mostrar_contenido("Hogar", tab2)
mostrar_contenido("Por Comprar", tab3)

# --- BOTÓN ESPECIAL DE TRASPASO ---
st.divider()
if st.button("✅ Mover todo de 'Por Comprar' a 'Inventario Comida'"):
    df_all = leer_datos()
    if not df_all.empty:
        # Cambiar el valor de la columna modulo
        df_all.loc[df_all['modulo'] == 'Por Comprar', 'modulo'] = 'Comida'
        conn.update(spreadsheet=URL_HOJA, data=df_all)
        st.success("¡Productos movidos con éxito!")
        st.rerun()
    else:
        st.warning("No hay productos para mover.")
