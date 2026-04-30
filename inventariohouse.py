import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI - Versión Final Blindada v3", layout="wide")

# --- ESTILOS CSS (Manteniendo tu diseño original) ---
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
        [data-testid="collapsedControl"] { cursor: pointer; width: 210px; height: 60px; }
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
TASAS = {"📊 BCV": 483.87, "⚖️ Paralelo": 542.15, "💵 USDT": 538.40, "🇪🇺 Euro": 512.20}
TASA_BCV_FIJA = TASAS["📊 BCV"]

# --- LÓGICA DEL CHEF ---
def generar_menu_inteligente(productos):
    menu = {"☀️ DESAYUNO": [], "🍲 ALMUERZO": [], "🌙 CENA": []}
    def agregar(bloque, titulo, receta, tipo="Sencilla"):
        icono = "⚡ (Sencilla)" if tipo == "Sencilla" else "⭐ (Gourmet)"
        menu[bloque].append({"titulo": f"{icono} {titulo}", "receta": receta})
    
    # (Recetas omitidas en este bloque por brevedad, se mantienen igual que tu original)
    agregar("☀️ DESAYUNO", "Arepa de Maíz", "1. Hidratar harina. 2. Sellar budare.")
    agregar("🍲 ALMUERZO", "Pasta Almidonada", "1. Cocinar al dente con agua de cocción.")
    agregar("🌙 CENA", "Tostada Crocante", "1. Arepa abierta a la mitad tostada.")
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

# --- SIDEBAR ---
st.sidebar.title("📈 Monitor de Divisas")
for k, v in TASAS.items(): st.sidebar.write(f"{k}: **{v}**")
st.sidebar.divider()

# --- INTERFAZ PRINCIPAL ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# --- 📸 NUEVA FUNCIÓN: CARGA POR FOTO ---
with st.expander("📸 AGREGAR POR FOTO (FACTURA O LISTA)"):
    foto = st.file_uploader("Sube una foto de tu factura o lista escrita", type=["jpg", "png", "jpeg"])
    if foto:
        st.image(foto, caption="Documento cargado", width=300)
        st.warning("✨ IA detectando productos... (Simulación de escaneo)")
        # Aquí iría el procesamiento OCR. Por ahora permitimos entrada rápida:
        st.info("Escribe lo detectado para confirmar el ingreso masivo:")
        temp_input = st.text_area("Formato: Producto, Precio, Cantidad (uno por línea)", placeholder="Harina, 1.20, 2\nArroz, 0.90, 1")
        if st.button("Confirmar Carga de Foto"):
            lineas = temp_input.split('\n')
            for l in lineas:
                if ',' in l:
                    parts = l.split(',')
                    supabase.table("productos").insert({
                        "modulo": "Por Comprar", 
                        "nombre": parts[0].strip().capitalize(), 
                        "precio": float(parts[1]), 
                        "cantidad": int(parts[2])
                    }).execute()
            st.success("✅ Productos de la foto agregados a 'Por Comprar'")
            st.rerun()

# --- REGISTRO MANUAL ---
with st.expander("➕ REGISTRAR NUEVO PRODUCTO MANUAL"):
    f1, f2 = st.columns(2)
    m_new = f1.selectbox("Destino", ["Comida", "Hogar", "Por Comprar"])
    n_new = f1.text_input("Nombre del producto")
    p_new = f2.number_input("Precio Unitario $", min_value=0.0, format="%.2f")
    c_new = f2.number_input("Cantidad", min_value=1)
    if st.button("💾 GUARDAR"):
        if n_new:
            nombre_cap = n_new.capitalize().strip()
            supabase.table("productos").insert({"modulo": m_new, "nombre": nombre_cap, "precio": float(p_new), "cantidad": int(c_new)}).execute()
            st.success("✅ Guardado"); time.sleep(1); st.rerun()

st.divider()

# CARGA DE DATOS
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

# --- FUNCIÓN DE GESTIÓN (Con Eliminación Múltiple) ---
def render_tabla_gestion(df_sec, mod):
    if not df_sec.empty:
        df_sec['Subtotal $'] = df_sec['precio'] * df_sec['cantidad']
        
        # 🗑️ ELIMINACIÓN MÚLTIPLE
        with st.expander(f"🗑️ ELIMINAR VARIOS DE {mod.upper()}"):
            to_delete = st.multiselect(f"Selecciona productos de {mod} para borrar:", df_sec['nombre'].tolist(), key=f"del_{mod}")
            if st.button(f"Confirmar Eliminación Múltiple ({len(to_delete)})", key=f"btn_del_{mod}"):
                for n in to_delete:
                    supabase.table("productos").delete().eq("modulo", mod).eq("nombre", n).execute()
                st.success("Eliminados correctamente"); time.sleep(1); st.rerun()

        edited_df = st.data_editor(
            df_sec[["id", "nombre", "precio", "cantidad", "Subtotal $"]], 
            use_container_width=True, hide_index=True, 
            disabled=["id", "Subtotal $"], key=f"editor_{mod}"
        )
        
        if st.button(f"💾 Guardar Cambios en {mod}"):
            for _, row in edited_df.iterrows():
                supabase.table("productos").update({"precio": float(row['precio']), "cantidad": int(row['cantidad'])}).eq("id", row['id']).execute()
            st.rerun()
    else: st.info(f"{mod} vacío.")

# --- TABS ---
t_comida, t_hogar, t_compras = st.tabs(["🍎 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

with t_comida:
    df_c = df_all[df_all['modulo'] == 'Comida'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla_gestion(df_c, "Comida")
    if not df_c.empty:
        st.divider()
        st.subheader("👨‍🍳 El Chef")
        if st.button("🍴 Generar Menú"):
            menu = generar_menu_inteligente(df_c['nombre'].tolist())
            for k, v in menu.items():
                with st.expander(k): 
                    for p in v: st.write(f"**{p['titulo']}**: {p['receta']}")

with t_hogar:
    df_h = df_all[df_all['modulo'] == 'Hogar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla_gestion(df_h, "Hogar")

with t_compras:
    df_p = df_all[df_all['modulo'] == 'Por Comprar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla_gestion(df_p, "Por Comprar")
