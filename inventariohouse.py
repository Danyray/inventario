import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario MI❤️AMOR JYI", layout="wide")

# --- LÓGICA DEL CHEF PROFESIONAL (SIN REPETICIONES) ---
def generar_menu_completo(productos):
    # Clasificación precisa
    proteinas = sorted(list(set([p.capitalize() for p in productos if any(x in p.capitalize() for x in ["Carne", "Pollo", "Huevo", "Atun", "Cerdo", "Queso", "Mortadela", "Salchicha"])])))
    harina_pan = [p.capitalize() for p in productos if "Harina pan" in p.capitalize()]
    harina_trigo = [p.capitalize() for p in productos if "Trigo" in p.capitalize()]
    carbo_cocidos = [p.capitalize() for p in productos if any(x in p.capitalize() for x in ["Arroz", "Pasta", "Papa", "Yuca", "Platano"])]
    pan = [p.capitalize() for p in productos if "Pan" in p.capitalize() and "Harina" not in p.capitalize()]

    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}
    
    # --- DESAYUNOS (SIN DUPLICADOS) ---
    bases_desayuno = harina_pan + harina_trigo + pan
    for b in bases_desayuno:
        for p in proteinas:
            if "Trigo" in b:
                t, r, img = f"Panquecas con {p}", f"1. Mezcla {b} con agua y sal.\n2. Cocina círculos en sartén.\n3. Sirve con {p}.", ""
            elif "Harina pan" in b:
                t, r, img = f"Arepa con {p}", f"1. Amasa {b} con agua.\n2. Cocina en budare.\n3. Rellena con {p}.", ""
            else:
                t, r, img = f"Sándwich de {p}", f"1. Tuesta el {b}.\n2. Rellena con {p} y un toque de mantequilla.", ""
            
            if len(menu["☀️ DESAYUNO"]) < 6:
                menu["☀️ DESAYUNO"].append({"titulo": t, "receta": r, "img": img})

    # --- ALMUERZOS (LÓGICA REAL) ---
    # Filtramos proteínas pesadas para el almuerzo
    prot_fuerte = [pr for pr in proteinas if "Queso" not in pr] or proteinas
    for c in carbo_cocidos:
        for p in prot_fuerte:
            if len(menu["🍴 ALMUERZO"]) < 6:
                menu["🍴 ALMUERZO"].append({
                    "titulo": f"{c} con {p}",
                    "receta": f"1. Hierve el/la {c} con sal.\n2. Prepara el {p} salteado o a la plancha.\n3. Sirve caliente.",
                    "img": ""
                })

    # --- CENAS (LIGERO Y DIFERENTE) ---
    for p in reversed(proteinas): # Empezamos por el final para variar
        base_cena = pan if pan else (carbo_cocidos if carbo_cocidos else ["una porción ligera"])
        for b in base_cena:
            if len(menu["🌙 CENA"]) < 6:
                menu["🌙 CENA"].append({
                    "titulo": f"Cena: {p} con {b}",
                    "receta": f"1. Prepara {b} en porción pequeña.\n2. Acompaña con {p} preparado de forma sencilla.",
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

# --- INTERFAZ ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# AGREGAR PRODUCTO
with st.expander("➕ REGISTRAR NUEVO PRODUCTO"):
    c1, c2 = st.columns(2)
    m_n, n_n = c1.selectbox("Lista", ["Comida", "Hogar", "Por Comprar"]), c1.text_input("Nombre")
    p_n, c_n = c2.number_input("Precio $", min_value=0.0), c2.number_input("Cantidad", min_value=1)
    if st.button("🚀 GUARDAR"):
        if n_n:
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
                for _, r in edit_df.iterrows(): 
                    supabase.table("productos").update({"precio": r['precio'], "cantidad": r['cantidad']}).eq("id", r['id']).execute()
                st.rerun()
            id_b = c2.number_input("ID a borrar", min_value=0, key=f"idb_{mod}", step=1)
            if c2.button(f"🗑️ Eliminar", key=f"del_{mod}"):
                supabase.table("productos").delete().eq("id", id_b).execute(); st.rerun()

# --- CHEF IA ---
st.divider()
st.subheader("👨‍🍳 Menú del Día (Opciones Únicas)")
if not df_all.empty:
    comida_list = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]['nombre'].tolist()
    if st.button("🪄 Generar Menú Sin Repeticiones", use_container_width=True):
        menu = generar_menu_completo(comida_list)
        for momento, platos in menu.items():
            if platos:
                st.markdown(f"## {momento}")
                for i in range(0, len(platos), 3):
                    cols = st.columns(3)
                    for j in range(3):
                        if i + j < len(platos):
                            p = platos[i+j]
                            with cols[j]:
                                with st.expander(f"🍴 {p['titulo']}"):
                                    st.write(p['img'])
                                    st.info(p['receta'])
