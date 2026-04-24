import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario Gourmet JYI", layout="wide")

# --- LÓGICA DEL CHEF CREATIVO (RECETAS ELABORADAS) ---
def generar_menu_elaborado(productos):
    # Clasificación avanzada
    prot = [p.capitalize() for p in productos if any(x in p.capitalize() for x in ["Carne", "Pollo", "Huevo", "Atun", "Cerdo", "Queso", "Mortadela", "Salchicha"])]
    carb_base = [p.capitalize() for p in productos if any(x in p.capitalize() for x in ["Harina pan", "Trigo", "Pan", "Arroz", "Pasta", "Papa", "Yuca", "Platano"])]
    extras = [p.capitalize() for p in productos if any(x in p.capitalize() for x in ["Granola", "Mantequilla", "Mayonesa", "Salsa", "Azucar", "Leche"])]

    menu = {"✨ DESAYUNOS CREATIVOS": [], "👨‍🍳 ALMUERZOS ESPECIALES": [], "🌙 CENAS GOURMET": []}
    
    # --- 1. DESAYUNOS ELABORADOS ---
    if "Trigo" in str(carb_base) and "Granola" in str(extras):
        menu["✨ DESAYUNOS CREATIVOS"].append({
            "titulo": "Panquecas de Trigo con Topping de Granola Crocante",
            "receta": "1. Prepara panquecas esponjosas con la Harina de Trigo.\n2. En un sartén, tuesta la Granola con un poco de mantequilla y azúcar para caramelizarla.\n3. Sirve las panquecas con el crocante arriba y un toque de queso fresco.",
            "img": ""
        })
    
    if "Harina pan" in str(carb_base) and "Carne" in str(prot):
        menu["✨ DESAYUNOS CREATIVOS"].append({
            "titulo": "Arepas con Carne Salteada al Estilo Pelúa",
            "receta": "1. Prepara arepas bien tostadas.\n2. Corta la carne en tiritas muy finas y saltéala a fuego alto con grasa hasta que dore.\n3. Rellena mezclando la carne caliente con abundante queso rallado para que se funda.",
            "img": ""
        })

    # --- 2. ALMUERZOS ELABORADOS ---
    if "Pasta" in str(carb_base) and "Atun" in str(prot):
        menu["👨‍🍳 ALMUERZOS ESPECIALES"].append({
            "titulo": "Pasta de la Casa al Gratín de Atún",
            "receta": "1. Cocina la pasta al dente.\n2. Mezcla el atún con un toque de mayonesa y mantequilla.\n3. Integra todo con la pasta y, si puedes, lleva al sartén para que el queso forme una costra dorada.",
            "img": ""
        })

    if "Arroz" in str(carb_base) and "Pollo" in str(prot):
        menu["👨‍🍳 ALMUERZOS ESPECIALES"].append({
            "titulo": "Arroz Salteado Tipo Oriental con Pollo",
            "receta": "1. Cocina el arroz y déjalo enfriar.\n2. Saltea el pollo en cubos pequeños con fuego máximo.\n3. Agrega el arroz al sartén del pollo y mezcla vigorosamente para que absorba el sabor del dorado.",
            "img": ""
        })

    # --- 3. CENAS ELABORADOS ---
    if "Pan" in str(carb_base) and "Huevo" in str(prot):
        menu["🌙 CENAS GOURMET"].append({
            "titulo": "Tostadas JYI con Huevo Poché Estilo Bistro",
            "receta": "1. Tuesta el pan con abundante mantequilla por ambos lados.\n2. Prepara un huevo suave (término medio).\n3. Coloca el huevo sobre el pan y deja que la yema bañe la tostada al cortarlo.",
            "img": ""
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
    st.title("🔐 Acceso")
    with st.form("login"):
        u, p = st.text_input("Usuario").lower().strip(), st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar") and u in ["ignacio", "joseilys"] and p == "yosa0325":
            st.session_state.auth, st.session_state.user = True, u.capitalize()
            st.rerun()
    st.stop()

# --- APP ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# TABLAS
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

t1, t2, t3 = st.tabs(["🍕 DESPENSA", "🏠 HOGAR", "🛒 COMPRAS"])
with t1:
    if not df_all.empty:
        df_c = df_all[df_all['modulo'] == 'Comida']
        edit_df = st.data_editor(df_c[["id", "nombre", "precio", "cantidad"]], use_container_width=True, hide_index=True)
        if st.button("💾 Guardar Cambios"):
            for _, r in edit_df.iterrows():
                supabase.table("productos").update({"precio": r['precio'], "cantidad": r['cantidad']}).eq("id", r['id']).execute()
            st.rerun()

# --- SECCIÓN GOURMET ---
st.divider()
st.subheader("👨‍🍳 El Chef Sugiere: Recetas Elaboradas")
if not df_all.empty:
    comida_disponible = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]['nombre'].tolist()
    if st.button("🪄 Descubrir Platos Especiales", use_container_width=True):
        recetas = generar_menu_elaborado(comida_disponible)
        for cat, platos in recetas.items():
            if platos:
                st.markdown(f"### {cat}")
                for p in platos:
                    with st.expander(f"⭐ {p['titulo']}"):
                        col1, col2 = st.columns([1, 2])
                        with col1: st.write(p['img'])
                        with col2: 
                            st.write("**Técnica y Preparación:**")
                            st.success(p['receta'])
