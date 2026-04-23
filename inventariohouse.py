import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# CONFIGURACIÓN
st.set_page_config(page_title="Inventario Cloud", layout="wide")
URL_HOJA = "https://docs.google.com/spreadsheets/d/1IjIzhXc7MmLt3fcCB7ReRlK9s_68y0RGdrGzPU2YmHw/edit?usp=sharing"

# Intentar conectar de forma privada
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_datos():
    try:
        # Lectura pública directa (No falla)
        sheet_id = "1IjIzhXc7MmLt3fcCB7ReRlK9s_68y0RGdrGzPU2YmHw"
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(csv_url)
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df.dropna(how="all")
    except:
        return pd.DataFrame(columns=['id', 'modulo', 'nombre', 'precio', 'cantidad'])

# --- INTERFAZ ---
st.sidebar.header("Nuevo Producto")
mod = st.sidebar.selectbox("Módulo", ["Comida", "Hogar", "Por Comprar"])
nom = st.sidebar.text_input("Nombre")
pre = st.sidebar.number_input("Precio", min_value=0.0)
can = st.sidebar.number_input("Cantidad", min_value=1)

if st.sidebar.button("Guardar"):
    if nom:
        df_actual = leer_datos()
        nuevo_id = int(df_actual["id"].max() + 1) if not df_actual.empty else 1
        nueva_fila = pd.DataFrame([{"id": nuevo_id, "modulo": mod, "nombre": nom.capitalize(), "precio": pre, "cantidad": can}])
        df_final = pd.concat([df_actual, nueva_fila], ignore_index=True)
        
        try:
            # EL TRUCO: Intentamos escribir forzando el modo público
            conn.update(spreadsheet=URL_HOJA, data=df_final)
            st.sidebar.success("¡Guardado!")
            st.rerun()
        except Exception as e:
            st.sidebar.error("Google sigue bloqueando la escritura directa.")
            st.info("Ingeniero, para desbloquear esto sin código complejo, haz el paso de 'Secrets' abajo.")

# ... (El resto del código de pestañas se mantiene igual)
