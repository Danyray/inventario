import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI - Versión Final Blindada v3", layout="wide")

# --- ESTILO PARA EL BOTÓN DE APERTURA LLAMATIVO ---
# Esto reemplaza las flechitas por un botón intuitivo que cualquiera pueda entender
st.markdown("""
    <style>
        [data-testid="stSidebarCollapseIcon"] {
            visibility: hidden;
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
            animation: pulse 2s infinite;
        }
        [data-testid="collapsedControl"] {
            cursor: pointer;
            width: 200px;
            height: 60px;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            70% { transform: scale(1.05); }
            100% { transform: scale(1); }
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
    "🏦 BCV": 483.87,
    "⚖️ Paralelo": 542.15,
    "💎 USDT": 538.40,
    "🇪🇺 Euro": 512.20
}
TASA_BCV_FIJA = TASAS["🏦 BCV"]

# --- LÓGICA DEL CHEF ---
def generar_menu_inteligente(productos):
    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}
    def agregar(bloque, titulo, receta, tipo="Sencilla"):
        icono = "⚡ (Sencilla)" if tipo == "Sencilla" else "⭐ (Gourmet)"
        menu[bloque].append({"titulo": f"{icono} {titulo}", "receta": receta})

    agregar("☀️ DESAYUNO", "Arepa en Doble Cocción", "1. Hidratar harina. 2. Amasar. 3. Sellar en budare. 4. Terminar tapado.")
    agregar("☀️ DESAYUNO", "Sándwich con Presión", "1. Mantequilla externa. 2. Queso al centro. 3. Tostar con peso encima.")
    agregar("☀️ DESAYUNO", "Arepa Pelúa Gourmet", "1. Sellar carne. 2. Desglasar jugos. 3. Rellenar con queso amarillo.", "Gourmet")
    agregar("☀️ DESAYUNO", "Omelette Cremoso", "1. Batir huevos espumosos. 2. Fuego bajo. 3. Remover centro.", "Gourmet")
    
    agregar("🍴 ALMUERZO", "Pasta con Emulsión", "1. Cocinar al dente. 2. Usar agua de pasta y mantequilla para ligar salsa.")
    agregar("🍴 ALMUERZO", "Arroz Graneado", "1. Nacarar con ajo. 2. Agua hirviendo 2:1. 3. No abrir en 18 min.")
    agregar("🍴 ALMUERZO", "Bistec Sellado", "1. Secar carne. 2. Hierro muy caliente 3 min/lado. 3. Reposo obligatorio.", "Gourmet")
    agregar("🍴 ALMUERZO", "Carne al Comino", "1. Salteado rápido. 2. Comino intenso. 3. Reducción de fondo.", "Gourmet")
    
    agregar("🌙 CENA", "Tostada de Maíz", "1. Arepa abierta. 2. Tostar caras internas hasta que suene crocante.")
    agregar("🌙 CENA", "Cacio e Pepe Sencillo", "1. Pasta corta. 2. Pimienta negra. 3. Queso seco y agua de pasta.")
    agregar("🌙 CENA", "Panini de Proteína", "1. Relleno compacto. 2. Papel aluminio y peso. 3. Tostado uniforme.", "Gourmet")
    agregar("🌙 CENA", "Queso Salteado", "1. Dados de queso con especias. 2. Dorado en sartén. 3. Pan de acompañamiento.", "Gourmet")
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

# --- SIDEBAR: MONITOR Y CONVERSOR ---
st.sidebar.title("💰 Monitor de Divisas")
st.sidebar.info(f"🏦 BCV: **{TASAS['🏦 BCV']}**")
st.sidebar.warning(f"⚖️ Paralelo: **{TASAS['⚖️ Paralelo']}**")
st.sidebar.success(f"💎 USDT: **{TASAS['💎 USDT']}**")
st.sidebar.error(f"🇪🇺 Euro: **{TASAS['🇪🇺 Euro']}**")

st.sidebar.divider()

with st.sidebar.container():
    st.markdown("### 🔄 CONVERSOR DE MONEDA")
    tasa_sel = st.selectbox("📌 Tasa a usar:", list(TASAS.keys()), index=0)
    v_tasa = TASAS[tasa_sel]
    modo = st.radio("Acción:", ["💵 $ a Bolívares", "🇻🇪 Bolívares a $"])
    
    st.markdown("---")
    
    if "💵" in modo:
        m_dol = st.number_input("Introduzca Dólares ($)", min_value=0.0, step=1.0, format="%.2f")
        if m_dol > 0:
            res_val = m_dol * v_tasa
            st.success(f"Son: **{res_val:,.2f} Bs**")
    else:
        m_bs = st.number_input("Introduzca Bolívares (Bs)", min_value=0.0, step=10.0, format="%.2f")
        if m_bs > 0:
            res_val = m_bs / v_tasa
            st.success(f"Son: **{res_val:,.2f} $**")

st.sidebar.divider()

# --- INTERFAZ PRINCIPAL ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

with st.expander("➕ REGISTRAR NUEVO PRODUCTO", expanded=True):
    f1, f2 = st.columns(2)
    m_new = f1.selectbox("Destino", ["Comida", "Hogar", "Por Comprar"])
    n_new = f1.text_input("Nombre del producto")
    p_new = f2.number_input("Precio Unitario $", min_value=0.0, format="%.2f")
    c_new = f2.number_input("Cantidad", min_value=1)
    
    if st.button("🚀 GUARDAR"):
        if n_new:
            nombre_cap = n_new.capitalize().strip()
            existe = supabase.table("productos").select("*").eq("modulo", m_new).eq("nombre", nombre_cap).execute()
            if existe.data:
                st.error(f"⚠️ El producto '{nombre_cap}' ya existe.")
            else:
                supabase.table("productos").insert({
                    "modulo": m_new, 
                    "nombre": nombre_cap, 
                    "precio": float(p_new), 
                    "cantidad": int(c_new), 
                    "created_at": datetime.now().isoformat()
                }).execute()
                st.success("✅ Guardado"); time.sleep(1); st.rerun()

st.divider()

# CARGA Y TABLAS
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])
t_comida, t_hogar, t_compras = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

def render_tabla_gestion(df_sec, mod):
    if not df_sec.empty:
        df_sec['Subtotal $'] = df_sec['precio'] * df_sec['cantidad']
        df_sec['Subtotal Bs.'] = df_sec['Subtotal $'] * TASA_BCV_FIJA
        edited_df = st.data_editor(
            df_sec[["id", "nombre", "precio", "cantidad", "Subtotal $", "Subtotal Bs."]], 
            use_container_width=True, hide_index=True, 
            disabled=["id", "Subtotal $", "Subtotal Bs."],
            key=f"editor_{mod}"
        )
        total_usd = (edited_df['precio'] * edited_df['cantidad']).sum()
        c1, c2 = st.columns(2)
        c1.metric(f"Total {mod} ($)", f"{total_usd:.2f} $")
        c2.metric(f"Total {mod} (Bs)", f"{(total_usd * TASA_BCV_FIJA):,.2f} Bs")
        
        if not edited_df.equals(df_sec[["id", "nombre", "precio", "cantidad", "Subtotal $", "Subtotal Bs."]]):
            if st.button(f"💾 Guardar Cambios en {mod}"):
                for _, row in edited_df.iterrows():
                    supabase.table("productos").update({"precio": float(row['precio']), "cantidad": int(row['cantidad'])}).eq("id", row['id']).execute()
                st.rerun()
    else: st.info(f"{mod} vacío.")

with t_comida:
    df_c = df_all[df_all['modulo'] == 'Comida'].copy() if not df_all.empty else pd.DataFrame()
    if not df_c.empty:
        render_tabla_gestion(df_c, "Comida")
        st.divider()
        st.subheader("👨‍🍳 El Chef")
        if st.button("🪄 Generar Menú"):
            menu = generar_menu_inteligente(df_c[df_c['cantidad'] > 0]['nombre'].tolist())
            for momento, platos in menu.items():
                with st.expander(momento):
                    cols = st.columns(2)
                    for idx, p in enumerate(platos):
                        with cols[idx % 2]:
                            with st.expander(p['titulo']): st.info(p['receta'])
    else: st.info("Sin comida.")

with t_hogar:
    df_h = df_all[df_all['modulo'] == 'Hogar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla_gestion(df_h, "Hogar")

with t_compras:
    df_p = df_all[df_all['modulo'] == 'Por Comprar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla_gestion(df_p, "Por Comprar")
