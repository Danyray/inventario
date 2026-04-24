import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario MI❤️AMOR JYI", layout="wide")

# --- LÓGICA DEL CHEF PROFESIONAL (CORREGIDA) ---
def generar_menu_coherente(productos):
    # Clasificación precisa
    proteinas = [p.capitalize() for p in productos if any(x in p.capitalize() for x in ["Carne", "Pollo", "Huevo", "Atun", "Cerdo", "Queso", "Mortadela", "Salchicha"])]
    harina_pan = [p.capitalize() for p in productos if "Harina pan" in p.capitalize()]
    harina_trigo = [p.capitalize() for p in productos if "Trigo" in p.capitalize()]
    carbo_cocidos = [p.capitalize() for p in productos if any(x in p.capitalize() for x in ["Arroz", "Pasta", "Papa", "Yuca", "Platano"])]
    pan = [p.capitalize() for p in productos if "Pan" in p.capitalize() and "Harina" not in p.capitalize()]

    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}
    
    # 1. DESAYUNOS LÓGICOS
    # Caso Harina Pan (Arepas)
    if harina_pan and proteinas:
        for p in proteinas[:2]: # Máximo 2 opciones de arepa
            menu["☀️ DESAYUNO"].append({
                "titulo": f"Arepas de Maíz con {p}",
                "receta": f"1. Mezcla la Harina Pan con agua y sal hasta tener una masa suave.\n2. Haz las arepas y cocínalas en el budare.\n3. Abre la arepa y rellena con {p} (ralla el queso si es el caso).",
                "img": ""
            })

    # Caso Harina de Trigo (Panquecas)
    if harina_trigo and proteinas:
        menu["☀️ DESAYUNO"].append({
            "titulo": "Panquecas de Trigo caseras",
            "receta": f"1. Mezcla la Harina de Trigo con un toque de azúcar, sal y agua/leche.\n2. Cocina en un sartén con un poquito de aceite.\n3. Sirve con {proteinas[0]} a un lado o encima.",
            "img": ""
        })

    # Caso Pan
    if pan and proteinas:
        menu["☀️ DESAYUNO"].append({
            "titulo": f"Sándwich de {proteinas[0]}",
            "receta": f"1. Tuesta el pan.\n2. Agrega {proteinas[0]} y un toque de mantequilla o mayonesa si tienes.",
            "img": "

[Image of a classic sandwich]
"
        })

    # 2. ALMUERZOS LÓGICOS (Proteína + Carbohidrato cocido)
    if carbo_cocidos and proteinas:
        for c in carbo_cocidos[:3]:
            # Buscamos una proteína que no sea solo Queso para el almuerzo
            pro_almuerzo = [pr for pr in proteinas if "Queso" not in pr]
            p = pro_almuerzo[0] if pro_almuerzo else proteinas[0]
            
            menu["🍴 ALMUERZO"].append({
                "titulo": f"{c} con {p}",
                "receta": f"1. Pon a hervir agua con sal para el/la {c}.\n2. Prepara el {p} (frito o salteado en tiritas).\n3. Sirve caliente para un almuerzo completo.",
                "img": "

[Image of rice and chicken plate]
"
            })

    # 3. CENAS LIGERAS
    if proteinas:
        menu["🌙 CENA"].append({
            "titulo": f"Cena rápida: {proteinas[-1]}",
            "receta": f"1. Prepara una porción pequeña de {proteinas[-1]}.\n2. Acompaña con una porción mínima de carbohidrato.\n3. Una opción ligera para cerrar el día.",
            "img": "

[Image of a light healthy meal]
"
        })

    return menu

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
        u, p = st.text_input("Usuario").lower().strip(), st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar") and u in ["ignacio", "joseilys"] and p == "yosa0325":
            st.session_state.auth, st.session_state.user = True, u.capitalize()
            st.rerun()
    st.stop()

# --- INTERFAZ ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# AGREGAR PRODUCTO
with st.expander("➕ REGISTRAR NUEVO PRODUCTO"):
    c1, c2 = st.columns(2)
    m_n, n_n = c1.selectbox("Lista", ["Comida", "Hogar", "Por Comprar"]), c1.text_input("Nombre")
    p_n, c_n = c2.number_input("Precio $", min_value=0.0), c2.number_input("Cantidad", min_value=1)
    if st.button("🚀 GUARDAR"):
        supabase.table("productos").insert({"modulo": m_n, "nombre": n_n.capitalize(), "precio": p_n, "cantidad": c_n, "created_at": datetime.now().isoformat()}).execute()
        st.success("¡Guardado!"); time.sleep(1); st.rerun()

# TABLAS
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

tabs = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])
for i, tab in enumerate(tabs):
    mod = ["Comida", "Hogar", "Por Comprar"][i]
    with tab:
        df = df_all[df_all['modulo'] == mod].copy() if not df_all.empty else pd.DataFrame()
        if not df.empty:
            edit_df = st.data_editor(df[["id", "nombre", "precio", "cantidad"]], key=f"ed_{mod}", use_container_width=True, hide_index=True)
            c1, c2 = st.columns(2)
            if c1.button(f"🔄 Actualizar {mod}", key=f"up_{mod}"):
                # --- AQUÍ ESTABA EL ERROR CORREGIDO (r['id'] en lugar de row['id']) ---
                for _, r in edit_df.iterrows(): 
                    supabase.table("productos").update({"precio": r['precio'], "cantidad": r['cantidad']}).eq("id", r['id']).execute()
                st.success("Base de datos actualizada")
                st.rerun()
            id_b = c2.number_input("ID a borrar", min_value=0, key=f"idb_{mod}", step=1)
            if c2.button(f"🗑️ Eliminar Registro", key=f"del_{mod}"):
                supabase.table("productos").delete().eq("id", id_b).execute(); st.rerun()

# --- SECCIÓN CHEF ---
st.divider()
st.subheader("👨‍🍳 Menú del Día (Lógica Real)")
if not df_all.empty:
    comida = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]['nombre'].tolist()
    if st.button("🪄 Mostrar Sugerencias", use_container_width=True):
        menu = generar_menu_coherente(comida)
        for momento, platos in menu.items():
            if platos:
                st.markdown(f"## {momento}")
                for i in range(0, len(platos), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        if i + j < len(platos):
                            with cols[j]:
                                p = platos[i+j]
                                with st.expander(f"🍴 {p['titulo']}"):
                                    st.write(p['img'])
                                    st.info(p['receta'])
