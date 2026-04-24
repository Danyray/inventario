import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI Pro - Chef Edition", layout="wide")

# --- CONEXIÓN ---
@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar_supabase()

# --- LÓGICA DEL CHEF (PASO A PASO DETALLADO) ---
def generar_menu_paso_a_paso(productos):
    p_list = [str(p).lower() for p in productos]
    tiene = lambda x: any(x in item for item in p_list)
    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}

    def agregar(bloque, titulo, receta, tipo="Sencilla"):
        icono = "⚡" if tipo == "Sencilla" else "⭐"
        menu[bloque].append({"titulo": f"{icono} {titulo}", "receta": receta})

    # --- DESAYUNOS ---
    if tiene("harina de maiz") or tiene("harina pan"):
        agregar("☀️ DESAYUNO", "Arepas Asadas con Queso (Técnica Exacta)", 
                "1. En un bol, vierte 1.5 tazas de agua tibia con 1/2 cucharadita de sal. 2. Agrega 1 taza de harina de maíz poco a poco, mezclando con los dedos para evitar grumos. 3. Amasa 3 min hasta que esté compacta. 4. Forma discos de 10cm de diámetro y 2cm de grosor. 5. Calienta un sartén o budare a fuego medio-alto por 2 min. 6. Cocina la arepa 7 min por lado hasta que la costra esté firme. 7. Abre por el medio y coloca 50g de queso rallado.")
        
        if tiene("carne"):
            agregar("☀️ DESAYUNO", "Arepa Pelúa Gourmet (Sazonada)", 
                    "1. Corta 200g de carne en tiritas de 1cm. 2. Sazona con una pizca de comino y sal. 3. Calienta un sartén con aceite, añade la carne y cocina 5 min a fuego alto hasta que dore. 4. Prepara la arepa según el método anterior. 5. Rellena mezclando la carne caliente con queso rallado grueso para que el calor la funda.", "Gourmet")

    # --- ALMUERZOS ---
    if tiene("pasta"):
        agregar("🍴 ALMUERZO", "Pasta al Dente con Queso", 
                "1. Hierve 2 litros de agua con 1 cucharada de sal. 2. Añade la pasta y cocina exactos 9 minutos. 3. Antes de colar, guarda 3 cucharadas del agua de la pasta. 4. Cuela y regresa a la olla. 5. Mezcla con el agua reservada, una cucharada de mantequilla y queso rallado fino hasta que emulsione.")
        
        if tiene("carne") and tiene("comino"):
            agregar("🍴 ALMUERZO", "Lomito Salteado al Comino", 
                    "1. Corta la carne en cubos medianos. 2. Espolvorea comino y sal generosamente. 3. En un sartén humeante, sella la carne 3 min por lado sin moverla. 4. Sirve la carne sobre la pasta cocida para que los jugos se mezclen con el queso.", "Gourmet")

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

# --- INTERFAZ ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# 1. REGISTRO AL INICIO
with st.expander("➕ REGISTRAR NUEVO PRODUCTO", expanded=True):
    f1, f2 = st.columns(2)
    m_new = f1.selectbox("Lista de Destino", ["Comida", "Hogar", "Por Comprar"])
    n_new = f1.text_input("Nombre del artículo")
    p_new = f2.number_input("Precio por unidad ($)", min_value=0.0, step=0.01)
    c_new = f2.number_input("Cantidad inicial", min_value=1)
    if st.button("🚀 GUARDAR REGISTRO"):
        if n_new:
            supabase.table("productos").insert({"modulo": m_new, "nombre": n_new.capitalize(), "precio": float(p_new), "cantidad": int(c_new), "created_at": datetime.now().isoformat()}).execute()
            st.success("✅ Producto agregado."); time.sleep(1); st.rerun()

st.sidebar.title("💰 Cambio del Día")
tasa_bcv = st.sidebar.number_input("Tasa BCV (Bs/$)", min_value=1.0, value=36.5, format="%.2f")

# --- CARGA Y PESTAÑAS ---
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

t_comida, t_hogar, t_compras = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

# --- PESTAÑA COMIDA (INCLUYE CHEF) ---
with t_comida:
    df_c = df_all[df_all['modulo'] == 'Comida'].copy() if not df_all.empty else pd.DataFrame()
    if not df_c.empty:
        st.dataframe(df_c[["id", "nombre", "precio", "cantidad"]], use_container_width=True, hide_index=True)
        st.divider()
        st.subheader("⚙️ Gestión de Alimentos")
        p_sel = st.selectbox("Producto a gestionar:", df_c['nombre'].tolist())
        item = df_c[df_c['nombre'] == p_sel].iloc[0]
        
        c1, c2 = st.columns(2)
        if c1.button(f"🛒 Enviar '{p_sel}' a Compras"):
            st.session_state.c_move = True
        
        if st.session_state.get('c_move'):
            if st.button(f"⚠️ CONFIRMAR: ¿Mover {p_sel}?"):
                # Anti-duplicados
                existe = supabase.table("productos").select("*").eq("modulo", "Por Comprar").eq("nombre", item['nombre']).execute()
                if existe.data:
                    nueva_cant = int(existe.data[0]['cantidad']) + int(item['cantidad'])
                    supabase.table("productos").update({"cantidad": nueva_cant}).eq("id", existe.data[0]['id']).execute()
                    supabase.table("productos").delete().eq("id", item['id']).execute()
                else:
                    supabase.table("productos").update({"modulo": "Por Comprar"}).eq("id", item['id']).execute()
                st.session_state.c_move = False; st.rerun()

        if c2.button(f"🗑️ Eliminar '{p_sel}'"):
            st.session_state.c_del = True
        
        if st.session_state.get('c_del'):
            if st.button(f"🔥 SÍ, ELIMINAR {p_sel} PERMANENTEMENTE"):
                supabase.table("productos").delete().eq("id", item['id']).execute()
                st.session_state.c_del = False; st.rerun()

        # EL CHEF SÓLO AQUÍ
        st.divider()
        st.subheader("👨‍🍳 Ideas del Chef Gourmet")
        if st.button("🪄 Generar Recetas Paso a Paso"):
            stock = df_c[df_c['cantidad'] > 0]['nombre'].tolist()
            menu = generar_menu_paso_a_paso(stock)
            for m, recetas in menu.items():
                if recetas:
                    st.write(f"### {m}")
                    for r in recetas:
                        with st.expander(r['titulo']): st.info(r['receta'])
    else: st.info("Sección de comida vacía.")

# --- LÓGICA DE TABLAS FINANCIERAS (HOGAR Y COMPRAS) ---
def render_tabla_pro(df_sec, mod_name):
    if not df_sec.empty:
        df_sec['Total USD'] = df_sec['precio'] * df_sec['cantidad']
        df_sec['Total Bs.'] = df_sec['Total USD'] * tasa_bcv
        st.data_editor(df_sec[["id", "nombre", "precio", "cantidad", "Total USD", "Total Bs."]], 
                       use_container_width=True, hide_index=True, disabled=["Total USD", "Total Bs."], key=f"ed_{mod_name}")
        t_usd, t_bs = df_sec['Total USD'].sum(), df_sec['Total Bs.'].sum()
        c1, c2 = st.columns(2)
        c1.metric(f"Monto Total {mod_name}", f"{t_usd:.2f} $")
        c2.metric(f"Monto Total {mod_name}", f"{t_bs:.2f} Bs")
    else: st.info(f"Sin registros en {mod_name}.")

with t_hogar:
    df_h = df_all[df_all['modulo'] == 'Hogar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla_pro(df_h, "Hogar")

with t_compras:
    df_p = df_all[df_all['modulo'] == 'Por Comprar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla_pro(df_p, "Por Comprar")
