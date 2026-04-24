import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI Pro v2", layout="wide")

# --- CONEXIÓN ---
@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar_supabase()

# --- RECETAS PASO A PASO (SIN IMAGINACIÓN) ---
def generar_menu_detallado(productos):
    p_list = [str(p).lower() for p in productos]
    tiene = lambda x: any(x in item for item in p_list)
    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}

    def agregar(bloque, titulo, receta, tipo="Sencilla"):
        icono = "⚡" if tipo == "Sencilla" else "⭐"
        menu[bloque].append({"titulo": f"{icono} {titulo}", "receta": receta})

    if tiene("harina"):
        agregar("☀️ DESAYUNO", "Arepas Asadas (Paso a Paso)", 
                "1. En un bol limpio, vierte 1 taza de agua y 1/2 cucharadita de sal. 2. Agrega 1 taza de harina de maíz lentamente. 3. Amasa con la mano durante 3 minutos hasta eliminar grumos. 4. Deja reposar la masa 2 minutos. 5. Divide en porciones y forma discos de 2cm de grosor. 6. Calienta un sartén a fuego medio y cocina cada lado por 6 minutos hasta que doren. 7. Corta por la mitad y rellena.")
    
    if tiene("pasta"):
        agregar("🍴 ALMUERZO", "Pasta con Queso y Especias", 
                "1. Pon a hervir 2 litros de agua con una pizca de sal. 2. Agrega la pasta y cocina por 9 minutos (al dente). 3. Antes de escurrir, reserva media taza del agua de cocción. 4. Escurre la pasta y regrésala a la olla. 5. Agrega el agua reservada, una cucharada de mantequilla y el queso rallado. 6. Revuelve a fuego mínimo hasta que se cree una salsa cremosa.")

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

# --- TASA BCV (SIDEBAR) ---
st.sidebar.title("💰 Cambio del Día")
tasa_bcv = st.sidebar.number_input("Tasa BCV (Bs/$)", min_value=1.0, value=36.5, step=0.01, format="%.2f")

# --- CARGA DE DATOS ---
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# --- PESTAÑAS ---
t_comida, t_hogar, t_compras = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

# --- MODULO COMIDA ---
with t_comida:
    df_c = df_all[df_all['modulo'] == 'Comida'].copy() if not df_all.empty else pd.DataFrame()
    if not df_c.empty:
        st.dataframe(df_c[["id", "nombre", "precio", "cantidad"]], use_container_width=True, hide_index=True)
        
        st.write("---")
        st.subheader("⚙️ Gestión de Inventario")
        p_sel = st.selectbox("Elegir producto:", df_c['nombre'].tolist(), key="sel_comida")
        item = df_c[df_c['nombre'] == p_sel].iloc[0]

        c1, c2 = st.columns(2)
        
        # MOVER A POR COMPRAR (Lógica Anti-Duplicados)
        if c1.button(f"🛒 Mover '{p_sel}' a Compras"):
            st.session_state.confirm_move = True
        
        if st.session_state.get('confirm_move'):
            st.warning(f"¿Mover {p_sel} a la lista de compras?")
            if st.button("CONFIRMAR ENVÍO"):
                # Verificar si ya existe en Compras
                check = supabase.table("productos").select("*").eq("modulo", "Por Comprar").eq("nombre", item['nombre']).execute()
                if check.data:
                    # Si existe, sumamos cantidad
                    nueva_cant = check.data[0]['cantidad'] + item['cantidad']
                    supabase.table("productos").update({"cantidad": nueva_cant}).eq("id", check.data[0]['id']).execute()
                    supabase.table("productos").delete().eq("id", item['id']).execute()
                else:
                    # Si no existe, cambiamos el modulo
                    supabase.table("productos").update({"modulo": "Por Comprar"}).eq("id", item['id']).execute()
                
                st.session_state.confirm_move = False
                st.rerun()

        # ELIMINAR
        if c2.button(f"🗑️ Eliminar '{p_sel}'"):
            st.session_state.confirm_del = True
        
        if st.session_state.get('confirm_del'):
            st.error(f"¿Eliminar permanentemente {p_sel}?")
            if st.button("SÍ, ELIMINAR DEFINITIVAMENTE"):
                supabase.table("productos").delete().eq("id", item['id']).execute()
                st.session_state.confirm_del = False
                st.rerun()

        # CHEF
        st.divider()
        if st.button("👨‍🍳 Ver Recetas Paso a Paso"):
            recetas = generar_menu_detallado(df_c[df_c['cantidad'] > 0]['nombre'].tolist())
            for m, p in recetas.items():
                if p:
                    st.write(f"### {m}")
                    for r in p:
                        with st.expander(r['titulo']): st.write(r['receta'])
    else: st.info("No hay comida.")

# --- MÓDULOS CON CÁLCULOS CORRECTOS ---
def render_lista(nombre_mod, dataframe):
    if not dataframe.empty:
        # Cálculo correcto: Precio Individual * Cantidad * Tasa
        dataframe['Subtotal Bs.'] = (dataframe['precio'] * dataframe['cantidad']) * tasa_bcv
        
        st.data_editor(dataframe[["id", "nombre", "precio", "cantidad", "Subtotal Bs."]], 
                       use_container_width=True, hide_index=True, 
                       disabled=["Subtotal Bs."], key=f"editor_{nombre_mod}")
        
        # Totales generales
        total_usd = (dataframe['precio'] * dataframe['cantidad']).sum()
        total_bs = total_usd * tasa_bcv
        
        col1, col2 = st.columns(2)
        col1.metric("Total Acumulado ($)", f"{total_usd:.2f} $")
        col2.metric("Total Acumulado (Bs)", f"{total_bs:.2f} Bs")
        
        # Botón de actualización de precios/cantidades
        if st.button(f"💾 Guardar cambios en {nombre_mod}"):
            # Lógica para guardar cambios del data_editor si es necesario
            st.rerun()
    else:
        st.info(f"La lista de {nombre_mod} está vacía.")

with t_hogar:
    df_h = df_all[df_all['modulo'] == 'Hogar'].copy() if not df_all.empty else pd.DataFrame()
    render_lista("Hogar", df_h)

with t_compras:
    df_p = df_all[df_all['modulo'] == 'Por Comprar'].copy() if not df_all.empty else pd.DataFrame()
    render_lista("Por Comprar", df_p)

# REGISTRO (Al final para no estorbar)
st.divider()
with st.expander("➕ AGREGAR NUEVO PRODUCTO"):
    f1, f2 = st.columns(2)
    m_new = f1.selectbox("Destino", ["Comida", "Hogar", "Por Comprar"])
    n_new = f1.text_input("Nombre del producto")
    p_new = f2.number_input("Precio Unitario $", min_value=0.0, format="%.2f")
    c_new = f2.number_input("Cantidad inicial", min_value=1)
    if st.button("➕ REGISTRAR"):
        if n_new:
            supabase.table("productos").insert({
                "modulo": m_new, "nombre": n_new.capitalize(), 
                "precio": p_new, "cantidad": c_new, 
                "created_at": datetime.now().isoformat()
            }).execute()
            st.rerun()
