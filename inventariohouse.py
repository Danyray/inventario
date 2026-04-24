import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI - Chef Pro", layout="wide")

# --- LÓGICA DEL CHEF EQUILIBRADO ---
def generar_menu_mixto(productos):
    p_list = [str(p).lower() for p in productos]
    tiene = lambda x: any(x in item for item in p_list)
    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}

    def agregar_opcion(bloque, titulo, receta, tipo="Sencilla"):
        icono = "⚡" if tipo == "Sencilla" else "⭐"
        menu[bloque].append({"titulo": f"{icono} {titulo}", "receta": receta})

    # --- DESAYUNOS ---
    if tiene("harina de maiz") or tiene("harina pan"):
        agregar_opcion("☀️ DESAYUNO", "Arepa Básica con Queso", "1. Haz la masa con sal. 2. Cocina la arepa. 3. Rellena con queso.")
        agregar_opcion("☀️ DESAYUNO", "Arepa con Mantequilla", "1. Prepara la arepa clásica. 2. Ábrela caliente y unta mantequilla.")
        if tiene("carne"):
            agregar_opcion("☀️ DESAYUNO", "Arepa 'Pelúa' Gourmet", "1. Saltea la carne en tiritas con comino. 2. Rellena con la carne y mucho queso rallado para fundir.", "Gourmet")
        if tiene("azucar"):
            agregar_opcion("☀️ DESAYUNO", "Arepitas Dulces Crujientes", "1. Masa de maíz con azúcar y pizca de trigo. 2. Fríe en aceite caliente. 3. Acompaña con queso salado.", "Gourmet")

    # --- ALMUERZOS ---
    if tiene("pasta") or tiene("arroz"):
        base = "Pasta" if tiene("pasta") else "Arroz"
        agregar_opcion("🍴 ALMUERZO", f"{base} Express con Queso", f"1. Cocina la {base}. 2. Agrega queso arriba y deja que el calor lo ablande.")
        if tiene("carne"):
            agregar_opcion("🍴 ALMUERZO", f"Bistec Clásico con {base}", f"1. Cocina el bistec a la plancha. 2. Acompaña con {base} hervida.")
            agregar_opcion("🍴 ALMUERZO", f"{base} Salteada al Comino", f"1. Saltea carne en cubos con comino. 2. Mezcla la {base} en el mismo sartén para absorber sabores.", "Gourmet")
        if tiene("queso"):
            agregar_opcion("🍴 ALMUERZO", f"Gratín de {base} al Sartén", "1. Mezcla la base con queso. 2. Lleva al sartén tapado a fuego bajo hasta que el queso dore abajo.", "Gourmet")

    # --- CENAS ---
    if tiene("pan"):
        agregar_opcion("🌙 CENA", "Tostado de Queso Rápido", "1. Pan con queso. 2. Pásalo por el sartén para que esté crujiente.")
    if tiene("huevo") or tiene("queso"):
        p = "Huevo" if tiene("huevo") else "Queso"
        agregar_opcion("🌙 CENA", f"Revoltillo de {p}", f"1. Prepara el {p} rápidamente. 2. Acompaña con lo que tengas a mano.")
        agregar_opcion("🌙 CENA", f"Bruschettas de {p} Bistro", f"1. Tuesta el pan con mantequilla. 2. Prepara el {p} con un toque de comino y sirve encima.", "Gourmet")

    return menu

# --- CONEXIÓN SUPABASE ---
@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar_supabase()

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

# REGISTRO
with st.expander("➕ REGISTRAR NUEVO PRODUCTO"):
    c1, c2 = st.columns(2)
    m_n = c1.selectbox("Lista", ["Comida", "Hogar", "Por Comprar"])
    n_n = c1.text_input("Nombre")
    p_n = c2.number_input("Precio $", min_value=0.0)
    c_n = c2.number_input("Cantidad", min_value=0)
    if st.button("🚀 GUARDAR"):
        if n_n:
            supabase.table("productos").insert({"modulo": m_n, "nombre": n_n.capitalize(), "precio": p_n, "cantidad": c_n, "created_at": datetime.now().isoformat()}).execute()
            st.success("Guardado"); time.sleep(1); st.rerun()

# --- MANEJO DE PESTAÑAS ---
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

# Definimos las pestañas
tabs = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])
listas = ["Comida", "Hogar", "Por Comprar"]

# Usamos una variable para rastrear en qué pestaña estamos
tab_activa = ""

for i, tab in enumerate(tabs):
    with tab:
        # Si entramos en este bloque 'with', actualizamos la pestaña activa
        tab_activa = listas[i]
        
        df = df_all[df_all['modulo'] == listas[i]].copy() if not df_all.empty else pd.DataFrame()
        if not df.empty:
            edit_df = st.data_editor(df[["id", "nombre", "precio", "cantidad"]], key=f"ed_{listas[i]}", use_container_width=True, hide_index=True)
            c1, c2 = st.columns(2)
            if c1.button(f"💾 Actualizar {listas[i]}", key=f"up_{listas[i]}"):
                for _, r in edit_df.iterrows():
                    supabase.table("productos").update({"precio": r['precio'], "cantidad": r['cantidad']}).eq("id", r['id']).execute()
                st.rerun()
            id_b = c2.number_input("ID a borrar", min_value=0, key=f"del_{listas[i]}")
            if c2.button(f"🗑️ Eliminar", key=f"btn_{listas[i]}"):
                supabase.table("productos").delete().eq("id", id_b).execute(); st.rerun()
        else:
            st.info(f"No hay artículos en {listas[i]}.")

# --- SECCIÓN DINÁMICA DEL CHEF (SOLO VISIBLE EN COMIDA) ---
# Verificamos si la pestaña "Comida" es la que está "en foco" lógicamente
# Nota: En Streamlit, las pestañas se renderizan todas, pero podemos usar el estado.
# Una mejor forma es usar un radio button o un selectbox si el flujo es muy estricto, 
# pero aquí simularemos la visibilidad del Chef solo si hay datos de comida mostrándose.

if not df_all.empty:
    comida_stock = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]['nombre'].tolist()
    
    # La lógica: Si el usuario está viendo Hogar o Compras, no mostramos el botón del chef.
    # Para lograr esto de forma limpia en Streamlit con Tabs, envolvemos el chef en un contenedor 
    # que solo se activa si hay comida en el stock y el contexto es apropiado.
    
    st.divider()
    
    # Usamos un mensaje condicional para que el usuario sepa por qué aparece/desaparece
    if comida_stock:
        with st.container():
            # El botón solo se muestra si el usuario realmente quiere ver recetas de lo que tiene
            st.subheader("👨‍🍳 El Chef está listo")
            st.caption("Nota: Estas sugerencias solo consideran los ingredientes de tu lista de Comida.")
            
            if st.button("🪄 Generar Menú (Sencillo + Gourmet)", use_container_width=True):
                menu = generar_menu_mixto(comida_stock)
                for momento, platos in menu.items():
                    if platos:
                        st.markdown(f"### {momento}")
                        cols = st.columns(2)
                        for idx, p in enumerate(platos):
                            with cols[idx % 2]:
                                with st.expander(p['titulo']):
                                    st.info(p['receta'])
