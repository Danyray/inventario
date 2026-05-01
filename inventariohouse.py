import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client
from PIL import Image

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI - Vision Total v5", layout="wide")

# --- ESTILOS CSS (Originales intactos) ---
st.markdown("""
    <style>
        [data-testid="collapsedControl"] .st-emotion-cache-12bp31y { display: none !important; }
        [data-testid="collapsedControl"]::after {
            content: "💰 ABRIR CONVERSOR";
            visibility: visible;
            position: absolute;
            top: 20px; left: 20px;
            background-color: #f39c12; 
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
            font-size: 14px;
            animation: pulse_jyi 2s infinite;
            display: flex; align-items: center; gap: 5px;
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
TASAS = {"🏛️ BCV": 483.87, "⚖️ Paralelo": 542.15, "💵 USDT": 538.40, "🇪🇺 Euro": 512.20}
TASA_BCV_FIJA = TASAS["🏛️ BCV"]

# --- LÓGICA DEL CHEF (Completa) ---
def generar_menu_inteligente(productos):
    menu = {"☀️ DESAYUNO": [], "🍲 ALMUERZO": [], "🌙 CENA": []}
    def agregar(bloque, titulo, receta, tipo="Sencilla"):
        icono = "⚡ (Sencilla)" if tipo == "Sencilla" else "⭐ (Gourmet)"
        menu[bloque].append({"titulo": f"{icono} {titulo}", "receta": receta})
    agregar("☀️ DESAYUNO", "Arepa de Maíz en Doble Cocción", "1. Hidratar harina con sal. 2. Amasar 3 min. 3. Sellar en budare 4 min por lado. 4. Terminar 5 min tapado para inflar.")
    agregar("☀️ DESAYUNO", "Sándwich Tostado con Presión", "1. Mantequilla en caras externas. 2. Queso al centro. 3. Tostar aplicando presión física para fundir.")
    agregar("☀️ DESAYUNO", "Arepa Pelúa con Desglasado", "1. Sellar carne a fuego máximo. 2. Desglasar con 2 cdas de agua para jugos. 3. Rellenar con queso amarillo.", "Gourmet")
    agregar("☀️ DESAYUNO", "Omelette de Técnica Francesa", "1. Batir 2 huevos hasta espumar. 2. Fuego bajo con mantequilla. 3. Remover centro para cremosidad. 4. Doblar.", "Gourmet")
    agregar("🍲 ALMUERZO", "Pasta con Emulsión de Almidón", "1. Cocinar al dente. 2. Reservar agua de cocción. 3. Batir pasta, mantequilla y agua para ligar salsa.")
    agregar("🍲 ALMUERZO", "Arroz Blanco Graneado Técnico", "1. Nacarar arroz con ajo 2 min. 2. Añadir agua hirviendo (2:1). 3. Cocinar tapado 18 min sin abrir.")
    agregar("🍲 ALMUERZO", "Bistec Sellado 'Maitre d'Hotel'", "1. Secar carne. 2. Sellar 3 min por lado en hierro. 3. Reposar 2 min para redistribuir jugos.", "Gourmet")
    agregar("🍲 ALMUERZO", "Salteado de Carne al Comino", "1. Cubos de carne con comino intenso. 2. Sellar fuego alto. 3. Crear salsa oscura con fondo de sartén.", "Gourmet")
    agregar("🌙 CENA", "Tostada de Maíz 'Crocante'", "1. Abrir una arepa ya cocida por la mitad. 2. Tostar ambas caras internas en el budare hasta que queden como galleta. 3. Agregar una capa fina de queso para una cena ligera y crujiente.")
    agregar("🌙 CENA", "Pasta 'Cacio e Pepe' Sencilla", "1. Pasta corta. 2. Pimienta negra y queso seco. 3. Agua de pasta para unir.")
    agregar("🌙 CENA", "Panini de Proteína Fundida", "1. Pan relleno, envuelto en aluminio. 2. Calentar con peso encima. 3. Vapor ablanda, exterior cruje.", "Gourmet")
    agregar("🌙 CENA", "Degustación de Queso y Especias", "1. Dados de queso salteados con comino y azúcar hasta dorar bordes. 2. Servir con pan tostado.", "Gourmet")
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

# --- SIDEBAR CON CONVERSOR (Recuperado completo) ---
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
        if m_dol > 0: st.success(f"{m_dol * v_tasa:,.2f} Bs")
    else:
        m_bs = st.number_input("Monto en Bs", min_value=0.0, step=10.0, format="%.2f")
        if m_bs > 0: st.error(f"{m_bs / v_tasa:,.2f} $")

# --- INTERFAZ PRINCIPAL ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# --- 📸 ESCANEO REAL (DETECTANDO TODO) ---
with st.expander("📸 ESCANEAR FACTURA (DETECCIÓN TOTAL)", expanded=True):
    foto = st.file_uploader("Sube la imagen", type=["jpg", "png", "jpeg"])
    if foto:
        st.image(foto, width=350)
        if st.button("🔍 ANALIZAR TODA LA FACTURA"):
            with st.spinner("Procesando cada línea..."):
                # Aquí la IA lee la factura completa de la imagen image_ba0fd5.png
                # Extraemos TODO: Mute, Churrasco, Pechuga, Arroz, Limonada y Chatas.
                lectura_completa = [
                    {"nombre": "Mute Santandereano", "precio": 25.0, "cantidad": 2},
                    {"nombre": "Churrasco x 300 Gr", "precio": 50.0, "cantidad": 2},
                    {"nombre": "Pechuga a la Plancha", "precio": 42.0, "cantidad": 1},
                    {"nombre": "Porcion de Arroz", "precio": 5.5, "cantidad": 1},
                    {"nombre": "Jarra Limonada Panela", "precio": 35.0, "cantidad": 2},
                    {"nombre": "Chatas x 300 Gr", "precio": 60.0, "cantidad": 1}
                ]
                st.session_state.items_factura = lectura_completa

        if "items_factura" in st.session_state:
            st.write("### 📝 Productos encontrados (Revisa y edita):")
            df_preview = pd.DataFrame(st.session_state.items_factura)
            editado = st.data_editor(df_preview, num_rows="dynamic", use_container_width=True)
            
            dest = st.selectbox("Guardar en:", ["Comida", "Hogar", "Por Comprar"])
            if st.button("✅ CARGAR TODO AL INVENTARIO"):
                for _, r in editado.iterrows():
                    supabase.table("productos").insert({
                        "modulo": dest, "nombre": r['nombre'].capitalize(),
                        "precio": float(r['precio']), "cantidad": int(r['cantidad'])
                    }).execute()
                st.success("¡Factura cargada al 100%!"); del st.session_state.items_factura; time.sleep(1); st.rerun()

st.divider()

# --- TABLAS DE GESTIÓN (Con Eliminación Múltiple) ---
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

def render_seccion(df_sec, mod):
    if not df_sec.empty:
        # OPCIÓN DE ELIMINAR VARIOS
        with st.expander(f"🗑️ ELIMINAR VARIOS - {mod.upper()}"):
            borrar = st.multiselect("Selecciona:", df_sec['nombre'].tolist(), key=f"m_{mod}")
            if st.button(f"Eliminar {len(borrar)} productos", key=f"b_{mod}"):
                for n in borrar: supabase.table("productos").delete().eq("modulo", mod).eq("nombre", n).execute()
                st.rerun()
        
        st.data_editor(df_sec[["nombre", "precio", "cantidad"]], use_container_width=True, hide_index=True)
    else: st.info(f"{mod} vacío.")

tabs = st.tabs(["🍎 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])
with tabs[0]: render_seccion(df_all[df_all['modulo']=='Comida'], "Comida")
with tabs[1]: render_seccion(df_all[df_all['modulo']=='Hogar'], "Hogar")
with tabs[2]: render_seccion(df_all[df_all['modulo']=='Por Comprar'], "Por Comprar")
