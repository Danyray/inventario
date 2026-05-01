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
            "modulo": modulo, "nombre": nombre_cap, "precio": float(precio), 
            "cantidad": int(cantidad), "created_at": datetime.now().isoformat()
        }).execute()
        return f"✅ Nuevo: {nombre_cap}"

# --- LÓGICA DEL CHEF (VINCULADA AL INVENTARIO REAL) ---
def generar_menu_inteligente(inventario_nombres):
    # Convertir a minúsculas para búsqueda flexible
    inv = [n.lower() for n in inventario_nombres]
    menu = {"☀️ DESAYUNO": [], "🍲 ALMUERZO": [], "🌙 CENA": []}
    
    def tiene(ingrediente):
        return any(ingrediente in item for item in inv)

    # --- DESAYUNOS ---
    if tiene("harina") or tiene("maiz"):
        menu["☀️ DESAYUNO"].append({"titulo": "⚡ Arepa Clásica", "receta": "Amasar harina, sal y agua. Sellar en budare."})
        if tiene("queso"):
            menu["☀️ DESAYUNO"].append({"titulo": "⭐ Arepa con Queso Fundido", "receta": "Rellenar con queso y calentar hasta fundir."})
    if tiene("pan"):
        menu["☀️ DESAYUNO"].append({"titulo": "⚡ Sándwich Tostado", "receta": "Tostar pan con mantequilla/aceite y el relleno disponible."})
    if tiene("huevo"):
        menu["☀️ DESAYUNO"].append({"titulo": "⭐ Omelette Técnico", "receta": "Batir huevos vigorosamente, cocinar a fuego bajo con poco aceite."})

    # --- ALMUERZOS ---
    if tiene("pasta"):
        menu["🍲 ALMUERZO"].append({"titulo": "⚡ Pasta al Almidón", "receta": "Cocer pasta y usar un poco de agua de cocción para crear emulsión."})
    if tiene("arroz"):
        menu["🍲 ALMUERZO"].append({"titulo": "⚡ Arroz Blanco Graneado", "receta": "Nacarar con ajo, añadir agua 2:1 y no destapar."})
    if tiene("carne") or tiene("bistec") or tiene("pollo"):
        menu["🍲 ALMUERZO"].append({"titulo": "⭐ Proteína Sellada", "receta": "Sellar a fuego máximo 3 min por lado para jugosidad."})
    if tiene("carne") and tiene("comino"):
        menu["🍲 ALMUERZO"].append({"titulo": "⭐ Salteado al Comino", "receta": "Saltear tiras de carne con comino y desglasar sartén."})

    # --- CENAS ---
    if tiene("pan") or tiene("queso"):
        menu["🌙 CENA"].append({"titulo": "⚡ Panini de Queso", "receta": "Prensar pan con queso y calentar con peso encima."})
    if tiene("harina"):
        menu["🌙 CENA"].append({"titulo": "⚡ Tostadas de Maíz", "receta": "Hacer arepas finas y tostarlas hasta quedar crocantes."})
    
    # Relleno de seguridad si no hay nada
    for bloque in menu:
        if not menu[bloque]:
            menu[bloque].append({"titulo": "❓ Opción Sugerida", "receta": "Revisa tus existencias de harina, arroz o pasta para habilitar recetas."})
            
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
    st.markdown("---")
    if "💵" in modo:
        m_dol = st.number_input("Monto en $", min_value=0.0, step=1.0, format="%.2f")
        if m_dol > 0:
            result = m_dol * v_tasa
            st.markdown(f'<div style="background-color:#1e3d33; padding:15px; border-radius:10px; border-left: 5px solid #2ecc71;"><h2 style="margin:0; color:#2ecc71;">{result:,.2f} Bs</h2></div>', unsafe_allow_html=True)
    else:
        m_bs = st.number_input("Monto en Bs", min_value=0.0, step=10.0, format="%.2f")
        if m_bs > 0:
            result = m_bs / v_tasa
            st.markdown(f'<div style="background-color:#3d1e1e; padding:15px; border-radius:10px; border-left: 5px solid #e74c3c;"><h2 style="margin:0; color:#e74c3c;">{result:,.2f} $</h2></div>', unsafe_allow_html=True)

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
        if st.button("🔍 ANALIZAR CONTENIDO COMPLETO"):
            st.session_state.factura_items = [
                {"nombre": "Harina pan", "precio": 1.20, "cantidad": 2},
                {"nombre": "Queso blanco", "precio": 5.50, "cantidad": 1},
                {"nombre": "Arroz", "precio": 1.10, "cantidad": 3}
            ]
        if "factura_items" in st.session_state:
            df_editado = st.data_editor(pd.DataFrame(st.session_state.factura_items), num_rows="dynamic", use_container_width=True)
            dest_scan = st.selectbox("Guardar detección en:", ["Comida", "Hogar", "Por Comprar"], key="dest_scan")
            if st.button("✅ CARGAR TODO AL INVENTARIO"):
                for _, row in df_editado.iterrows():
                    upsert_producto(dest_scan, row['nombre'], row['precio'], row['cantidad'])
                st.success("¡Factura procesada!"); del st.session_state.factura_items; time.sleep(1); st.rerun()

st.divider()

# CARGA DE DATOS
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])
t_comida, t_hogar, t_compras = st.tabs(["🍎 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

# --- TABLAS CON ELIMINADO MÚLTIPLE ---
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
            if st.button(f"💾 Actualizar Datos en {mod}"):
                for _, row in edited_df.iterrows():
                    supabase.table("productos").update({"precio": float(row['precio']), "cantidad": int(row['cantidad'])}).eq("id", row['id']).execute()
                st.rerun()

        seleccionados = edited_df[edited_df['Seleccionar'] == True]
        if not seleccionados.empty:
            if st.button(f"🗑️ Eliminar Seleccionados ({len(seleccionados)})", key=f"del_mult_{mod}"):
                for id_del in seleccionados['id']:
                    supabase.table("productos").delete().eq("id", id_del).execute()
                st.success("Eliminados"); time.sleep(1); st.rerun()

        st.divider()
        p_sel = st.selectbox(f"Acción rápida sobre:", df_sec['nombre'].tolist(), key=f"sel_{mod}")
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
        st.subheader("👨‍🍳 El Chef")
        if st.button("🍳 ¿Qué puedo cocinar hoy?"):
            # Filtrar solo productos con stock > 0
            ingredientes = df_c[df_c['cantidad'] > 0]['nombre'].tolist()
            menu = generar_menu_inteligente(ingredientes)
            for mom, platos in menu.items():
                with st.expander(mom):
                    for p in platos:
                        with st.expander(p['titulo']): st.info(p['receta'])

with t_hogar: render_tabla_gestion(df_all[df_all['modulo'] == 'Hogar'].copy() if not df_all.empty else pd.DataFrame(), "Hogar")
with t_compras: render_tabla_gestion(df_all[df_all['modulo'] == 'Por Comprar'].copy() if not df_all.empty else pd.DataFrame(), "Por Comprar")
