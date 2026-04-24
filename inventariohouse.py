import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI Pro", layout="wide")

# --- CONEXIÓN SUPABASE ---
@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar_supabase()

# --- 1. LÓGICA DE RECETAS DETALLADAS ---
def generar_menu_detallado(productos):
    p_list = [str(p).lower() for p in productos]
    tiene = lambda x: any(x in item for item in p_list)
    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}

    def agregar(bloque, titulo, receta, tipo="Sencilla"):
        icono = "⚡" if tipo == "Sencilla" else "⭐"
        menu[bloque].append({"titulo": f"{icono} {titulo}", "receta": receta})

    # --- DESAYUNOS ---
    if tiene("harina"):
        agregar("☀️ DESAYUNO", "Arepas Asadas Tradicionales", 
                "1. En un bol, vierte 1 taza de agua y una pizca de sal. 2. Agrega la harina de maíz poco a poco mientras amasas con la mano hasta que la masa esté suave y no se pegue a los dedos. 3. Forma bolas del tamaño de una naranja y aplástalas para darles forma de disco. 4. Cocina en un budare o sartén caliente a fuego medio durante 5-7 minutos por cada lado hasta que al golpearlas suenen huecas. 5. Abre con un cuchillo y rellena inmediatamente con queso para que se funda.")
        
        if tiene("carne"):
            agregar("☀️ DESAYUNO", "Arepa Pelúa Gourmet Paso a Paso", 
                    "1. Sazona la carne bistec con sal y una pizca de comino. 2. En un sartén con una cucharadita de aceite, cocina la carne a fuego alto hasta que dore, luego desmenúzala o córtala en tiritas muy finas. 3. Prepara la arepa según el método tradicional. 4. Rellena la arepa colocando primero una capa generosa de carne caliente y cubre con una montaña de queso rallado fino. El calor de la carne debe derretir el queso ligeramente.", "Gourmet")

    # --- ALMUERZOS ---
    if tiene("pasta") or tiene("arroz"):
        base = "Pasta" if tiene("pasta") else "Arroz"
        agregar("🍴 ALMUERZO", f"{base} a la Mantequilla y Queso", 
                f"1. Hierve abundante agua con sal en una olla. 2. Agrega la {base} (si es pasta, cocina 8-10 min; si es arroz, usa 2 tazas de agua por 1 de arroz a fuego bajo). 3. Escurre y, mientras sigue caliente, agrega una cucharada de mantequilla y remueve. 4. Sirve en un plato hondo y ralla el queso por encima para que cree una capa cremosa.")
        
        if tiene("carne") and tiene("comino"):
            agregar("🍴 ALMUERZO", "Salteado de Carne al Estilo Criollo", 
                    f"1. Corta la carne en tiras de 2cm. 2. En un bol, mezcla la carne con sal y media cucharadita de comino. 3. Calienta un sartén con un chorrito de aceite hasta que humee. 4. Echa la carne y deja que selle sin moverla por 2 min. 5. Saltea 3 min más. 6. Sirve junto a una porción de {base}, asegurándote de verter los jugos de la carne sobre el carbohidrato para dar más sabor.", "Gourmet")

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

# --- 2. TASA DE CONVERSIÓN (SIDEBAR) ---
st.sidebar.title("💰 Conversor de Moneda")
tasa_bcv = st.sidebar.number_input("Tasa BCV (Bs/$)", min_value=1.0, value=36.5, step=0.1)

# --- INTERFAZ PRINCIPAL ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# REGISTRO
with st.expander("➕ REGISTRAR NUEVO PRODUCTO"):
    c1, c2 = st.columns(2)
    m_n = c1.selectbox("Lista", ["Comida", "Hogar", "Por Comprar"])
    n_n = c1.text_input("Nombre")
    p_n, c_n = c2.number_input("Precio $", min_value=0.0), c2.number_input("Cantidad", min_value=0)
    if st.button("🚀 GUARDAR"):
        if n_n:
            supabase.table("productos").insert({"modulo": m_n, "nombre": n_n.capitalize(), "precio": p_n, "cantidad": c_n, "created_at": datetime.now().isoformat()}).execute()
            st.success("Guardado"); time.sleep(1); st.rerun()

# DATOS
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

t_comida, t_hogar, t_compras = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

# --- 4. GESTIÓN DE COMIDA (SIN ELIMINACIÓN DIRECTA) ---
with t_comida:
    df_c = df_all[df_all['modulo'] == 'Comida'].copy() if not df_all.empty else pd.DataFrame()
    if not df_c.empty:
        st.write("### Inventario de Alimentos")
        # Mostrar tabla informativa
        st.dataframe(df_c[["nombre", "precio", "cantidad"]], use_container_width=True, hide_index=True)
        
        st.write("---")
        st.write("⚙️ **Acciones de Producto**")
        p_seleccionado = st.selectbox("Selecciona un producto para gestionar:", df_c['nombre'].tolist())
        datos_p = df_c[df_c['nombre'] == p_seleccionado].iloc[0]

        col_act, col_mov, col_el = st.columns(3)
        
        with col_mov:
            if st.button(f"🛒 Enviar '{p_seleccionado}' a Por Comprar"):
                st.warning(f"¿Confirmas mover {p_seleccionado}?")
                if st.button("SÍ, CONFIRMO MOVIMIENTO"):
                    supabase.table("productos").update({"modulo": "Por Comprar"}).eq("id", datos_p['id']).execute()
                    st.rerun()

        with col_el:
            if st.button(f"🗑️ Eliminar '{p_seleccionado}' permanentemente"):
                st.error(f"¿Estás seguro de eliminar {p_seleccionado}?")
                if st.button("SÍ, ELIMINAR AHORA"):
                    supabase.table("productos").delete().eq("id", datos_p['id']).execute()
                    st.rerun()
        
        # EL CHEF DENTRO DE COMIDA
        st.divider()
        st.subheader("👨‍🍳 Ideas del Chef (Detalladas)")
        if st.button("🪄 Generar Menú Paso a Paso"):
            stock = df_c[df_c['cantidad'] > 0]['nombre'].tolist()
            menu = generar_menu_detallado(stock)
            for momento, platos in menu.items():
                if platos:
                    st.markdown(f"#### {momento}")
                    for p in platos:
                        with st.expander(p['titulo']):
                            st.write(p['receta'])
    else:
        st.info("No hay comida.")

# --- 3. HOGAR Y COMPRAS (SUMATORIAS Y CONVERSIÓN) ---
def mostrar_seccion_con_totales(nombre_modulo, df_seccion):
    if not df_seccion.empty:
        # Añadir columna de bolívares calculada
        df_seccion['Precio Bs.'] = df_seccion['precio'] * tasa_bcv
        
        st.data_editor(df_seccion[["id", "nombre", "precio", "Precio Bs.", "cantidad"]], use_container_width=True, hide_index=True, disabled=["Precio Bs."])
        
        total_usd = (df_seccion['precio'] * df_seccion['cantidad']).sum()
        total_bs = total_usd * tasa_bcv
        
        c1, c2 = st.columns(2)
        c1.metric("Total en Dólares", f"{total_usd:.2f} $")
        c2.metric("Total en Bolívares (BCV)", f"{total_bs:.2f} Bs.")
    else:
        st.info(f"Lista de {nombre_modulo} vacía.")

with t_hogar:
    df_h = df_all[df_all['modulo'] == 'Hogar'].copy() if not df_all.empty else pd.DataFrame()
    mostrar_seccion_con_totales("Hogar", df_h)

with t_compras:
    df_p = df_all[df_all['modulo'] == 'Por Comprar'].copy() if not df_all.empty else pd.DataFrame()
    mostrar_seccion_con_totales("Por Comprar", df_p)
