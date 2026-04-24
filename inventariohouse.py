import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI - Chef & Gestión Pro", layout="wide")

# --- CONEXIÓN ---
@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar_supabase()

# --- LÓGICA DEL CHEF INTELIGENTE (4 OPCIONES POR TURNO) ---
def generar_menu_inteligente(productos):
    p_list = [str(p).lower() for p in productos]
    tiene = lambda x: any(x in item for item in p_list)
    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}

    def agregar(bloque, titulo, receta, tipo="Sencilla"):
        icono = "⚡ (Sencilla)" if tipo == "Sencilla" else "⭐ (Gourmet)"
        menu[bloque].append({"titulo": f"{icono} {titulo}", "receta": receta})

    # --- DESAYUNOS ---
    if tiene("harina") or tiene("pan"):
        agregar("☀️ DESAYUNO", "Arepa Asada Clásica", "1. Mezcla agua tibia con sal. 2. Añade harina y amasa 3 min. 3. Forma discos de 2cm. 4. Cocina 7 min por lado a fuego medio. 5. Rellena con queso.")
        agregar("☀️ DESAYUNO", "Tostadas de Queso Express", "1. Tuesta el pan en sartén con mantequilla. 2. Coloca láminas de queso. 3. Tapa 1 min para que el vapor funda el queso.")
        if tiene("carne"):
            agregar("☀️ DESAYUNO", "Arepa Pelúa Gourmet", "1. Sella la carne con sal y comino a fuego alto. 2. Prepara la arepa según pasos previos. 3. Mezcla la carne con abundante queso rallado para el relleno.", "Gourmet")
        if tiene("huevo"):
            agregar("☀️ DESAYUNO", "Perico Gourmet sobre Arepa", "1. Sofríe cebolla y tomate. 2. Agrega huevos y sal. 3. Cocina hasta que estén jugosos. 4. Sirve sobre la arepa abierta con mantequilla.", "Gourmet")

    # --- ALMUERZOS ---
    if tiene("pasta") or tiene("arroz"):
        base = "Pasta" if tiene("pasta") else "Arroz"
        agregar("🍴 ALMUERZO", f"{base} al Queso", f"1. Hierve {base} con sal (Pasta 9 min / Arroz 20 min). 2. Escurre. 3. Mezcla con mantequilla y queso rallado inmediatamente.")
        if tiene("huevo"):
            agregar("🍴 ALMUERZO", f"Arroz con Huevo a Caballo", "1. Prepara arroz blanco. 2. Fríe un huevo con la yema blanda. 3. Coloca sobre el arroz caliente y rompe la yema para que bañe el grano.")
        if tiene("carne"):
            agregar("🍴 ALMUERZO", "Salteado Criollo al Comino", f"1. Corta carne en cubos. 2. Sazona con comino y sal. 3. Sella en sartén humeante 5 min. 4. Sirve con una porción de {base} moldeada.", "Gourmet")
            agregar("🍴 ALMUERZO", f"Bistec Encebollado con {base}", f"1. Cocina el bistec sazonado. 2. Agrega aros de cebolla al sartén. 3. Sirve junto a la {base} caliente.", "Gourmet")

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

# --- TASA BCV AUTOMÁTICA (REFERENCIA 2026) ---
st.sidebar.title("💰 Monitor BCV")
tasa_bcv = st.sidebar.number_input("Tasa BCV (Bs/$)", min_value=1.0, value=483.87, step=0.01, format="%.2f")

st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# --- 1. REGISTRO AL INICIO ---
with st.expander("➕ REGISTRAR NUEVO PRODUCTO", expanded=True):
    f1, f2 = st.columns(2)
    m_new = f1.selectbox("Destino", ["Comida", "Hogar", "Por Comprar"])
    n_new = f1.text_input("Nombre del producto")
    p_new = f2.number_input("Precio Unitario $", min_value=0.0, format="%.2f")
    c_new = f2.number_input("Cantidad", min_value=1)
    if st.button("🚀 GUARDAR REGISTRO"):
        if n_new:
            supabase.table("productos").insert({"modulo": m_new, "nombre": n_new.capitalize(), "precio": float(p_new), "cantidad": int(c_new), "created_at": datetime.now().isoformat()}).execute()
            st.success("Guardado"); time.sleep(1); st.rerun()

st.divider()

# --- CARGA DE DATOS ---
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

t_comida, t_hogar, t_compras = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

# --- PESTAÑA COMIDA (GESTIÓN + CHEF) ---
with t_comida:
    df_c = df_all[df_all['modulo'] == 'Comida'].copy() if not df_all.empty else pd.DataFrame()
    if not df_c.empty:
        st.dataframe(df_c[["id", "nombre", "precio", "cantidad"]], use_container_width=True, hide_index=True)
        
        st.write("---")
        st.subheader("⚙️ Gestión de Inventario")
        p_sel = st.selectbox("Selecciona un producto:", df_c['nombre'].tolist(), key="sel_comida")
        item = df_c[df_c['nombre'] == p_sel].iloc[0]
        
        c1, c2 = st.columns(2)
        if c1.button(f"🛒 Enviar '{p_sel}' a Compras"):
            st.session_state.confirm_move = True
        
        if st.session_state.get('confirm_move'):
            st.warning(f"¿Seguro que quieres mover {p_sel} a la lista de compras?")
            if st.button("✅ SÍ, MOVER AHORA"):
                check = supabase.table("productos").select("*").eq("modulo", "Por Comprar").eq("nombre", item['nombre']).execute()
                if check.data:
                    n_cant = int(check.data[0]['cantidad']) + int(item['cantidad'])
                    supabase.table("productos").update({"cantidad": n_cant}).eq("id", check.data[0]['id']).execute()
                    supabase.table("productos").delete().eq("id", item['id']).execute()
                else:
                    supabase.table("productos").update({"modulo": "Por Comprar"}).eq("id", item['id']).execute()
                st.session_state.confirm_move = False; st.rerun()

        if c2.button(f"🗑️ Eliminar '{p_sel}'"):
            st.session_state.confirm_del = True
        
        if st.session_state.get('confirm_del'):
            st.error(f"¿Estás seguro de eliminar {p_sel} para siempre?")
            if st.button("🔥 SÍ, ELIMINAR PERMANENTEMENTE"):
                supabase.table("productos").delete().eq("id", item['id']).execute()
                st.session_state.confirm_del = False; st.rerun()

        # EL CHEF INTELIGENTE
        st.divider()
        st.subheader("👨‍🍳 Ideas del Chef Inteligente")
        if st.button("🪄 Generar Menú (Sencillo + Gourmet)"):
            menu = generar_menu_inteligente(df_c[df_c['cantidad'] > 0]['nombre'].tolist())
            for m, platos in menu.items():
                if platos:
                    st.write(f"### {m}")
                    cols = st.columns(2)
                    for idx, p in enumerate(platos):
                        with cols[idx % 2]:
                            with st.expander(p['titulo']): st.info(p['receta'])
    else: st.info("Sección de comida vacía.")

# --- LÓGICA DE TABLAS FINANCIERAS ---
def render_tabla(df_sec, mod):
    if not df_sec.empty:
        df_sec['Subtotal USD'] = df_sec['precio'] * df_sec['cantidad']
        df_sec['Subtotal Bs.'] = df_sec['Subtotal USD'] * tasa_bcv
        
        st.data_editor(df_sec[["id", "nombre", "precio", "cantidad", "Subtotal USD", "Subtotal Bs."]], 
                       use_container_width=True, hide_index=True, disabled=["Subtotal USD", "Subtotal Bs."], key=f"ed_{mod}")
        
        t_usd = df_sec['Subtotal USD'].sum()
        t_bs = t_usd * tasa_bcv
        
        c1, c2 = st.columns(2)
        c1.metric(f"Total {mod} ($)", f"{t_usd:.2f} $")
        c2.metric(f"Total {mod} (Bs)", f"{t_bs:,.2f} Bs")
    else: st.info(f"Sección {mod} vacía.")

with t_hogar:
    df_h = df_all[df_all['modulo'] == 'Hogar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla(df_h, "Hogar")

with t_compras:
    df_p = df_all[df_all['modulo'] == 'Por Comprar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla(df_p, "Por Comprar")
