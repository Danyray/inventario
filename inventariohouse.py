import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI - Home", layout="wide")

# --- LÓGICA DEL CHEF CREATIVO (RECETAS ELABORADAS) ---
def generar_menu_elaborado(productos):
    # Limpiamos y clasificamos
    prod_caps = [str(p).capitalize() for p in productos]
    
    prot = [p for p in prod_caps if any(x in p for x in ["Carne", "Pollo", "Huevo", "Atun", "Cerdo", "Queso", "Mortadela", "Salchicha"])]
    carb = [p for p in prod_caps if any(x in p for x in ["Harina pan", "Trigo", "Pan", "Arroz", "Pasta", "Papa", "Yuca", "Platano"])]
    ext = [p for p in prod_caps if any(x in p for x in ["Granola", "Mantequilla", "Mayonesa", "Salsa", "Azucar", "Leche"])]

    menu = {"✨ DESAYUNOS CREATIVOS": [], "👨‍🍳 ALMUERZOS ESPECIALES": [], "🌙 CENAS GOURMET": []}
    
    # 1. DESAYUNOS
    if any("Trigo" in c for c in carb) and any("Granola" in e for e in ext):
        menu["✨ DESAYUNOS CREATIVOS"].append({
            "titulo": "Panquecas Gourmet con Crocante de Granola",
            "receta": "1. Haz la mezcla de Harina de Trigo. 2. En un sartén, derrite mantequilla con azúcar y tuesta la Granola hasta que caramelice. 3. Sirve las panquecas bañadas con el crocante dulce.",
            "img": ""
        })
    
    if any("Harina pan" in c for c in carb) and any("Carne" in p for p in prot):
        menu["✨ DESAYUNOS CREATIVOS"].append({
            "titulo": "Arepas Pelúas con Carne Salteada",
            "receta": "1. Cocina la carne en tiritas con un toque de grasa hasta que esté crujiente. 2. Prepara arepas bien tostadas. 3. Rellena mezclando la carne caliente con queso rallado para que se funda por completo.",
            "img": ""
        })

    # 2. ALMUERZOS
    if any("Arroz" in c for c in carb) and any("Pollo" in p for p in prot):
        menu["👨‍🍳 ALMUERZOS ESPECIALES"].append({
            "titulo": "Bowl de Arroz Tostado con Pollo al Grill",
            "receta": "1. Saltea el pollo en cubos con fuego alto. 2. Agrega el arroz ya cocido al sartén para que se tueste con el jugo del pollo. 3. Sirve con un toque de mantequilla para dar brillo y cremosidad.",
            "img": ""
        })
    
    if any("Pasta" in c for c in carb) and any("Atun" in p for p in prot):
        menu["👨‍🍳 ALMUERZOS ESPECIALES"].append({
            "titulo": "Pasta de la Casa al Gratín de Atún",
            "receta": "1. Cocina la pasta al dente. 2. Mezcla el atún con un toque de mayonesa. 3. Integra todo en un sartén caliente y agrega queso encima para que se gratine ligeramente.",
            "img": ""
        })

    # 3. CENAS
    if any("Pan" in c for c in carb) and any("Huevo" in p for p in prot):
        menu["🌙 CENAS GOURMET"].append({
            "titulo": "Bruschettas Caseras con Huevo y Mantequilla",
            "receta": "1. Rebana el pan y tuéstalo con mucha mantequilla hasta que esté dorado. 2. Prepara un huevo a fuego lento para que quede tierno. 3. Colócalo sobre el pan con una pizca de sal.",
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
    st.title("🔐 Acceso al Sistema")
    with st.form("login"):
        u, p = st.text_input("Usuario").lower().strip(), st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar") and u in ["ignacio", "joseilys"] and p == "yosa0325":
            st.session_state.auth, st.session_state.user = True, u.capitalize()
            st.rerun()
    st.stop()

# --- APP PRINCIPAL ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# --- REUPERADA: BARRA DE AGREGAR PRODUCTOS ---
with st.expander("➕ AGREGAR NUEVO PRODUCTO", expanded=False):
    c1, c2 = st.columns(2)
    mod_n = c1.selectbox("Lista", ["Comida", "Hogar", "Por Comprar"])
    nom_n = c1.text_input("Nombre del producto")
    pre_n = c2.number_input("Precio $", min_value=0.0, step=0.1)
    can_n = c2.number_input("Cantidad", min_value=1, step=1)
    if st.button("🚀 GUARDAR PRODUCTO", use_container_width=True):
        if nom_n:
            supabase.table("productos").insert({
                "modulo": mod_n, "nombre": nom_n.capitalize(), 
                "precio": pre_n, "cantidad": can_n, "created_at": datetime.now().isoformat()
            }).execute()
            st.success("¡Guardado correctamente!")
            time.sleep(1)
            st.rerun()

# --- VISUALIZACIÓN Y TABLAS ---
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

tabs = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])
listas = ["Comida", "Hogar", "Por Comprar"]

for i, tab in enumerate(tabs):
    with tab:
        df = df_all[df_all['modulo'] == listas[i]].copy() if not df_all.empty else pd.DataFrame()
        if not df.empty:
            # Editor de datos
            edit_df = st.data_editor(df[["id", "nombre", "precio", "cantidad"]], key=f"ed_{listas[i]}", use_container_width=True, hide_index=True)
            
            col_save, col_del = st.columns(2)
            if col_save.button(f"💾 Actualizar {listas[i]}", key=f"btn_upd_{listas[i]}"):
                for _, r in edit_df.iterrows():
                    supabase.table("productos").update({"precio": r['precio'], "cantidad": r['cantidad']}).eq("id", r['id']).execute()
                st.rerun()
            
            id_borrar = col_del.number_input("ID a borrar", min_value=0, key=f"del_id_{listas[i]}", step=1)
            if col_del.button(f"🗑️ Eliminar ID {id_borrar}", key=f"btn_del_{listas[i]}"):
                supabase.table("productos").delete().eq("id", id_borrar).execute()
                st.rerun()
        else:
            st.info("No hay productos registrados en esta sección.")

# --- SECCIÓN CHEF GOURMET ---
st.divider()
st.subheader("👨‍🍳 Ideas del Chef (Mezclas Elaboradas)")

if not df_all.empty:
    comida_actual = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]['nombre'].tolist()
    
    if st.button("🪄 Generar Menú Especial", use_container_width=True):
        recetas = generar_menu_elaborado(comida_actual)
        
        found = False
        for cat, platos in recetas.items():
            if platos:
                found = True
                st.markdown(f"### {cat}")
                for p in platos:
                    with st.expander(f"⭐ {p['titulo']}"):
                        c1, c2 = st.columns([1, 2])
                        with c1: st.write(p['img'])
                        with c2:
                            st.write("**Técnica y Preparación:**")
                            st.success(p['receta'])
        
        if not found:
            st.warning("El Chef no encontró combinaciones gourmet con los ingredientes actuales. ¡Intenta agregar más variedad!")
