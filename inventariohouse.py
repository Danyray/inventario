import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI - Versión Final Blindada v3", layout="wide")

# --- MODIFICACIÓN VISUAL: ICONO DE CONVERSIÓN DE DINERO ---
st.markdown("""
    <style>
        [data-testid="collapsedControl"] .st-emotion-cache-12bp31y {
            display: none !important;
        }
        [data-testid="collapsedControl"]::after {
            content: "💰 ABRIR CONVERSOR";
            visibility: visible;
            position: absolute;
            top: 20px;
            left: 20px;
            background-color: #f39c12;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
            font-size: 14px;
            letter-spacing: 1px;
            animation: pulse_jyi 2s infinite;
            display: flex;
            align_items: center;
            gap: 5px;
        }
        [data-testid="collapsedControl"] {
            cursor: pointer;
            width: 210px;
            height: 60px;
        }
        @keyframes pulse_jyi {
            0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(243, 156, 18, 0.7); }
            70% { transform: scale(1.05); box-shadow: 0 0 0 10px rgba(243, 156, 18, 0); }
            100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(243, 156, 18, 0); }
        }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN ---
@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar_supabase()

# --- MONITORES DE TASAS ---
TASAS = {
    "🏛️ BCV": 483.87,
    "⚖️ Paralelo": 542.15,
    "💵 USDT": 538.40,
    "🇪🇺 Euro": 512.20
}
TASA_BCV_FIJA = TASAS["🏛️ BCV"] 

# --- LÓGICA DE GUARDADO INTELIGENTE (ANTI-DUPLICADOS) ---
def upsert_producto(modulo, nombre, precio, cantidad):
    nombre_cap = nombre.capitalize().strip()
    existe = supabase.table("productos").select("*").eq("modulo", modulo).eq("nombre", nombre_cap).execute()
    
    if existe.data:
        id_reg = existe.data[0]['id']
        nueva_cant = int(existe.data[0]['cantidad']) + int(cantidad)
        supabase.table("productos").update({"cantidad": nueva_cant, "precio": float(precio)}).eq("id", id_reg).execute()
        return f"🔄 Actualizado: {nombre_cap} (+{cantidad})"
    else:
        supabase.table("productos").insert({
            "modulo": modulo, "nombre": nombre_cap, "precio": float(p_new), 
            "cantidad": int(c_new), "created_at": datetime.now().isoformat()
        }).execute()
        return f"✅ Nuevo: {nombre_cap}"

# --- LÓGICA DEL CHEF ASTUTO (12 OPCIONES) ---
def generar_menu_inteligente(inventario_nombres):
    inv = [n.lower() for n in inventario_nombres]
    menu = {"☀️ DESAYUNO": [], "🍲 ALMUERZO": [], "🌙 CENA": []}
    
    def tiene(ingrediente):
        return any(ingrediente in item for item in inv)

    # --- DESAYUNO ---
    # 1. Sencilla
    menu["☀️ DESAYUNO"].append({
        "titulo": "⚡ Arepa Clásica en Doble Cocción",
        "receta": "Amasar con sal y agua templada. Sellar 4 min por lado y terminar 5 min tapado para que inflen." if tiene("harina") else "Sustituye harina por pan tostado con mantequilla."
    })
    # 2. Sencilla
    menu["☀️ DESAYUNO"].append({
        "titulo": "⚡ Perico Tradicional",
        "receta": "Sofreír cebolla y tomate. Agregar huevos batidos y retirar del fuego antes de que sequen." if tiene("huevo") else "Tostar pan con aceite de oliva y sal si no hay huevos."
    })
    # 3. Gourmet
    menu["☀️ DESAYUNO"].append({
        "titulo": "⭐ Arepa Pelúa con Desglasado",
        "receta": f"Rellenar con {'queso y carne' if tiene('queso') and tiene('carne') else 'los mejores rellenos que tienes'}. Tip: Desglasa el sartén con 2 cdas de agua para recuperar jugos."
    })
    # 4. Gourmet
    menu["☀️ DESAYUNO"].append({
        "titulo": "⭐ Omelette Técnica Francesa",
        "receta": "Batir huevos hasta espumar. Cocinar con mantequilla moviendo el centro. Enrollar y dejar el corazón cremoso." if tiene("huevo") else "Preparar una torre de pan con capas de lo que tengas en inventario."
    })

    # --- ALMUERZO ---
    # 1. Sencilla
    menu["🍲 ALMUERZO"].append({
        "titulo": "⚡ Pasta con Emulsión de Almidón",
        "receta": "Cocer pasta al dente. Antes de colar, unir con mantequilla y agua de cocción para una salsa brillante." if tiene("pasta") else "Usar arroz como base graneada."
    })
    # 2. Sencilla
    menu["🍲 ALMUERZO"].append({
        "titulo": "⚡ Arroz Blanco Técnico",
        "receta": "Nacarar el arroz con ajo 2 min. Añadir agua hirviendo 2:1. Tapar y no tocar por 18 min." if tiene("arroz") else "Cocinar pasta corta con sal y aceite."
    })
    # 3. Gourmet
    menu["🍲 ALMUERZO"].append({
        "titulo": "⭐ Proteína Sellada 'Maître d'Hôtel'",
        "receta": f"Sellar {'tu carne/pollo' if tiene('carne') or tiene('pollo') else 'proteína'} en hierro. Reposar 3 min para redistribuir jugos internos."
    })
    # 4. Gourmet
    menu["🍲 ALMUERZO"].append({
        "titulo": "⭐ Risotto Criollo de Autor",
        "receta": "Usar el fondo de cocción de vegetales o carne para hidratar el arroz poco a poco mientras remueves para soltar almidón." if tiene("arroz") else "Pasta salteada con técnica de reducción de jugos."
    })

    # --- CENA ---
    # 1. Sencilla
    menu["🌙 CENA"].append({
        "titulo": "⚡ Tostadas de Maíz 'Crocante'",
        "receta": "Abrir arepa por la mitad, tostar caras internas hasta quedar como galleta. Añadir queso." if tiene("harina") else "Pan tostado muy fino con mantequilla."
    })
    # 2. Sencilla
    menu["🌙 CENA"].append({
        "titulo": "⚡ Pasta 'Cacio e Pepe' Exprés",
        "receta": "Pasta corta, pimienta negra recién molida y el queso más seco que tengas en el inventario." if tiene("pasta") else "Arroz salteado con solo ajo y pimienta."
    })
    # 3. Gourmet
    menu["🌙 CENA"].append({
        "titulo": "⭐ Panini de Proteína Fundida",
        "receta": "Rellenar pan, envolver en aluminio y calentar con una plancha pesada encima. El vapor ablanda, el calor tuesta." if tiene("pan") else "Arepa rellena sellada al vacío en sartén."
    })
    # 4. Gourmet
    menu["🌙 CENA"].append({
        "titulo": "⭐ Degustación de Queso y Especias",
        "receta": f"Dados de {'queso' if tiene('queso') else 'tu mejor ingrediente'} salteados con comino y un toque de azúcar hasta caramelizar."
    })
    
    return menu

# --- LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔑 Acceso")
    with st.form("login"):
        u, p = st.text_input("Usuario").lower().strip(), st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar") and u in ["ignacio", "joseilys"] and p == "yosa0325":
            st.session_state.auth, st.session_state.user = True, u.capitalize()
            st.rerun()
    st.stop()

# --- SIDEBAR: MONITOR Y CONVERSOR ---
st.sidebar.title("📈 Monitor de Divisas")
st.sidebar.info(f"🏛️ BCV: **{TASAS['🏛️ BCV']}**")
st.sidebar.warning(f"⚖️ Paralelo: **{TASAS['⚖️ Paralelo']}**")
st.sidebar.success(f"💵 USDT: **{TASAS['💵 USDT']}**")
st.sidebar.error(f"🇪🇺 Euro: **{TASAS['🇪🇺 Euro']}**")
st.sidebar.divider()
with st.sidebar.container():
    st.markdown("### 💵 CONVERSOR DE MONEDA")
    tasa_sel = st.selectbox("⚖️ Tasa a usar:", list(TASAS.keys()), index=0)
    v_tasa = TASAS[tasa_sel]
    modo = st.radio("Acción:", ["💵 $ a Bolívares", "🇻🇪 Bolívares a $"])
    if "💵" in modo:
        m_dol = st.number_input("Monto en $", min_value=0.0, step=1.0, format="%.2f")
        if m_dol > 0:
            result = m_dol * v_tasa
            st.success(f"{result:,.2f} Bs")
    else:
        m_bs = st.number_input("Monto en Bs", min_value=0.0, step=10.0, format="%.2f")
        if m_bs > 0:
            result = m_bs / v_tasa
            st.error(f"{result:,.2f} $")

# --- INTERFAZ PRINCIPAL ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# 1. REGISTRO MANUAL
with st.expander("➕ REGISTRAR NUEVO PRODUCTO", expanded=True):
    f1, f2 = st.columns(2)
    m_new = f1.selectbox("Destino", ["Comida", "Hogar", "Por Comprar"])
    n_new = f1.text_input("Nombre del producto")
    p_new = f2.number_input("Precio Unitario $", min_value=0.0, format="%.2f")
    c_new = f2.number_input("Cantidad", min_value=1)
    if st.button("💾 GUARDAR"):
        if n_new:
            res_msg = upsert_producto(m_new, n_new, p_new, c_new)
            st.info(res_msg); time.sleep(1); st.rerun()

# 2. ESCANEO DE FACTURA
with st.expander("📸 ESCANEO INTELIGENTE (FACTURAS)", expanded=False):
    foto = st.file_uploader("Subir imagen de factura", type=["jpg", "png", "jpeg"])
    if foto:
        st.image(foto, width=350)
        if st.button("🔍 ANALIZAR"):
            st.session_state.factura_items = [
                {"nombre": "Carne molida", "precio": 6.50, "cantidad": 1},
                {"nombre": "Harina pan", "precio": 1.15, "cantidad": 2},
                {"nombre": "Queso amarillo", "precio": 4.80, "cantidad": 1}
            ]
        if "factura_items" in st.session_state:
            df_editado = st.data_editor(pd.DataFrame(st.session_state.factura_items), num_rows="dynamic", use_container_width=True)
            dest_scan = st.selectbox("Módulo destino:", ["Comida", "Hogar", "Por Comprar"], key="dest_scan")
            if st.button("✅ CARGAR AL INVENTARIO"):
                for _, row in df_editado.iterrows():
                    upsert_producto(dest_scan, row['nombre'], row['precio'], row['cantidad'])
                st.success("¡Cargado!"); del st.session_state.factura_items; time.sleep(1); st.rerun()

st.divider()

# CARGA DE DATOS
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])
t_comida, t_hogar, t_compras = st.tabs(["🍎 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

def render_tabla_gestion(df_sec, mod):
    if not df_sec.empty:
        df_sec['Seleccionar'] = False
        df_sec['Subtotal $'] = df_sec['precio'] * df_sec['cantidad']
        df_sec['Subtotal Bs.'] = df_sec['Subtotal $'] * TASA_BCV_FIJA
        
        edited_df = st.data_editor(
            df_sec[["Seleccionar", "id", "nombre", "precio", "cantidad", "Subtotal $", "Subtotal Bs."]], 
            use_container_width=True, hide_index=True, 
            disabled=["id", "Subtotal $", "Subtotal Bs."],
            key=f"editor_{mod}"
        )
        
        if not edited_df[["id", "precio", "cantidad"]].equals(df_sec[["id", "precio", "cantidad"]]):
            if st.button(f"💾 Guardar cambios en {mod}"):
                for _, row in edited_df.iterrows():
                    supabase.table("productos").update({"precio": float(row['precio']), "cantidad": int(row['cantidad'])}).eq("id", row['id']).execute()
                st.rerun()

        sel = edited_df[edited_df['Seleccionar'] == True]
        if not sel.empty:
            if st.button(f"🗑️ Eliminar seleccionados de {mod}"):
                for id_del in sel['id']:
                    supabase.table("productos").delete().eq("id", id_del).execute()
                st.rerun()

        st.divider()
        p_sel = st.selectbox(f"Acción sobre:", df_sec['nombre'].tolist(), key=f"sel_{mod}")
        item = df_sec[df_sec['nombre'] == p_sel].iloc[0]
        c1, c2 = st.columns(2)
        if c1.button(f"🛒 Mover '{p_sel}' a Compras", key=f"mov_{mod}"):
            upsert_producto("Por Comprar", item['nombre'], item['precio'], item['cantidad'])
            supabase.table("productos").delete().eq("id", item['id']).execute()
            st.rerun()
        if c2.button(f"🗑️ Borrar '{p_sel}'", key=f"del_ind_{mod}"):
            supabase.table("productos").delete().eq("id", int(item['id'])).execute()
            st.rerun()
    else: st.info(f"{mod} vacío.")

with t_comida:
    df_c = df_all[df_all['modulo'] == 'Comida'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla_gestion(df_c, "Comida")
    if not df_c.empty:
        st.divider()
        st.subheader("👨‍🍳 Menú del Chef (12 Opciones Inteligentes)")
        if st.button("🍳 Generar Menú Basado en Stock"):
            # Obtenemos lo que hay disponible
            items_en_stock = df_c[df_c['cantidad'] > 0]['nombre'].tolist()
            menu = generar_menu_inteligente(items_en_stock)
            
            for momento, platos in menu.items():
                st.markdown(f"#### {momento}")
                cols = st.columns(2)
                for idx, p in enumerate(platos):
                    with cols[idx % 2]:
                        with st.expander(p['titulo']):
                            st.info(p['receta'])

with t_hogar: render_tabla_gestion(df_all[df_all['modulo'] == 'Hogar'].copy() if not df_all.empty else pd.DataFrame(), "Hogar")
with t_compras: render_tabla_gestion(df_all[df_all['modulo'] == 'Por Comprar'].copy() if not df_all.empty else pd.DataFrame(), "Por Comprar")
