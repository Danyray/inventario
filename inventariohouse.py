import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI - Chef 4x4 Pro", layout="wide")

# --- CONEXIÓN ---
@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar_supabase()

# --- TASA BCV FIJA (PÁGINA OFICIAL) ---
TASA_BCV_FIJA = 483.87 

# --- LÓGICA DEL CHEF INTELIGENTE (ESTRICTAMENTE 4 OPCIONES POR TURNO) ---
def generar_menu_inteligente(productos):
    p_list = [str(p).lower() for p in productos]
    tiene = lambda x: any(x in item for item in p_list)
    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}

    def agregar(bloque, titulo, receta, tipo="Sencilla"):
        icono = "⚡ (Sencilla)" if tipo == "Sencilla" else "⭐ (Gourmet)"
        menu[bloque].append({"titulo": f"{icono} {titulo}", "receta": receta})

    # --- DESAYUNOS (2 Sencillas + 2 Gourmet) ---
    agregar("☀️ DESAYUNO", "Arepa o Pan Tradicional", "1. Preparar base (masa o tostado). 2. Rellenar con lo disponible en stock. 3. Servir caliente.")
    agregar("☀️ DESAYUNO", "Revoltillo Express", "1. Batir huevos (si hay) o saltear embutidos. 2. Cocinar 3 min. 3. Acompañar con carbohidrato base.")
    # Gourmet
    agregar("☀️ DESAYUNO", "Torre Presidencial JYI", "1. Crear capas de arepa/pan, proteína sellada y queso. 2. Gratinar 2 min. 3. Servir con presentación circular.", "Gourmet")
    agregar("☀️ DESAYUNO", "Salteado de Proteína y Especias", "1. Cortar carne/huevo en dados. 2. Sazonar con comino y sal. 3. Sellar a fuego alto y rellenar.", "Gourmet")

    # --- ALMUERZOS (2 Sencillas + 2 Gourmet) ---
    base = "Pasta/Arroz" if not tiene("pasta") and not tiene("arroz") else ("Pasta" if tiene("pasta") else "Arroz")
    agregar("🍴 ALMUERZO", f"{base} al Natural", f"1. Hervir {base} con sal. 2. Añadir grasa (aceite/mantequilla). 3. Servir con queso rallado.")
    agregar("🍴 ALMUERZO", f"Bol de {base} Mixto", f"1. Mezclar {base} con cualquier vegetal o grano disponible. 2. Saltear todo junto por 5 min.")
    # Gourmet
    agregar("🍴 ALMUERZO", f"{base} en Salsa de Comino y Carne", f"1. Sellar carne en tiras. 2. Crear emulsión con agua de cocción y comino. 3. Mezclar con la {base}.", "Gourmet")
    agregar("🍴 ALMUERZO", "Degustación de Proteína Sellada", "1. Corte fino de carne sazonado. 2. Sellado 'Maitre' (dorado por fuera, jugoso dentro). 3. Acompañar con base moldeada.", "Gourmet")

    # --- CENAS (2 Sencillas + 2 Gourmet) ---
    agregar("🌙 CENA", "Tostada Ligera", "1. Pan o arepa delgada. 2. Capa fina de queso o mantequilla. 3. Tostar hasta que esté crocante.")
    agregar("🌙 CENA", "Sopa o Crema Rápida", "1. Procesar ingredientes con agua y sal. 2. Hervir 10 min. 3. Servir con trocitos de pan.")
    # Gourmet
    agregar("🌙 CENA", "Sandwich Goumert Fundido", "1. Capas dobles de queso y proteína. 2. Tostar con peso encima para compactar. 3. Cortar en triángulos.", "Gourmet")
    agregar("🌙 CENA", "Carpaccio de Proteína y Queso", "1. Láminas muy delgadas de carne sellada. 2. Decorar con lluvia de queso y comino. 3. Servir frío.", "Gourmet")

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
st.sidebar.subheader("🧮 Conversor de Divisas")
monto_dol = st.sidebar.number_input("Dólares a convertir ($)", min_value=0.0, step=1.0, format="%.2f")
if monto_dol > 0:
    st.sidebar.success(f"Son: **{(monto_dol * TASA_BCV_FIJA):,.2f} Bs**")

# --- INTERFAZ PRINCIPAL ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# 1. REGISTRO AL INICIO
with st.expander("➕ REGISTRAR NUEVO PRODUCTO", expanded=True):
    f1, f2 = st.columns(2)
    m_new = f1.selectbox("Destino", ["Comida", "Hogar", "Por Comprar"])
    n_new = f1.text_input("Nombre del producto")
    p_new = f2.number_input("Precio Unitario $", min_value=0.0, format="%.2f")
    c_new = f2.number_input("Cantidad", min_value=1)
    if st.button("🚀 GUARDAR PRODUCTO"):
        if n_new:
            supabase.table("productos").insert({"modulo": m_new, "nombre": n_new.capitalize(), "precio": float(p_new), "cantidad": int(c_new), "created_at": datetime.now().isoformat()}).execute()
            st.success("Guardado"); time.sleep(1); st.rerun()

st.divider()

# CARGA DE DATOS
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

t_comida, t_hogar, t_compras = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

with t_comida:
    df_c = df_all[df_all['modulo'] == 'Comida'].copy() if not df_all.empty else pd.DataFrame()
    if not df_c.empty:
        st.dataframe(df_c[["id", "nombre", "precio", "cantidad"]], use_container_width=True, hide_index=True)
        st.subheader("⚙️ Gestión")
        p_sel = st.selectbox("Elegir producto:", df_c['nombre'].tolist())
        item = df_c[df_c['nombre'] == p_sel].iloc[0]
        
        c1, c2 = st.columns(2)
        if c1.button(f"🛒 Enviar '{p_sel}' a Compras"): st.session_state.m_move = True
        if st.session_state.get('m_move'):
            if st.button(f"⚠️ CONFIRMAR MOVIMIENTO"):
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
            if st.button(f"🔥 CONFIRMAR ELIMINACIÓN"):
                supabase.table("productos").delete().eq("id", item['id']).execute()
                st.session_state.m_del = False; st.rerun()

        st.divider()
        st.subheader("👨‍🍳 El Chef: 4 Opciones")
        if st.button("🪄 Mostrar Menú Sencillo y Gourmet"):
            menu = generar_menu_inteligente(df_c[df_c['cantidad'] > 0]['nombre'].tolist())
            for m, platos in menu.items():
                st.write(f"### {m}")
                cols = st.columns(2)
                for idx, p in enumerate(platos):
                    with cols[idx % 2]:
                        with st.expander(p['titulo']): st.info(p['receta'])
    else: st.info("Sección vacía.")

# --- LÓGICA DE TABLAS ---
def render_tabla(df_sec, mod):
    if not df_sec.empty:
        df_sec['Subtotal $'] = df_sec['precio'] * df_sec['cantidad']
        df_sec['Subtotal Bs.'] = df_sec['Subtotal $'] * TASA_BCV_FIJA
        st.data_editor(df_sec[["id", "nombre", "precio", "cantidad", "Subtotal $", "Subtotal Bs."]], 
                       use_container_width=True, hide_index=True, disabled=["Subtotal $", "Subtotal Bs."], key=f"ed_{mod}")
        t_usd = df_sec['Subtotal $'].sum()
        c1, c2 = st.columns(2)
        c1.metric(f"Total {mod} ($)", f"{t_usd:.2f} $")
        c2.metric(f"Total {mod} (Bs)", f"{(t_usd * TASA_BCV_FIJA):,.2f} Bs")
    else: st.info(f"{mod} vacío.")

with t_hogar:
    df_h = df_all[df_all['modulo'] == 'Hogar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla(df_h, "Hogar")

with t_compras:
    df_p = df_all[df_all['modulo'] == 'Por Comprar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla(df_p, "Por Comprar")
