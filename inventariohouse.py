import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI - Sistema Blindado", layout="wide")

# --- CONEXIÓN ---
@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar_supabase()

# --- TASA BCV FIJA (PÁGINA OFICIAL) ---
TASA_BCV_FIJA = 483.87 

# --- LÓGICA DEL CHEF INTELIGENTE (4 OPCIONES POR TURNO) ---
def generar_menu_inteligente(productos):
    p_list = [str(p).lower() for p in productos]
    tiene = lambda x: any(x in item for item in p_list)
    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}

    def agregar(bloque, titulo, receta, tipo="Sencilla"):
        icono = "⚡ (Sencilla)" if tipo == "Sencilla" else "⭐ (Gourmet)"
        menu[bloque].append({"titulo": f"{icono} {titulo}", "receta": receta})

    if tiene("harina") or tiene("pan"):
        agregar("☀️ DESAYUNO", "Arepa Asada Clásica", "1. Mezcla agua con sal. 2. Añade harina y amasa 3 min. 3. Cocina 7 min por lado. 4. Rellena con queso.")
        agregar("☀️ DESAYUNO", "Tostadas Express", "1. Tuesta el pan con mantequilla. 2. Coloca queso y tapa 1 min para fundir.")
        if tiene("carne"):
            agregar("☀️ DESAYUNO", "Arepa Pelúa Gourmet", "1. Sella carne con sal/comino. 2. Rellena la arepa con carne y mucho queso rallado.", "Gourmet")
        if tiene("huevo"):
            agregar("☀️ DESAYUNO", "Perico sobre Arepa", "1. Sofríe tomate/cebolla. 2. Agrega huevos. 3. Sirve sobre arepa con mantequilla.", "Gourmet")

    if tiene("pasta") or tiene("arroz"):
        base = "Pasta" if tiene("pasta") else "Arroz"
        agregar("🍴 ALMUERZO", f"{base} al Queso", f"1. Hierve {base} con sal. 2. Escurre. 3. Agrega mantequilla y queso rallado.")
        if tiene("huevo"):
            agregar("🍴 ALMUERZO", f"Arroz a Caballo", "1. Arroz blanco + huevo frito con yema blanda arriba.")
        if tiene("carne"):
            agregar("🍴 ALMUERZO", "Salteado Criollo", "1. Carne en cubos con comino. 2. Sella 5 min. 3. Sirve con base moldeada.", "Gourmet")
            agregar("🍴 ALMUERZO", "Bistec Encebollado", "1. Bistec sazonado + aros de cebolla al sartén. 2. Acompaña con base caliente.", "Gourmet")
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

# --- BARRA LATERAL (TASA FIJA Y CONVERSOR) ---
st.sidebar.title("💰 Referencia BCV")
st.sidebar.info(f"Tasa Oficial: **{TASA_BCV_FIJA} Bs/$**")

st.sidebar.divider()
st.sidebar.subheader("🧮 Conversor Rápido")
monto_dol = st.sidebar.number_input("Monto en Dólares ($)", min_value=0.0, step=1.0, format="%.2f")
if monto_dol > 0:
    resultado_bs = monto_dol * TASA_BCV_FIJA
    st.sidebar.success(f"Equivale a: **{resultado_bs:,.2f} Bs**")

# --- INTERFAZ PRINCIPAL ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# 1. REGISTRO AL INICIO
with st.expander("➕ REGISTRAR NUEVO PRODUCTO", expanded=True):
    f1, f2 = st.columns(2)
    m_new = f1.selectbox("Destino", ["Comida", "Hogar", "Por Comprar"])
    n_new = f1.text_input("Nombre del producto")
    p_new = f2.number_input("Precio Unitario $", min_value=0.0, format="%.2f")
    c_new = f2.number_input("Cantidad", min_value=1)
    if st.button("🚀 GUARDAR"):
        if n_new:
            supabase.table("productos").insert({"modulo": m_new, "nombre": n_new.capitalize(), "precio": float(p_new), "cantidad": int(c_new), "created_at": datetime.now().isoformat()}).execute()
            st.success("Guardado"); time.sleep(1); st.rerun()

st.divider()

# CARGA DE DATOS
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

t_comida, t_hogar, t_compras = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

# --- COMIDA ---
with t_comida:
    df_c = df_all[df_all['modulo'] == 'Comida'].copy() if not df_all.empty else pd.DataFrame()
    if not df_c.empty:
        st.dataframe(df_c[["id", "nombre", "precio", "cantidad"]], use_container_width=True, hide_index=True)
        st.subheader("⚙️ Gestión")
        p_sel = st.selectbox("Producto:", df_c['nombre'].tolist())
        item = df_c[df_c['nombre'] == p_sel].iloc[0]
        
        c1, c2 = st.columns(2)
        if c1.button(f"🛒 Mover '{p_sel}' a Compras"): st.session_state.m_move = True
        if st.session_state.get('m_move'):
            if st.button(f"✅ Confirmar Envío"):
                check = supabase.table("productos").select("*").eq("modulo", "Por Comprar").eq("nombre", item['nombre']).execute()
                if check.data:
                    n_cant = int(check.data[0]['cantidad']) + int(item['cantidad'])
                    supabase.table("productos").update({"cantidad": n_cant}).eq("id", check.data[0]['id']).execute()
                    supabase.table("productos").delete().eq("id", item['id']).execute()
                else:
                    supabase.table("productos").update({"modulo": "Por Comprar"}).eq("id", item['id']).execute()
                st.session_state.m_move = False; st.rerun()

        if c2.button(f"🗑️ Eliminar '{p_sel}'"): st.session_state.m_del = True
        if st.session_state.get('m_del'):
            if st.button(f"🔥 Confirmar Eliminación"):
                supabase.table("productos").delete().eq("id", item['id']).execute()
                st.session_state.m_del = False; st.rerun()

        st.divider()
        st.subheader("👨‍🍳 Chef Inteligente")
        if st.button("🪄 Generar Menú"):
            menu = generar_menu_inteligente(df_c[df_c['cantidad'] > 0]['nombre'].tolist())
            for m, platos in menu.items():
                if platos:
                    st.write(f"### {m}")
                    cols = st.columns(2)
                    for idx, p in enumerate(platos):
                        with cols[idx % 2]:
                            with st.expander(p['titulo']): st.info(p['receta'])
    else: st.info("Sección vacía.")

# --- TABLAS FINANCIERAS ---
def render_tabla(df_sec, mod):
    if not df_sec.empty:
        df_sec['Subtotal $'] = df_sec['precio'] * df_sec['cantidad']
        df_sec['Subtotal Bs.'] = df_sec['Subtotal $'] * TASA_BCV_FIJA
        st.data_editor(df_sec[["id", "nombre", "precio", "cantidad", "Subtotal $", "Subtotal Bs."]], 
                       use_container_width=True, hide_index=True, disabled=["Subtotal $", "Subtotal Bs."], key=f"ed_{mod}")
        t_usd = df_sec['Subtotal $'].sum()
        t_bs = t_usd * TASA_BCV_FIJA
        c1, c2 = st.columns(2)
        c1.metric(f"Total {mod} ($)", f"{t_usd:.2f} $")
        c2.metric(f"Total {mod} (Bs)", f"{t_bs:,.2f} Bs")
    else: st.info(f"{mod} vacío.")

with t_hogar:
    df_h = df_all[df_all['modulo'] == 'Hogar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla(df_h, "Hogar")

with t_compras:
    df_p = df_all[df_all['modulo'] == 'Por Comprar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla(df_p, "Por Comprar")
