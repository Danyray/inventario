import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI - Chef Pro", layout="wide")

# --- LÓGICA DEL CHEF EQUILIBRADO (SENCILO + GOURMET) ---
def generar_menu_mixto(productos):
    p_list = [str(p).lower() for p in productos]
    tiene = lambda x: any(x in item for item in p_list)
    
    # Clasificación de ingredientes para recetas
    prot = [p.capitalize() for p in productos if any(x in p.lower() for x in ["carne", "pollo", "huevo", "atun", "queso", "mortadela"])]
    carb = [p.capitalize() for p in productos if any(x in p.lower() for x in ["harina", "pan", "pasta", "arroz", "papa"])]
    
    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}

    # --- FUNCIONES DE APOYO ---
    def agregar_opcion(bloque, titulo, receta, tipo="Sencilla"):
        icono = "⚡" if tipo == "Sencilla" else "⭐"
        menu[bloque].append({"titulo": f"{icono} {titulo}", "receta": receta})

    # --- 1. DESAYUNOS (2 Sencillos + 2 Gourmet) ---
    if tiene("harina de maiz") or tiene("harina pan"):
        # Sencillos
        agregar_opcion("☀️ DESAYUNO", "Arepa Básica con Queso", "1. Haz la masa con sal. 2. Cocina la arepa. 3. Rellena con queso rallado o en rebanadas.")
        agregar_opcion("☀️ DESAYUNO", "Arepa con Mantequilla", "1. Prepara la arepa clásica. 2. Ábrela caliente y unta abundante mantequilla.")
        # Gourmet
        if tiene("carne"):
            agregar_opcion("☀️ DESAYUNO", "Arepa 'Pelúa' Gourmet", "1. Saltea la carne en tiritas con comino hasta dorar. 2. Rellena la arepa con la carne y mucho queso rallado para que se funda.", "Gourmet")
        if tiene("azucar"):
            agregar_opcion("☀️ DESAYUNO", "Arepitas Dulces con Queso", "1. Agrega azúcar y un toque de harina de trigo a la masa de maíz. 2. Fríe en abundante aceite. 3. Acompaña con queso salado.", "Gourmet")

    # --- 2. ALMUERZOS (2 Sencillos + 2 Gourmet) ---
    if tiene("pasta") or tiene("arroz"):
        base = "Pasta" if tiene("pasta") else "Arroz"
        # Sencillos
        agregar_opcion("🍴 ALMUERZO", f"{base} con Queso", f"1. Cocina la {base}. 2. Agrega queso arriba y deja que el calor lo ablande.")
        if tiene("carne"):
            agregar_opcion("🍴 ALMUERZO", f"Bistec con {base}", f"1. Cocina el bistec a la plancha con sal. 2. Acompaña con {base} hervida.")
            # Gourmet
            agregar_opcion("🍴 ALMUERZO", f"{base} Salteada con Carne al Comino", f"1. Corta la carne en cubos y saltea con comino y grasa. 2. Mezcla la {base} en el mismo sartén para que absorba el sabor del fondo.", "Gourmet")
        if tiene("queso"):
            agregar_opcion("🍴 ALMUERZO", f"Gratín de {base} y Atún", "1. Mezcla la base con atún (si tienes) o solo queso. 2. Lleva al sartén tapado hasta que el queso dore en la base.", "Gourmet")

    # --- 3. CENAS (2 Sencillos + 2 Gourmet) ---
    # Sencillos
    if tiene("pan"):
        agregar_opcion("🌙 CENA", "Sándwich de Queso", "1. Pan con queso. 2. Pásalo por el sartén para que el pan esté crujiente.")
    if tiene("huevo") or tiene("queso"):
        p = "Huevo" if tiene("huevo") else "Queso"
        agregar_opcion("🌙 CENA", f"Cena rápida de {p}", f"1. Prepara el {p} de forma rápida. 2. Acompaña con lo que tengas a mano.")
        # Gourmet
        agregar_opcion("🌙 CENA", f"Tostadas de {p} al Estilo Bistro", f"1. Tuesta el pan con mantequilla por ambos lados. 2. Prepara el {p} con un toque de comino. 3. Sirve estéticamente sobre el pan.", "Gourmet")

    return menu

# --- CONEXIÓN SUPABASE ---
@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar_supabase()

# --- LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔐 Acceso")
    with st.form("login"):
        u, p = st.text_input("Usuario").lower().strip(), st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar") and u in ["ignacio", "joseilys"] and p == "yosa0325":
            st.session_state.auth, st.session_state.user = True, u.capitalize()
            st.rerun()
    st.stop()

# --- INTERFAZ ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# MÓDULO DE REGISTRO
with st.expander("➕ REGISTRAR NUEVO PRODUCTO"):
    c1, c2 = st.columns(2)
    m_n = c1.selectbox("Lista", ["Comida", "Hogar", "Por Comprar"])
    n_n = c1.text_input("Nombre")
    p_n = c2.number_input("Precio $", min_value=0.0)
    c_n = c2.number_input("Cantidad", min_value=0)
    if st.button("🚀 GUARDAR"):
        if n_n:
            supabase.table("productos").insert({"modulo": m_n, "nombre": n_n.capitalize(), "precio": p_n, "cantidad": c_n, "created_at": datetime.now().isoformat()}).execute()
            st.success("Guardado"); time.sleep(1); st.rerun()

# TABLAS
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

t1, t2, t3 = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 COMPRAS"])
listas = ["Comida", "Hogar", "Por Comprar"]

for i, tab in enumerate([t1, t2, t3]):
    with tab:
        df = df_all[df_all['modulo'] == listas[i]].copy() if not df_all.empty else pd.DataFrame()
        if not df.empty:
            edit_df = st.data_editor(df[["id", "nombre", "precio", "cantidad"]], key=f"ed_{listas[i]}", use_container_width=True, hide_index=True)
            c1, c2 = st.columns(2)
            if c1.button(f"💾 Actualizar {listas[i]}", key=f"up_{listas[i]}"):
                for _, r in edit_df.iterrows():
                    supabase.table("productos").update({"precio": r['precio'], "cantidad": r['cantidad']}).eq("id", r['id']).execute()
                st.rerun()
            id_b = c2.number_input("ID a borrar", min_value=0, key=f"del_{listas[i]}")
            if c2.button(f"🗑️ Eliminar", key=f"btn_{listas[i]}"):
                supabase.table("productos").delete().eq("id", id_b).execute(); st.rerun()

# --- SECCIÓN CHEF ---
st.divider()
st.subheader("👨‍🍳 Sugerencias del Chef (2 Sencillas + 2 Elaboradas)")

if not df_all.empty:
    comida_stock = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]['nombre'].tolist()
    
    if st.button("🪄 Generar Menú Equilibrado", use_container_width=True):
        menu = generar_menu_mixto(comida_stock)
        
        for momento, platos in menu.items():
            if platos:
                st.markdown(f"### {momento}")
                cols = st.columns(2)
                # Dividimos en 2 columnas para ver las 4 opciones ordenadas
                for idx, p in enumerate(platos):
                    with cols[idx % 2]:
                        with st.expander(p['titulo']):
                            st.info(p['receta'])
