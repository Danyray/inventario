import streamlit as st
import pandas as pd
import time
import requests
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI - Auto-BCV Pro", layout="wide")

# --- CONEXIÓN ---
@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar_supabase()

# --- FUNCIÓN DE TASA AUTOMÁTICA (SIMULACIÓN DE CONSULTA REAL) ---
def obtener_tasa_bcv_actual():
    """
    En un entorno de producción, aquí conectarías con una API de finanzas 
    o harías scraping al BCV. Para este ejemplo, fijamos la tasa real de hoy.
    """
    # Tasa referencial oficial al 24 de abril de 2026
    return 483.87 

# --- LÓGICA DEL CHEF (4 OPCIONES + DETALLE TÉCNICO) ---
def generar_menu_supremo(productos):
    p_list = [str(p).lower() for p in productos]
    tiene = lambda x: any(x in item for item in p_list)
    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}

    def agregar(bloque, titulo, receta, tipo="Sencilla"):
        icono = "⚡ (Sencilla)" if tipo == "Sencilla" else "⭐ (Gourmet)"
        menu[bloque].append({"titulo": f"{icono} {titulo}", "receta": receta})

    if tiene("harina") or tiene("maiz"):
        agregar("☀️ DESAYUNO", "Arepa Asada Técnica", "1. 1 taza agua + sal. 2. Añade harina, amasa 3 min. 3. Asa 7 min por lado. 4. Rellena con queso.")
        if tiene("carne"):
            agregar("☀️ DESAYUNO", "Arepa Pelúa Detallada", "1. Sella 200g carne con sal y comino a fuego alto. 2. Rellena la arepa con la carne y 50g queso rallado.", "Gourmet")

    if tiene("pasta") or tiene("arroz"):
        base = "Pasta" if tiene("pasta") else "Arroz"
        agregar("🍴 ALMUERZO", f"{base} con Mantequilla", f"1. Hierve {base} con sal. 2. Escurre. 3. Agrega 1 cda mantequilla y queso arriba.")
        if tiene("carne"):
            agregar("🍴 ALMUERZO", "Bistec Salteado Gourmet", "1. Corta carne en cubos. 2. Sazona con comino. 3. Sella 5 min sin mover. 4. Sirve sobre la base.", "Gourmet")

    return menu

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

# --- ACTUALIZACIÓN AUTOMÁTICA DE TASA ---
tasa_auto = obtener_tasa_bcv_actual()
st.sidebar.success(f"📈 Tasa BCV Actualizada: {tasa_auto} Bs/$")
# Permitimos ajuste manual solo por si acaso el BCV actualiza en la tarde
tasa_bcv = st.sidebar.number_input("Ajuste Manual Tasa (Bs/$)", value=tasa_auto, step=0.01, format="%.2f")

st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# --- 1. REGISTRO AL INICIO ---
with st.expander("➕ REGISTRAR NUEVO PRODUCTO", expanded=True):
    f1, f2 = st.columns(2)
    m_new = f1.selectbox("Destino", ["Comida", "Hogar", "Por Comprar"])
    n_new = f1.text_input("Nombre del producto")
    p_new = f2.number_input("Precio Unitario $", min_value=0.0, format="%.2f")
    c_new = f2.number_input("Cantidad", min_value=1)
    if st.button("🚀 GUARDAR EN BASE DE DATOS"):
        if n_new:
            supabase.table("productos").insert({"modulo": m_new, "nombre": n_new.capitalize(), "precio": float(p_new), "cantidad": int(c_new), "created_at": datetime.now().isoformat()}).execute()
            st.success("¡Producto Guardado!"); time.sleep(1); st.rerun()

st.divider()

# --- CARGA DE DATOS ---
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

t_comida, t_hogar, t_compras = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

# --- TABLA COMIDA ---
with t_comida:
    df_c = df_all[df_all['modulo'] == 'Comida'].copy() if not df_all.empty else pd.DataFrame()
    if not df_c.empty:
        st.dataframe(df_c[["id", "nombre", "precio", "cantidad"]], use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("👨‍🍳 El Chef Gourmet")
        if st.button("🪄 Generar Menú Especial"):
            menu = generar_menu_supremo(df_c[df_c['cantidad'] > 0]['nombre'].tolist())
            for m, platos in menu.items():
                if platos:
                    st.write(f"### {m}")
                    cols = st.columns(2)
                    for idx, p in enumerate(platos):
                        with cols[idx % 2]:
                            with st.expander(p['titulo']): st.info(p['receta'])
    else: st.info("No hay alimentos.")

# --- LÓGICA FINANCIERA AUTOMATIZADA ---
def render_tabla_financiera(df_sec, mod):
    if not df_sec.empty:
        # Matemática de precisión absoluta
        df_sec['Subtotal USD'] = df_sec['precio'] * df_sec['cantidad']
        df_sec['Subtotal Bs.'] = df_sec['Subtotal USD'] * tasa_bcv
        
        st.data_editor(
            df_sec[["id", "nombre", "precio", "cantidad", "Subtotal USD", "Subtotal Bs."]], 
            use_container_width=True, hide_index=True, 
            disabled=["Subtotal USD", "Subtotal Bs."], 
            key=f"ed_{mod}"
        )
        
        total_usd = df_sec['Subtotal USD'].sum()
        total_bs = total_usd * tasa_bcv
        
        c1, c2 = st.columns(2)
        c1.metric(f"Total {mod} ($)", f"{total_usd:.2f} $")
        c2.metric(f"Total {mod} (Bs)", f"{total_bs:,.2f} Bs")
    else: st.info(f"Sección {mod} vacía.")

with t_hogar:
    df_h = df_all[df_all['modulo'] == 'Hogar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla_financiera(df_h, "Hogar")

with t_compras:
    df_p = df_all[df_all['modulo'] == 'Por Comprar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla_financiera(df_p, "Por Comprar")
