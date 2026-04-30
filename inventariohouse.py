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

# --- LÓGICA DEL CHEF SUPERIOR ---
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
            st.markdown(f'<div style="background-color:#1e3d33; padding:15px; border-radius:10px; border-left: 5px solid #2ecc71;"><p style="margin:0; font-size:14px; color:#aecbbd;">Resultado en Bs:</p><h2 style="margin:0; color:#2ecc71;">{result:,.2f} Bs</h2></div>', unsafe_allow_html=True)
    else:
        m_bs = st.number_input("Monto en Bs", min_value=0.0, step=10.0, format="%.2f")
        if m_bs > 0:
            result = m_bs / v_tasa
            st.markdown(f'<div style="background-color:#3d1e1e; padding:15px; border-radius:10px; border-left: 5px solid #e74c3c;"><p style="margin:0; font-size:14px; color:#cbb9b9;">Resultado en $:</p><h2 style="margin:0; color:#e74c3c;">{result:,.2f} $</h2></div>', unsafe_allow_html=True)

st.sidebar.divider()

# --- INTERFAZ PRINCIPAL ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# AGREGAR POR FOTO (NUEVA FUNCIÓN)
with st.expander("📸 AGREGAR POR FOTO (FACTURA O LISTA)"):
    foto = st.file_uploader("Sube imagen de factura o lista", type=["jpg", "jpeg", "png"])
    if foto:
        st.image(foto, width=300)
        st.info("Escribe los productos detectados (Formato: Nombre, Precio, Cantidad)")
        texto_foto = st.text_area("Ejemplo: Arroz, 1.2, 2", help="Un producto por línea")
        dest_foto = st.selectbox("Enviar productos de foto a:", ["Comida", "Hogar", "Por Comprar"])
        if st.button("Confirmar Carga desde Foto"):
            for linea in texto_foto.split('\n'):
                if ',' in linea:
                    datos = linea.split(',')
                    supabase.table("productos").insert({"modulo": dest_foto, "nombre": datos[0].strip().capitalize(), "precio": float(datos[1]), "cantidad": int(datos[2])}).execute()
            st.success("Productos agregados correctamente"); time.sleep(1); st.rerun()

# REGISTRO MANUAL
with st.expander("➕ REGISTRAR NUEVO PRODUCTO", expanded=True):
    f1, f2 = st.columns(2)
    m_new = f1.selectbox("Destino", ["Comida", "Hogar", "Por Comprar"])
    n_new = f1.text_input("Nombre del producto")
    p_new = f2.number_input("Precio Unitario $", min_value=0.0, format="%.2f")
    c_new = f2.number_input("Cantidad", min_value=1)
    if st.button("💾 GUARDAR"):
        if n_new:
            nombre_cap = n_new.capitalize().strip()
            existe = supabase.table("productos").select("*").eq("modulo", m_new).eq("nombre", nombre_cap).execute()
            if existe.data: st.error(f"⚠️ El producto '{nombre_cap}' ya existe.")
            else:
                supabase.table("productos").insert({"modulo": m_new, "nombre": nombre_cap, "precio": float(p_new), "cantidad": int(c_new), "created_at": datetime.now().isoformat()}).execute()
                st.success("✅ Guardado"); time.sleep(1); st.rerun()

st.divider()

# CARGA DE DATOS
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

t_comida, t_hogar, t_compras = st.tabs(["🍎 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

def render_tabla_gestion(df_sec, mod):
    if not df_sec.empty:
        df_sec['Subtotal $'] = df_sec['precio'] * df_sec['cantidad']
        df_sec['Subtotal Bs.'] = df_sec['Subtotal $'] * TASA_BCV_FIJA
        
        # ELIMINACIÓN MÚLTIPLE (NUEVA FUNCIÓN)
        with st.expander(f"🗑️ Eliminar varios de {mod}"):
            seleccionados = st.multiselect("Selecciona productos para eliminar:", df_sec['nombre'].tolist(), key=f"multi_{mod}")
            if st.button(f"Eliminar seleccionados ({len(seleccionados)})", key=f"btn_multi_{mod}"):
                for p_del in seleccionados:
                    supabase.table("productos").delete().eq("modulo", mod).eq("nombre", p_del).execute()
                st.rerun()

        edited_df = st.data_editor(df_sec[["id", "nombre", "precio", "cantidad", "Subtotal $", "Subtotal Bs."]], use_container_width=True, hide_index=True, disabled=["id", "Subtotal $", "Subtotal Bs."], key=f"editor_{mod}")
        
        total_usd = (edited_df['precio'] * edited_df['cantidad']).sum()
        c1, c2 = st.columns(2)
        c1.metric(f"Total {mod} ($)", f"{total_usd:.2f} $")
        c2.metric(f"Total {mod} (Bs)", f"{(total_usd * TASA_BCV_FIJA):,.2f} Bs")
        
        if not edited_df.equals(df_sec[["id", "nombre", "precio", "cantidad", "Subtotal $", "Subtotal Bs."]]):
            if st.button(f"💾 Guardar Cambios en {mod}", key=f"save_{mod}"):
                for _, row in edited_df.iterrows():
                    supabase.table("productos").update({"precio": float(row['precio']), "cantidad": int(row['cantidad'])}).eq("id", row['id']).execute()
                st.rerun()
    else: st.info(f"{mod} vacío.")

with t_comida:
    df_c = df_all[df_all['modulo'] == 'Comida'].copy() if not df_all.empty else pd.DataFrame()
    if not df_c.empty:
        render_tabla_gestion(df_c, "Comida")
        st.divider()
        st.subheader("⚙️ Operaciones de Inventario")
        p_sel = st.selectbox("Seleccionar producto:", df_c['nombre'].tolist(), key="sel_c")
        item = df_c[df_c['nombre'] == p_sel].iloc[0]
        c1, c2 = st.columns(2)
        if c1.button(f"📦 Enviar '{p_sel}' a Compras"):
            check = supabase.table("productos").select("*").eq("modulo", "Por Comprar").eq("nombre", item['nombre']).execute()
            if check.data:
                supabase.table("productos").update({"cantidad": int(check.data[0]['cantidad']) + int(item['cantidad'])}).eq("id", check.data[0]['id']).execute()
            else:
                supabase.table("productos").insert({"modulo": "Por Comprar", "nombre": item['nombre'], "precio": item['precio'], "cantidad": item['cantidad']}).execute()
            supabase.table("productos").delete().eq("id", item['id']).execute()
            st.rerun()
        if c2.button(f"🗑️ Eliminar '{p_sel}'"):
            supabase.table("productos").delete().eq("id", int(item['id'])).execute()
            st.rerun()
        st.divider()
        st.subheader("👨‍🍳 El Chef: Menú de 12 Opciones")
        if st.button("🍴 Generar Menú"):
            menu = generar_menu_inteligente(df_c['nombre'].tolist())
            for mom, platos in menu.items():
                with st.expander(mom):
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
