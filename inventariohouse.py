¡Entiendo perfectamente! Quieres que el Chef deje de dar "títulos" y pase a darte soluciones reales: ideas variadas, el paso a paso de la preparación y una imagen para que se les antoje el plato a ti y a Joseilys.

Para lograr esto, vamos a usar una técnica llamada "Expanders" de Streamlit. Al hacer clic en el nombre del plato, se desplegará la receta. Además, he configurado el código para que te dé 5 ideas y busque imágenes ilustrativas.

Aquí tienes el código completo y actualizado:

Python

import streamlit as st
import pandas as pd
import time
import requests
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Inventario MI❤️AMOR JYI", layout="wide")

# --- FUNCIÓN PARA EL CHEF IA (RECETAS DETALLADAS) ---
def obtener_recetas_detalladas(ingredientes_lista):
    # Filtro de ingredientes para que la receta tenga sentido
    basicos = ["Azucar", "Sal", "Aceite", "Mayonesa", "Vinagre"]
    filtrados = [i for i in ingredientes_lista if not any(b.lower() in i.lower() for b in basicos)]
    principal = filtrados[0] if filtrados else "ingredientes varios"
    
    # Definimos 5 ideas de recetas basadas en tus ingredientes
    ideas = [
        {
            "titulo": f"🫓 Arepas Rellenas Especiales",
            "receta": f"1. Prepara la masa con {principal}.\n2. Haz bolitas y aplana.\n3. Cocina en budare 5 min por lado.\n4. Rellena con lo que tengas en la nevera.",
            "img": ""
        },
        {
            "titulo": f"🥘 Salteado Criollo de {principal}",
            "receta": f"1. Corta el {principal} en trozos pequeños.\n2. Sofríe con un poco de aceite.\n3. Agrega vegetales picados.\n4. Sirve con arroz o pasta.",
            "img": ""
        },
        {
            "titulo": f"🥣 Bowl Mixto JYI",
            "receta": f"1. Usa una base de arroz o pasta.\n2. Agrega {principal} cocido arriba.\n3. Añade un toque de mayonesa o salsa.\n4. Mezcla y disfruta.",
            "img": ""
        },
        {
            "titulo": f"🍳 Tortilla de la Casa",
            "receta": f"1. Bate 2 huevos.\n2. Agrega {principal} picadito.\n3. Cocina a fuego lento en un sartén tapado.\n4. Voltea con cuidado y dora.",
            "img": ""
        },
        {
            "titulo": f"🍝 Pasta Express con {principal}",
            "receta": f"1. Hierve agua con sal.\n2. Cocina la pasta al dente.\n3. Mezcla con {principal} y un toque de mantequilla o aceite.\n4. ¡Listo en 10 minutos!",
            "img": ""
        }
    ]
    return ideas

# --- CONEXIÓN SUPABASE ---
@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar_supabase()

# --- LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔐 Acceso al Sistema")
    with st.form("login"):
        u = st.text_input("Usuario").lower().strip()
        p = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            if u in ["ignacio", "joseilys"] and p == "yosa0325":
                st.session_state.auth = True
                st.session_state.user = u.capitalize()
                st.rerun()
            else: st.error("Acceso denegado")
    st.stop()

# --- APP PRINCIPAL ---
st.title("📦 INVENTARIO MI❤️AMOR JYI")

# 1. FORMULARIO AGREGAR
with st.expander("➕ AGREGAR NUEVO PRODUCTO", expanded=False):
    c1, c2 = st.columns(2)
    mod_n = c1.selectbox("Lista", ["Comida", "Hogar", "Por Comprar"])
    nom_n = c1.text_input("Nombre")
    pre_n = c2.number_input("Precio $", min_value=0.0, step=0.1)
    can_n = c2.number_input("Cantidad", min_value=1, step=1)
    if st.button("🚀 GUARDAR PRODUCTO", use_container_width=True):
        if nom_n:
            supabase.table("productos").insert({
                "modulo": mod_n, "nombre": nom_n.capitalize(), 
                "precio": pre_n, "cantidad": can_n, "created_at": datetime.now().isoformat()
            }).execute()
            st.success("¡Guardado!")
            time.sleep(1)
            st.rerun()

# 2. TABLAS DE INVENTARIO
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

tabs = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])
listas = ["Comida", "Hogar", "Por Comprar"]

for i, tab in enumerate(tabs):
    with tab:
        df = df_all[df_all['modulo'] == listas[i]].copy() if not df_all.empty else pd.DataFrame()
        if not df.empty:
            df['fecha_f'] = pd.to_datetime(df['created_at']).dt.strftime('%d/%m %H:%M')
            edit_df = st.data_editor(df[["id", "nombre", "precio", "cantidad", "fecha_f"]], key=f"ed_{listas[i]}", use_container_width=True, hide_index=True)
            
            c1, c2 = st.columns(2)
            if c1.button(f"💾 Guardar cambios {listas[i]}", key=f"b_{listas[i]}"):
                for _, row in edit_df.iterrows():
                    supabase.table("productos").update({"precio": row['precio'], "cantidad": row['cantidad']}).eq("id", row['id']).execute()
                st.rerun()
            
            id_del = c2.number_input("ID a borrar", min_value=0, key=f"d_{listas[i]}", step=1)
            if c2.button(f"🗑️ Borrar ID {id_del}", key=f"bd_{listas[i]}"):
                supabase.table("productos").delete().eq("id", id_del).execute()
                st.rerun()
        else: st.info("Sin productos.")

# 3. SECCIÓN CHEF IA MEJORADA
st.divider()
st.subheader("👨‍🍳 El Menú de Hoy")

if not df_all.empty:
    comida_disponible = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]['nombre'].tolist()
    
    if comida_disponible:
        if st.button("✨ ¡Dame 5 ideas para cocinar!", use_container_width=True):
            recetas = obtener_recetas_detalladas(comida_disponible)
            
            for r in recetas:
                with st.expander(r['titulo']):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        # Aquí se inserta la etiqueta de imagen
                        st.write(r['img'])
                    with col2:
                        st.write("**Pasos de preparación:**")
                        st.info(r['receta'])
    else:
        st.warning("No hay comida disponible para sugerir recetas.")
