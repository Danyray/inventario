import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI - Versión Final Blindada v3", layout="wide")

# --- CONEXIÓN ---
@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar_supabase()

# --- TASA BCV FIJA (REFERENCIA OFICIAL) ---
TASA_BCV_FIJA = 483.87 

# --- LÓGICA DEL CHEF SUPERIOR (12 OPCIONES TOTALES) ---
def generar_menu_inteligente(productos):
    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}

    def agregar(bloque, titulo, receta, tipo="Sencilla"):
        icono = "⚡ (Sencilla)" if tipo == "Sencilla" else "⭐ (Gourmet)"
        menu[bloque].append({"titulo": f"{icono} {titulo}", "receta": receta})

    # --- DESAYUNOS (4 OPCIONES) ---
    agregar("☀️ DESAYUNO", "Arepa de Maíz en Doble Cocción", "1. Hidratar harina (1:1.2 agua/harina) con sal. 2. Amasar 3 min. 3. Sellar en budare 4 min por lado. 4. Terminar 5 min en horno o tapado a fuego mínimo para inflar. Rellenar con queso rallado.")
    agregar("☀️ DESAYUNO", "Sándwich Tostado con Presión", "1. Untar mantequilla en ambas caras externas del pan. 2. Colocar queso en el centro. 3. Tostar en sartén aplicando presión física con otra olla o prensa 2 min por lado para compactar miga y fundir.")
    # Gourmet
    agregar("☀️ DESAYUNO", "Arepa Pelúa con Desglasado de Carne", "1. Sellar 150g de carne en tiras a fuego máximo hasta dorar. 2. Añadir 2 cdas de agua para recuperar los jugos del fondo del sartén. 3. Rellenar arepa asada con la carne jugosa y queso amarillo rallado grueso.", "Gourmet")
    agregar("☀️ DESAYUNO", "Omelette Cremoso con Técnica de Batido", "1. Batir 2 huevos con sal hasta espumar. 2. Verter en sartén con mantequilla a fuego bajo. 3. Remover el centro con espátula mientras cuaja para crear textura sedosa. 4. Doblar y servir sobre pan tostado.", "Gourmet")

    # --- ALMUERZOS (4 OPCIONES) ---
    agregar("🍴 ALMUERZO", "Pasta con Emulsión de Almidón", "1. Cocinar pasta al dente. 2. Reservar media taza del agua de cocción (rica en almidón). 3. Mezclar pasta caliente, mantequilla y el agua reservada. 4. Batir vigorosamente para crear una salsa que brille sin usar crema.")
    agregar("🍴 ALMUERZO", "Arroz Blanco Graneado Técnico", "1. Sofreír el arroz en aceite con ajo 2 min antes de añadir agua (Nacarado). 2. Añadir agua hirviendo (relación 2:1). 3. Cocinar tapado 18 min sin abrir la tapa para que el vapor termine la cocción perfecta.")
    # Gourmet
    agregar("🍴 ALMUERZO", "Bistec Sellado 'Maitre d'Hotel'", "1. Secar la carne con papel antes de cocinar. 2. Sellar en sartén de hierro muy caliente 3 min por lado. 3. Reposar 2 min sobre el arroz caliente para que los jugos se redistribuyan. Decorar con aros de cebolla caramelizados.", "Gourmet")
    agregar("🍴 ALMUERZO", "Salteado de Carne al Comino y Reducción", "1. Cubos de carne sazonados con sal y comino intenso. 2. Sellar a fuego alto. 3. Terminar con un chorrito de agua o caldo para crear una salsa oscura y potente. Servir con arroz moldeado en copa.", "Gourmet")

    # --- CENAS (4 OPCIONES) ---
    agregar("🌙 CENA", "Tostada de Maíz 'Crocante'", "1. Abrir una arepa ya cocida por la mitad. 2. Tostar ambas caras internas en el budare hasta que queden como galleta. 3. Agregar una capa fina de queso para una cena ligera y crujiente.")
    agregar("🌙 CENA", "Pasta 'Cacio e Pepe' Sencilla", "1. Pasta corta cocida. 2. Mezclar con abundante pimienta negra recién molida y el queso rallado más seco que tengas en stock. 3. Añadir agua de pasta para ligar.")
    # Gourmet
    agregar("🌙 CENA", "Panini Gourmet de Proteína Fundida", "1. Pan relleno con tiras de carne y doble porción de queso. 2. Envolver en papel aluminio y calentar en sartén con peso encima 4 min. 3. El vapor interno ablandará el pan mientras el exterior queda crocante.", "Gourmet")
    agregar("🌙 CENA", "Degustación de Queso y Especias", "1. Cortar queso en cubos de 1cm. 2. Saltear brevemente en sartén con comino y una pizca de azúcar hasta que los bordes doren. 3. Servir con trozos de pan tostado en punta.", "Gourmet")

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

# 1. REGISTRO AL INICIO (CON PROTECCIÓN ANTI-DUPLICADOS)
with st.expander("➕ REGISTRAR NUEVO PRODUCTO", expanded=True):
    f1, f2 = st.columns(2)
    m_new = f1.selectbox("Destino", ["Comida", "Hogar", "Por Comprar"])
    n_new = f1.text_input("Nombre del producto")
    p_new = f2.number_input("Precio Unitario $", min_value=0.0, format="%.2f")
    c_new = f2.number_input("Cantidad", min_value=1)
    
    if st.button("🚀 GUARDAR"):
        if n_new:
            nombre_cap = n_new.capitalize().strip()
            # VERIFICACIÓN DE DUPLICADOS
            existe = supabase.table("productos").select("*").eq("modulo", m_new).eq("nombre", nombre_cap).execute()
            if existe.data:
                st.error(f"⚠️ El producto '{nombre_cap}' ya existe en la tabla {m_new}. Modifica el existente si es necesario.")
            else:
                supabase.table("productos").insert({"modulo": m_new, "nombre": nombre_cap, "precio": float(p_new), "cantidad": int(c_new), "created_at": datetime.now().isoformat()}).execute()
                st.success("✅ Guardado exitosamente"); time.sleep(1); st.rerun()

st.divider()

# CARGA DE DATOS
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

t_comida, t_hogar, t_compras = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

# --- FUNCIÓN DE TABLAS RE-ACTIVAS ---
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

# --- PESTAÑA COMIDA (GESTIÓN + CHEF) ---
with t_comida:
    df_c = df_all[df_all['modulo'] == 'Comida'].copy() if not df_all.empty else pd.DataFrame()
    if not df_c.empty:
        render_tabla_gestion(df_c, "Comida")
        
        st.divider()
        st.subheader("⚙️ Operaciones de Inventario")
        p_sel = st.selectbox("Seleccionar producto para acción:", df_c['nombre'].tolist())
        item = df_c[df_c['nombre'] == p_sel].iloc[0]
        
        c1, c2 = st.columns(2)
        # MOVER A COMPRAS
        if c1.button(f"🛒 Enviar '{p_sel}' a Compras"): st.session_state.m_move = True
        if st.session_state.get('m_move'):
            if st.button("✅ Confirmar Envío"):
                check = supabase.table("productos").select("*").eq("modulo", "Por Comprar").eq("nombre", item['nombre']).execute()
                if check.data:
                    n_cant = int(check.data[0]['cantidad']) + int(item['cantidad'])
                    supabase.table("productos").update({"cantidad": n_cant}).eq("id", check.data[0]['id']).execute()
                else:
                    supabase.table("productos").update({"modulo": "Por Comprar"}).eq("id", item['id']).execute()
                supabase.table("productos").delete().eq("id", item['id']).execute()
                st.session_state.m_move = False; st.rerun()

        # ELIMINAR (CORREGIDO)
        if c2.button(f"🗑️ Eliminar '{p_sel}'"): st.session_state.m_del = True
        if st.session_state.get('m_del'):
            st.error(f"¿Eliminar '{p_sel}' permanentemente?")
            if st.button("🔥 SÍ, ELIMINAR"):
                # Corrección: Uso directo del ID del item filtrado para asegurar el borrado
                supabase.table("productos").delete().eq("id", int(item['id'])).execute()
                st.session_state.m_del = False
                st.success("Producto eliminado."); time.sleep(1); st.rerun()

        st.divider()
        st.subheader("👨‍🍳 El Chef: Menú de 12 Opciones")
        if st.button("🪄 Generar Todas las Opciones (Desayuno, Almuerzo y Cena)"):
            menu = generar_menu_inteligente(df_c[df_c['cantidad'] > 0]['nombre'].tolist())
            for m, platos in menu.items():
                st.write(f"### {m}")
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
