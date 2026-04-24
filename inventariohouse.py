import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario MI❤️AMOR JYI", layout="wide")

# --- LÓGICA DEL CHEF CON SENTIDO COMÚN ---
def generar_menu_coherente(productos):
    # Clasificación por comportamiento culinario
    proteinas = [p.capitalize() for p in productos if any(x in p.capitalize() for x in ["Carne", "Pollo", "Huevo", "Atun", "Cerdo", "Queso", "Mortadela", "Salchicha"])]
    carbo_secos = [p.capitalize() for p in productos if any(x in p.capitalize() for x in ["Harina pan", "Pan", "Galleta"])]
    carbo_cocidos = [p.capitalize() for p in productos if any(x in p.capitalize() for x in ["Arroz", "Pasta", "Papa", "Yuca", "Platano"])]
    harina_trigo = [p.capitalize() for p in productos if "Trigo" in p.capitalize()]

    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}
    vistas = set()

    # 1. LÓGICA DE DESAYUNO (Arepas o Panquecas)
    if harina_trigo and proteinas:
        p = proteinas[0]
        menu["☀️ DESAYUNO"].append({
            "titulo": f"Panquecas de Trigo con {p}",
            "receta": f"1. Mezcla la Harina de Trigo con agua (o leche), un huevo y una pizca de sal.\n2. Cocina círculos en un sartén caliente.\n3. Rellena o acompaña con {p}.",
            "img": ""
        })
    
    for c in carbo_secos:
        for p in proteinas:
            if f"{c}-{p}" not in vistas:
                tipo_base = "la arepa" if "Harina pan" in c else "el pan"
                menu["☀️ DESAYUNO"].append({
                    "titulo": f"{c} con {p}",
                    "receta": f"1. Prepara {tipo_base}.\n2. Si el {p} requiere cocción (como huevo o carne), prepáralo aparte.\n3. Rellena con {p} (puedes rallar el queso o ponerlo en rebanadas).",
                    "img": ""
                })
                vistas.add(f"{c}-{p}")

    # 2. LÓGICA DE ALMUERZO (Comida completa)
    for c in carbo_cocidos:
        for p in proteinas:
            if f"{c}-{p}" not in vistas and "Queso" not in p: # No solemos almorzar solo arroz con queso
                menu["🍴 ALMUERZO"].append({
                    "titulo": f"Plato de {c} con {p}",
                    "receta": f"1. Cocina el/la {c} (hirviendo en agua con sal).\n2. Prepara el {p} (frito, salteado o guisado según prefieras).\n3. Sirve caliente.",
                    "img": ""
                })
                vistas.add(f"{c}-{p}")

    # 3. LÓGICA DE CENA (Ligero)
    if proteinas:
        p = proteinas[-1]
        menu["🌙 CENA"].append({
            "titulo": f"Cena rápida de {p}",
            "receta": f"1. Prepara una porción ligera de lo que tengas disponible.\n2. Acompaña con {p} en su forma más sencilla.\n3. Una opción rápida para descansar mejor.",
            "img": ""
        })

    # Limitar y limpiar
    for k in menu: menu[k] = menu[k][:6]
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

# AGREGAR PRODUCTO
with st.expander("➕ REGISTRAR NUEVO PRODUCTO"):
    c1, c2 = st.columns(2)
    m_n, n_n = c1.selectbox("Lista", ["Comida", "Hogar", "Por Comprar"]), c1.text_input("Nombre")
    p_n, c_n = c2.number_input("Precio $", min_value=0.0), c2.number_input("Cantidad", min_value=1)
    if st.button("🚀 GUARDAR"):
        supabase.table("productos").insert({"modulo": m_n, "nombre": n_n.capitalize(), "precio": p_n, "cantidad": c_n, "created_at": datetime.now().isoformat()}).execute()
        st.success("Guardado"); time.sleep(1); st.rerun()

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
                for _, r in edit_df.iterrows(): supabase.table("productos").update({"precio": r['precio'], "cantidad": r['cantidad']}).eq("id", row['id']).execute()
                st.rerun()
            id_b = c2.number_input("ID a borrar", min_value=0, key=f"idb_{mod}", step=1)
            if c2.button(f"🗑️ Eliminar", key=f"del_{mod}"):
                supabase.table("productos").delete().eq("id", id_b).execute(); st.rerun()

# --- CHEF IA ---
st.divider()
st.subheader("👨‍🍳 Sugerencias de Comida (Lógica Real)")
if not df_all.empty:
    comida = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]['nombre'].tolist()
    if st.button("✨ Generar Menú Coherente", use_container_width=True):
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
