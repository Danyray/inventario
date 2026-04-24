import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI Pro - Chef Supremo", layout="wide")

# --- CONEXIÓN ---
@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar_supabase()

# --- LÓGICA DEL CHEF (4 OPCIONES POR TURNO + DETALLE MÁXIMO) ---
def generar_menu_supremo(productos):
    p_list = [str(p).lower() for p in productos]
    tiene = lambda x: any(x in item for item in p_list)
    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}

    def agregar(bloque, titulo, receta, tipo="Sencilla"):
        icono = "⚡ (Sencilla)" if tipo == "Sencilla" else "⭐ (Gourmet)"
        menu[bloque].append({"titulo": f"{icono} {titulo}", "receta": receta})

    # --- ☀️ DESAYUNOS (2 Sencillos + 2 Gourmet) ---
    if tiene("harina") or tiene("pan"):
        # Sencillos
        agregar("☀️ DESAYUNO", "Arepa Rellena Express", "1. Mezcla 1 taza de agua con sal. 2. Añade harina hasta que la masa no se pegue. 3. Haz un disco de 2cm y cocina 5 min por lado. 4. Abre y coloca queso rallado inmediatamente.")
        agregar("☀️ DESAYUNO", "Sándwich Tostado de Queso", "1. Toma dos rebanadas de pan. 2. Coloca queso en medio. 3. Calienta un sartén con una gota de aceite. 4. Tuesta el sándwich 2 min por lado apretándolo con una espátula.")
        # Gourmet
        if tiene("carne"):
            agregar("☀️ DESAYUNO", "Arepa Pelúa con Carne Sellada", "1. Corta la carne en tiritas de 1cm y sazona con sal y comino. 2. Cocina a fuego máximo 4 min hasta que dore. 3. Prepara la arepa tradicional. 4. Rellena con la carne caliente y cubre con una montaña de queso rallado fino para que gratine.", "Gourmet")
        if tiene("azucar"):
            agregar("☀️ DESAYUNO", "Arepitas Dulces Tradicionales", "1. A la masa de harina de maíz, agrega 1 cucharada de azúcar y una pizca de harina de trigo. 2. Forma arepas delgadas (1cm). 3. Fríe en aceite muy caliente hasta que se inflen. 4. Sirve con queso salado al lado.", "Gourmet")

    # --- 🍴 ALMUERZOS (2 Sencillos + 2 Gourmet) ---
    if tiene("pasta") or tiene("arroz"):
        base = "Pasta" if tiene("pasta") else "Arroz"
        # Sencillos
        agregar("🍴 ALMUERZO", f"{base} Hervida con Queso", f"1. Cocina el {base} en agua con sal (Pasta 9 min / Arroz 20 min). 2. Escurre. 3. Sirve caliente y agrega el queso rallado arriba para que se ablande.")
        if tiene("huevo"):
            agregar("🍴 ALMUERZO", f"{base} con Huevo frito", f"1. Prepara tu {base} normal. 2. Fríe un huevo dejando la yema blanda. 3. Sirve el huevo sobre el carbohidrato para que la yema sirva de salsa.")
        # Gourmet
        if tiene("carne"):
            agregar("🍴 ALMUERZO", "Salteado Criollo al Comino", f"1. Corta la carne en cubos. 2. Sazona con sal y bastante comino. 3. Sella en sartén caliente 5 min. 4. Mezcla con el {base} ya cocido y añade un chorrito del agua donde se cocinó el carbohidrato para dar cremosidad.", "Gourmet")
            agregar("🍴 ALMUERZO", f"Bistec Encebollado con {base}", f"1. Cocina el bistec entero sazonado con sal. 2. Si tienes cebolla, sofríela arriba. 3. Sirve con una porción de {base} moldeada en una taza para que se vea profesional.", "Gourmet")

    # --- 🌙 CENAS (2 Sencillos + 2 Gourmet) ---
    # Sencillos
    agregar("🌙 CENA", "Cena Ligera de Queso", "1. Corta el queso en cubos pequeños. 2. Si tienes pan o galletas, acompáñalo. 3. Una opción rápida sin cocinar.")
    if tiene("pasta"):
        agregar("🌙 CENA", "Pasta al Burro (Mantequilla)", "1. Cocina media porción de pasta. 2. Escurre bien. 3. Agrega mantequilla y sal. Mezcla hasta que brille.")
    # Gourmet
    if tiene("pan"):
        agregar("🌙 CENA", "Tostadas Bistro de Queso y Comino", "1. Tuesta el pan con mantequilla en el sartén. 2. Derrite queso aparte y agrégale una pizca de comino. 3. Vierte el queso fundido sobre el pan tostado.", "Gourmet")
    if tiene("carne"):
        agregar("🌙 CENA", "Wrap de Carne y Queso", "1. Usa una arepa muy delgada o pan. 2. Rellena con tiritas de carne salteadas y queso. 3. Envuelve y calienta 1 min más en el sartén.", "Gourmet")

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

# --- INTERFAZ PRINCIPAL ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# 1. REGISTRO AL INICIO (LO PRIMERO QUE SE VE)
with st.expander("➕ REGISTRAR NUEVO PRODUCTO", expanded=True):
    f1, f2 = st.columns(2)
    m_new = f1.selectbox("Lista de Destino", ["Comida", "Hogar", "Por Comprar"])
    n_new = f1.text_input("Nombre del artículo")
    p_new = f2.number_input("Precio por unidad ($)", min_value=0.0, step=0.01, format="%.2f")
    c_new = f2.number_input("Cantidad inicial", min_value=1, step=1)
    if st.button("🚀 GUARDAR REGISTRO"):
        if n_new:
            supabase.table("productos").insert({"modulo": m_new, "nombre": n_new.capitalize(), "precio": float(p_new), "cantidad": int(c_new), "created_at": datetime.now().isoformat()}).execute()
            st.success("✅ Producto guardado"); time.sleep(1); st.rerun()

st.sidebar.title("💰 Cambio del Día")
tasa_bcv = st.sidebar.number_input("Tasa BCV (Bs/$)", min_value=1.0, value=36.5, format="%.2f")

# CARGA DE DATOS
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

t_comida, t_hogar, t_compras = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

# --- PESTAÑA COMIDA (GESTIÓN + CHEF) ---
with t_comida:
    df_c = df_all[df_all['modulo'] == 'Comida'].copy() if not df_all.empty else pd.DataFrame()
    if not df_c.empty:
        st.dataframe(df_c[["id", "nombre", "precio", "cantidad"]], use_container_width=True, hide_index=True)
        
        st.write("---")
        st.subheader("⚙️ Gestión de Alimentos")
        p_sel = st.selectbox("Elegir producto para mover/eliminar:", df_c['nombre'].tolist())
        item = df_c[df_c['nombre'] == p_sel].iloc[0]
        
        c1, c2 = st.columns(2)
        if c1.button(f"🛒 Enviar '{p_sel}' a Compras"):
            st.session_state.confirm_move = True
        
        if st.session_state.get('confirm_move'):
            if st.button(f"✅ CONFIRMAR ENVÍO DE {p_sel}"):
                existe = supabase.table("productos").select("*").eq("modulo", "Por Comprar").eq("nombre", item['nombre']).execute()
                if existe.data:
                    nueva_cant = int(existe.data[0]['cantidad']) + int(item['cantidad'])
                    supabase.table("productos").update({"cantidad": nueva_cant}).eq("id", existe.data[0]['id']).execute()
                    supabase.table("productos").delete().eq("id", item['id']).execute()
                else:
                    supabase.table("productos").update({"modulo": "Por Comprar"}).eq("id", item['id']).execute()
                st.session_state.confirm_move = False; st.rerun()

        if c2.button(f"🗑️ Eliminar '{p_sel}'"):
            st.session_state.confirm_del = True
        
        if st.session_state.get('confirm_del'):
            if st.button(f"🔥 CONFIRMAR ELIMINACIÓN DE {p_sel}"):
                supabase.table("productos").delete().eq("id", item['id']).execute()
                st.session_state.confirm_del = False; st.rerun()

        # --- EL CHEF (SOLO VISIBLE AQUÍ) ---
        st.divider()
        st.subheader("👨‍🍳 Ideas del Chef Gourmet (4 Opciones por Turno)")
        if st.button("🪄 Generar Menú Sencillo + Gourmet"):
            stock = df_c[df_c['cantidad'] > 0]['nombre'].tolist()
            menu = generar_menu_supremo(stock)
            for momento, platos in menu.items():
                if platos:
                    st.write(f"### {momento}")
                    cols = st.columns(2)
                    for idx, p in enumerate(platos):
                        with cols[idx % 2]:
                            with st.expander(p['titulo']):
                                st.info(p['receta'])
    else:
        st.info("No hay comida registrada.")

# --- LÓGICA FINANCIERA CORREGIDA (HOGAR Y COMPRAS) ---
def render_tabla_financiera(df_sec, mod):
    if not df_sec.empty:
        # Cálculo exacto: (Precio * Cantidad) * Tasa
        df_sec['Total USD'] = df_sec['precio'] * df_sec['cantidad']
        df_sec['Total Bs.'] = df_sec['Total USD'] * tasa_bcv
        
        st.data_editor(df_sec[["id", "nombre", "precio", "cantidad", "Total USD", "Total Bs."]], 
                       use_container_width=True, hide_index=True, disabled=["Total USD", "Total Bs."], key=f"ed_{mod}")
        
        sum_usd = df_sec['Total USD'].sum()
        sum_bs = df_sec['Total Bs.'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric(f"Total {mod} ($)", f"{sum_usd:.2f} $")
        c2.metric(f"Total {mod} (Bs)", f"{sum_bs:.2f} Bs")
    else:
        st.info(f"Sección {mod} vacía.")

with t_hogar:
    df_h = df_all[df_all['modulo'] == 'Hogar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla_financiera(df_h, "Hogar")

with t_compras:
    df_p = df_all[df_all['modulo'] == 'Por Comprar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla_financiera(df_p, "Por Comprar")
