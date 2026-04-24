import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario MI❤️AMOR JYI", layout="wide")

# --- LÓGICA DEL CHEF REAL (SIN MEZCLAS LOCAS) ---
def generar_menu_coherente(productos):
    # Clasificación manual para evitar desastres culinarios
    categorias = {
        "proteinas": ["Pollo", "Carne", "Huevo", "Atun", "Cerdo", "Queso", "Mortadela"],
        "carbohidratos": ["Arroz", "Pasta", "Harina pan", "Pan", "Papa", "Platano"],
        "complementos": ["Mantequilla", "Mayonesa", "Salsa", "Granola", "Leche"]
    }
    
    disponibles = {"p": [], "c": [], "acc": []}
    for p in productos:
        p_name = p.capitalize()
        if any(x in p_name for x in categorias["proteinas"]): disponibles["p"].append(p_name)
        elif any(x in p_name for x in categorias["carbohidratos"]): disponibles["c"].append(p_name)
        else: disponibles["acc"].append(p_name)

    # Definimos 5 platos con lógica venezolana/casera
    prot = disponibles["p"][0] if disponibles["p"] else "Huevo"
    carb = disponibles["c"][0] if disponibles["c"] else "Arroz"
    
    ideas = [
        {
            "titulo": f"🍛 Almuerzo Criollo: {prot} con {carb}",
            "receta": f"1. Cocina el {carb} en agua con sal hasta que esté tierno.\n2. Prepara el {prot} a la plancha o frito con un toque de aceite.\n3. Sirve caliente y agrega un toque de mantequilla al {carb}.",
            "img": ""
        },
        {
            "titulo": f"🫓 Arepas Rellenas de {prot}",
            "receta": f"1. Haz la masa con Harina Pan y agua.\n2. Cocina las arepas hasta que suenen 'hueco'.\n3. Abre y rellena con {prot} y un poco de queso o mantequilla.",
            "img": ""
        },
        {
            "titulo": f"🍝 Pasta con {prot} en Salsa",
            "receta": f"1. Hierve la pasta al dente.\n2. Pica el {prot} en trozos pequeños y saltéalo.\n3. Mezcla todo con un chorrito de aceite o salsa para dar jugosidad.",
            "img": ""
        },
        {
            "titulo": f"🥪 Sándwich o Pan con {prot}",
            "receta": f"1. Tuesta el pan con un poco de mantequilla.\n2. Agrega el {prot} (mortadela, queso o huevo).\n3. Añade una pizca de mayonesa si tienes disponible.",
            "img": ""
        },
        {
            "titulo": f"🥣 Desayuno Energético (Granola)",
            "receta": "1. Sirve la Granola en un bol.\n2. Acompáñala con leche o cómela sola como snack crujiente.\n3. Ideal para antes de entrenar o empezar el día.",
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
            else: st.error("Clave incorrecta")
    st.stop()

# --- APP PRINCIPAL ---
st.title(f"📦 INVENTARIO JYI - Bienvenido {st.session_state.user}")

# FORMULARIO AGREGAR
with st.expander("➕ AGREGAR NUEVO PRODUCTO", expanded=False):
    c1, c2 = st.columns(2)
    mod = c1.selectbox("Lista", ["Comida", "Hogar", "Por Comprar"])
    nom = c1.text_input("Nombre del producto")
    pre = c2.number_input("Precio $", min_value=0.0, step=0.1)
    can = c2.number_input("Cantidad", min_value=1, step=1)
    if st.button("🚀 GUARDAR EN NUBE", use_container_width=True):
        if nom:
            supabase.table("productos").insert({"modulo": mod, "nombre": nom.capitalize(), "precio": pre, "cantidad": can, "created_at": datetime.now().isoformat()}).execute()
            st.success("Registrado!")
            time.sleep(1)
            st.rerun()

# TABLAS
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

tabs = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])
for i, tab in enumerate(tabs):
    m = ["Comida", "Hogar", "Por Comprar"][i]
    with tab:
        df = df_all[df_all['modulo'] == m].copy() if not df_all.empty else pd.DataFrame()
        if not df.empty:
            edit_df = st.data_editor(df[["id", "nombre", "precio", "cantidad"]], key=f"e_{m}", use_container_width=True, hide_index=True)
            c1, c2 = st.columns(2)
            if c1.button(f"💾 Guardar {m}", key=f"b_{m}"):
                for _, row in edit_df.iterrows():
                    supabase.table("productos").update({"precio": row['precio'], "cantidad": row['cantidad']}).eq("id", row['id']).execute()
                st.rerun()
            id_del = c2.number_input("ID a borrar", min_value=0, key=f"d_{m}", step=1)
            if c2.button(f"🗑️ Borrar ID {id_del}", key=f"bd_{m}"):
                supabase.table("productos").delete().eq("id", id_del).execute()
                st.rerun()

# CHEF IA DEFINITIVO
st.divider()
st.subheader("👨‍🍳 ¿Qué almorzamos hoy?")
if not df_all.empty:
    ing = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]['nombre'].tolist()
    if ing:
        if st.button("🪄 Generar 5 Ideas Reales", use_container_width=True):
            recetas = generar_menu_coherente(ing)
            for r in recetas:
                with st.expander(r['titulo']):
                    c1, c2 = st.columns([1, 2])
                    with c1: st.write(r['img'])
                    with c2: 
                        st.write("**Instrucciones:**")
                        st.info(r['receta'])
                        
