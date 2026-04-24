import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI - Versión Final Blindada", layout="wide")

# --- CONEXIÓN ---
@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar_supabase()

# --- TASA BCV FIJA (REFERENCIA OFICIAL) ---
TASA_BCV_FIJA = 483.87 

# --- LÓGICA DEL CHEF ESPECÍFICO (4 OPCIONES DETALLADAS) ---
def generar_menu_inteligente(productos):
    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}

    def agregar(bloque, titulo, receta, tipo="Sencilla"):
        icono = "⚡ (Sencilla)" if tipo == "Sencilla" else "⭐ (Gourmet)"
        menu[bloque].append({"titulo": f"{icono} {titulo}", "receta": receta})

    # --- DESAYUNOS ---
    agregar("☀️ DESAYUNO", "Arepa de Maíz con Sellado en Budare", "1. Hidratar 1 taza de harina con 1.2 tazas de agua y sal marina. 2. Amasar 4 min hasta eliminar grumos. 3. Formar discos de 2.5cm de grosor. 4. Sellar en budare caliente 5 min por lado hasta formar costra. 5. Terminar 3 min a fuego bajo para cocción interna. Rellenar con queso rallado fresco.")
    agregar("☀️ DESAYUNO", "Sándwich de Presión en Mantequilla", "1. Untar 10g de mantequilla en las caras externas del pan. 2. Colocar 2 láminas de queso en el centro. 3. Tostar en sartén aplicando presión con una espátula durante 2 min por lado a fuego medio hasta lograr un dorado uniforme y fundido total.")
    # Gourmet
    agregar("☀️ DESAYUNO", "Arepa Pelúa con Carne en Reducción de Jugos", "1. Sellar 150g de carne en tiras finas con comino y sal a fuego máximo (Técnica de salteado). 2. Agregar 2 cdas de agua para desglasar el sartén y crear una salsa corta. 3. Abrir arepa asada, untar mantequilla y rellenar con la carne y queso amarillo rallado fino para que gratine con el calor residual.", "Gourmet")
    agregar("☀️ DESAYUNO", "Omelette de Técnica Francesa", "1. Batir 2 huevos con una pizca de sal. 2. Verter en sartén con fuego mínimo y mantequilla. 3. Remover el centro constantemente para crear cremosidad. 4. Doblar en forma de media luna antes de que dore la base. Servir sobre arepa o pan tostado con lluvia de comino.", "Gourmet")

    # --- ALMUERZOS ---
    agregar("🍴 ALMUERZO", "Pasta al Dente con Emulsión de Mantequilla", "1. Hervir 1L de agua por cada 100g de pasta. 2. Cocinar 8-10 min (según empaque). 3. Antes de colar, reservar 1/4 taza de agua de cocción. 4. Mezclar pasta, agua reservada, mantequilla y queso para crear una salsa emulsionada que se adhiera al grano.")
    agregar("🍴 ALMUERZO", "Arroz Blanco con Huevo Escalfado en Aceite", "1. Sofreír arroz con ajo antes del agua para soltar el grano. 2. Cocinar a fuego mínimo tapado 18 min. 3. Fríe un huevo en abundante aceite caliente bañando la yema con una cuchara (baño de aceite) para que quede blanca por fuera y líquida por dentro. Servir sobre el arroz.")
    # Gourmet
    agregar("🍴 ALMUERZO", "Carne al Comino con Glaseado de Sartén", "1. Cortar carne en cubos uniformes de 2cm. 2. Sazonar con sal y comino molido. 3. Sellar en aceite caliente sin amontonar para evitar que la carne suelte agua. 4. Al dorar, apagar el fuego y tapar 2 min para redistribuir jugos. Servir con arroz moldeado en copa.", "Gourmet")
    agregar("🍴 ALMUERZO", "Bistec 'Maitre' con Cebollas Caramelizadas", "1. Cocinar bistec a fuego alto 3 min por lado (término medio). 2. En el mismo sartén, agregar cebolla en aros con una pizca de azúcar y sal hasta que doren. 3. Servir la cebolla sobre la carne para que los jugos se mezclen. Acompañar con pasta emulsionada.", "Gourmet")

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

# --- SIDEBAR: TASA Y CONVERSOR ---
st.sidebar.title("💰 Referencia BCV")
st.sidebar.info(f"Tasa Oficial: **{TASA_BCV_FIJA} Bs/$**")
st.sidebar.divider()
st.sidebar.subheader("🧮 Conversor Rápido")
monto_dol = st.sidebar.number_input("Dólares ($)", min_value=0.0, step=1.0, format="%.2f")
if monto_dol > 0:
    st.sidebar.success(f"Equivale a: **{(monto_dol * TASA_BCV_FIJA):,.2f} Bs**")

# --- INTERFAZ PRINCIPAL ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# 1. REGISTRO AL INICIO
with st.expander("➕ REGISTRAR NUEVO PRODUCTO", expanded=True):
    f1, f2 = st.columns(2)
    m_new = f1.selectbox("Destino", ["Comida", "Hogar", "Por Comprar"])
    n_new = f1.text_input("Nombre del producto")
    p_new = f2.number_input("Precio Unitario $", min_value=0.0, format="%.2f")
    c_new = f2.number_input("Cantidad", min_value=1)
    if st.button("🚀 GUARDAR"):
        if n_new:
            supabase.table("productos").insert({"modulo": m_new, "nombre": n_new.capitalize(), "precio": float(p_new), "cantidad": int(c_new), "created_at": datetime.now().isoformat()}).execute()
            st.success("Guardado"); time.sleep(1); st.rerun()

st.divider()

# CARGA DE DATOS
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

t_comida, t_hogar, t_compras = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

# --- FUNCIÓN PARA RENDERIZAR TABLAS CON ACTUALIZACIÓN EN TIEMPO REAL ---
def render_tabla_gestion(df_sec, mod):
    if not df_sec.empty:
        # Cálculo inicial
        df_sec['Subtotal $'] = df_sec['precio'] * df_sec['cantidad']
        df_sec['Subtotal Bs.'] = df_sec['Subtotal $'] * TASA_BCV_FIJA
        
        # El data_editor permite editar y recalcular
        edited_df = st.data_editor(
            df_sec[["id", "nombre", "precio", "cantidad", "Subtotal $", "Subtotal Bs."]], 
            use_container_width=True, hide_index=True, 
            disabled=["id", "Subtotal $", "Subtotal Bs."],
            key=f"editor_{mod}"
        )
        
        # Recalcular totales basados en la edición actual
        total_usd = (edited_df['precio'] * edited_df['cantidad']).sum()
        total_bs = total_usd * TASA_BCV_FIJA
        
        c1, c2 = st.columns(2)
        c1.metric(f"Total {mod} ($)", f"{total_usd:.2f} $")
        c2.metric(f"Total {mod} (Bs)", f"{total_bs:,.2f} Bs")
        
        # Botón para persistir cambios si se editó algo
        if not edited_df.equals(df_sec[["id", "nombre", "precio", "cantidad", "Subtotal $", "Subtotal Bs."]]):
            if st.button(f"💾 Guardar Cambios de {mod}"):
                for index, row in edited_df.iterrows():
                    supabase.table("productos").update({"precio": float(row['precio']), "cantidad": int(row['cantidad'])}).eq("id", row['id']).execute()
                st.success("Cambios guardados"); time.sleep(1); st.rerun()
    else:
        st.info(f"{mod} vacío.")

# --- PESTAÑA COMIDA (GESTIÓN + CHEF) ---
with t_comida:
    df_c = df_all[df_all['modulo'] == 'Comida'].copy() if not df_all.empty else pd.DataFrame()
    if not df_c.empty:
        render_tabla_gestion(df_c, "Comida")
        
        st.divider()
        st.subheader("⚙️ Operaciones de Inventario")
        p_sel = st.selectbox("Seleccionar producto:", df_c['nombre'].tolist())
        item = df_c[df_c['nombre'] == p_sel].iloc[0]
        
        c1, c2 = st.columns(2)
        if c1.button(f"🛒 Mover '{p_sel}' a Compras"): st.session_state.m_move = True
        if st.session_state.get('m_move'):
            if st.button("✅ Confirmar Envío"):
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
            if st.button("🔥 Confirmar Borrado"):
                supabase.table("productos").delete().eq("id", item['id']).execute()
                st.session_state.m_del = False; st.rerun()

        st.divider()
        st.subheader("👨‍🍳 Chef de Alta Especificación")
        if st.button("🪄 Generar Menú Gourmet Técnico"):
            menu = generar_menu_inteligente(df_c[df_c['cantidad'] > 0]['nombre'].tolist())
            for m, platos in menu.items():
                if platos:
                    st.write(f"### {m}")
                    cols = st.columns(2)
                    for idx, p in enumerate(platos):
                        with cols[idx % 2]:
                            with st.expander(p['titulo']): st.info(p['receta'])
    else: st.info("Sin comida registrada.")

with t_hogar:
    df_h = df_all[df_all['modulo'] == 'Hogar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla_gestion(df_h, "Hogar")

with t_compras:
    df_p = df_all[df_all['modulo'] == 'Por Comprar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla_gestion(df_p, "Por Comprar")
