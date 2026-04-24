import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI - Chef Pro", layout="wide")

# --- LÓGICA DEL CHEF EQUILIBRADO ---
def generar_menu_mixto(productos):
    p_list = [str(p).lower() for p in productos]
    tiene = lambda x: any(x in item for item in p_list)
    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}

    def agregar_opcion(bloque, titulo, receta, tipo="Sencilla"):
        icono = "⚡" if tipo == "Sencilla" else "⭐"
        menu[bloque].append({"titulo": f"{icono} {titulo}", "receta": receta})

    # DESAYUNOS
    if tiene("harina de maiz") or tiene("harina pan"):
        agregar_opcion("☀️ DESAYUNO", "Arepa Básica con Queso", "1. Haz la masa con sal. 2. Cocina la arepa. 3. Rellena con queso.")
        agregar_opcion("☀️ DESAYUNO", "Arepa con Mantequilla", "1. Prepara la arepa clásica y unta mantequilla.")
        if tiene("carne"):
            agregar_opcion("☀️ DESAYUNO", "Arepa 'Pelúa' Gourmet", "1. Saltea la carne con comino. 2. Rellena con carne y queso rallado.", "Gourmet")
        if tiene("azucar"):
            agregar_opcion("☀️ DESAYUNO", "Arepitas Dulces", "1. Masa con azúcar. 2. Fríe y acompaña con queso.", "Gourmet")

    # ALMUERZOS
    if tiene("pasta") or tiene("arroz"):
        base = "Pasta" if tiene("pasta") else "Arroz"
        agregar_opcion("🍴 ALMUERZO", f"{base} con Queso", f"1. Cocina {base}. 2. Agrega queso arriba.")
        if tiene("carne"):
            agregar_opcion("🍴 ALMUERZO", f"Bistec con {base}", "1. Bistec a la plancha con sal y acompañante.")
            agregar_opcion("🍴 ALMUERZO", f"{base} Salteada al Comino", "1. Saltea carne en cubos con comino e integra la base.", "Gourmet")

    # CENAS
    if tiene("pan"):
        agregar_opcion("🌙 CENA", "Tostado de Queso", "1. Pan con queso al sartén hasta que dore.")
    if tiene("huevo") or tiene("queso"):
        p = "Huevo" if tiene("huevo") else "Queso"
        agregar_opcion("🌙 CENA", f"Revoltillo de {p}", f"1. Prepara {p} rápido y sirve.")
        agregar_opcion("🌙 CENA", f"Bruschettas {p} Bistro", "1. Pan tostado con mantequilla, comino y ingrediente encima.", "Gourmet")

    return menu

# --- CONEXIÓN ---
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

st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# --- REGISTRO ---
with st.expander("➕ REGISTRAR NUEVO PRODUCTO"):
    c1, c2 = st.columns(2)
    m_n = c1.selectbox("Lista", ["Comida", "Hogar", "Por Comprar"])
    n_n = c1.text_input("Nombre")
    p_n, c_n = c2.number_input("Precio $", min_value=0.0), c2.number_input("Cantidad", min_value=0)
    if st.button("🚀 GUARDAR"):
        if n_n:
            supabase.table("productos").insert({"modulo": m_n, "nombre": n_n.capitalize(), "precio": p_n, "cantidad": c_n, "created_at": datetime.now().isoformat()}).execute()
            st.success("Guardado"); time.sleep(1); st.rerun()

# --- DATOS ---
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

# --- PESTAÑAS ---
t_comida, t_hogar, t_compras = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

# PESTAÑA COMIDA (Única donde aparece el Chef)
with t_comida:
    df_c = df_all[df_all['modulo'] == 'Comida'].copy() if not df_all.empty else pd.DataFrame()
    if not df_c.empty:
        ed_c = st.data_editor(df_c[["id", "nombre", "precio", "cantidad"]], key="ed_c", use_container_width=True, hide_index=True)
        c1, c2 = st.columns(2)
        if c1.button("💾 Actualizar Comida"):
            for _, r in ed_c.iterrows():
                supabase.table("productos").update({"precio": r['precio'], "cantidad": r['cantidad']}).eq("id", r['id']).execute()
            st.rerun()
        id_b = c2.number_input("ID a borrar", min_value=0, key="del_c")
        if c2.button("🗑️ Eliminar"):
            supabase.table("productos").delete().eq("id", id_b).execute(); st.rerun()
        
        # --- EL CHEF AHORA VIVE AQUÍ ADENTRO ---
        st.divider()
        st.subheader("👨‍🍳 Ideas del Chef (Solo para Comida)")
        comida_stock = df_c[df_c['cantidad'] > 0]['nombre'].tolist()
        
        if st.button("🪄 Generar Menú (Sencillo + Gourmet)", use_container_width=True):
            menu = generar_menu_mixto(comida_stock)
            for momento, platos in menu.items():
                if platos:
                    st.markdown(f"### {momento}")
                    cols = st.columns(2)
                    for idx, p in enumerate(platos):
                        with cols[idx % 2]:
                            with st.expander(p['titulo']):
                                st.info(p['receta'])
    else:
        st.info("No hay comida registrada.")

# PESTAÑA HOGAR
with t_hogar:
    df_h = df_all[df_all['modulo'] == 'Hogar'].copy() if not df_all.empty else pd.DataFrame()
    if not df_h.empty:
        ed_h = st.data_editor(df_h[["id", "nombre", "precio", "cantidad"]], key="ed_h", use_container_width=True, hide_index=True)
        if st.button("💾 Actualizar Hogar"):
            for _, r in ed_h.iterrows():
                supabase.table("productos").update({"precio": r['precio'], "cantidad": r['cantidad']}).eq("id", r['id']).execute()
            st.rerun()
    else:
        st.info("Sección de hogar vacía.")

# PESTAÑA POR COMPRAR
with t_compras:
    df_p = df_all[df_all['modulo'] == 'Por Comprar'].copy() if not df_all.empty else pd.DataFrame()
    if not df_p.empty:
        st.data_editor(df_p[["id", "nombre", "precio", "cantidad"]], key="ed_p", use_container_width=True, hide_index=True)
    else:
        st.info("Nada pendiente por comprar.")
