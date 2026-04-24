import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario MI❤️AMOR JYI", layout="wide")

# --- LÓGICA DEL CHEF PROFESIONAL 2.0 (18 RECETAS REALES) ---
def generar_menu_extendido(productos):
    # Diccionario de procesos lógicos
    procesos = {
        "Carne": "cortada en tiritas y salteada",
        "Pollo": "picado en cubos y dorado",
        "Huevo": "frito o en revoltillo",
        "Queso": "rallado o en rebanadas",
        "Mortadela": "frita o picadita",
        "Atun": "mezclado con un toque de mayonesa",
        "Salchicha": "hervida o sofrita"
    }

    # Clasificación
    proteinas = [p.capitalize() for p in productos if any(x in p.capitalize() for x in ["Carne", "Pollo", "Huevo", "Atun", "Cerdo", "Queso", "Mortadela", "Salchicha"])]
    carbohidratos = [p.capitalize() for p in productos if any(x in p.capitalize() for x in ["Arroz", "Pasta", "Harina", "Pan", "Papa", "Platano", "Yuca"])]
    
    # Asegurar ingredientes base
    prot = proteinas if proteinas else ["Huevo", "Queso", "Embutido"]
    carb = carbohidratos if carbohidratos else ["Harina pan", "Arroz", "Pasta"]
    
    def obtener_accion(nombre):
        for k, v in procesos.items():
            if k in nombre: return v
        return "cocinado a tu gusto"

    # Generación de 6 opciones por categoría
    menu = {
        "☀️ DESAYUNO": [],
        "🍴 ALMUERZO": [],
        "🌙 CENA": []
    }

    # Llenado de opciones (Lógica de repetición inteligente)
    for i in range(6):
        p_idx = i % len(prot)
        c_idx = i % len(carb)
        
        # Desayunos (Enfoque Arepas/Pan/Huevos)
        menu["☀️ DESAYUNO"].append({
            "titulo": f"Opción {i+1}: Arepa o Pan con {prot[p_idx]}",
            "receta": f"1. Prepara tu base (arepa de harina o pan tostado).\n2. Prepara el/la {prot[p_idx]} que esté {obtener_accion(prot[p_idx])}.\n3. Rellena y disfruta caliente.",
            "img": ""
        })
        
        # Almuerzos (Enfoque Arroz/Pasta/Proteína fuerte)
        menu["🍴 ALMUERZO"].append({
            "titulo": f"Opción {i+1}: {carb[c_idx]} con {prot[p_idx]}",
            "receta": f"1. Cocina el {carb[c_idx]} (hervido o al dente).\n2. Prepara la proteína ({prot[p_idx]}) {obtener_accion(prot[p_idx])}.\n3. Sirve junto y añade un toque de grasa (aceite o mantequilla) para dar sabor.",
            "img": ""
        })
        
        # Cenas (Enfoque ligero o rápido)
        menu["🌙 CENA"].append({
            "titulo": f"Opción {i+1}: Cena rápida de {prot[p_idx]}",
            "receta": f"1. Usa una porción pequeña de {carb[c_idx]}.\n2. Acompaña con {prot[p_idx]} {obtener_accion(prot[p_idx])}.\n3. Una cena ligera ideal para descansar.",
            "img": ""
        })
        
    return menu

# --- CONEXIÓN SUPABASE ---
@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar_supabase()

# --- LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔐 Acceso al Sistema")
    with st.form("login"):
        u, p = st.text_input("Usuario").lower().strip(), st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar") and u in ["ignacio", "joseilys"] and p == "yosa0325":
            st.session_state.auth, st.session_state.user = True, u.capitalize()
            st.rerun()
    st.stop()

# --- INTERFAZ ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# AGREGAR PRODUCTO
with st.expander("➕ REGISTRAR NUEVO PRODUCTO"):
    c1, c2 = st.columns(2)
    m_n, n_n = c1.selectbox("Lista", ["Comida", "Hogar", "Por Comprar"]), c1.text_input("Nombre")
    p_n, c_n = c2.number_input("Precio $", min_value=0.0), c2.number_input("Cantidad", min_value=1)
    if st.button("💾 GUARDAR"):
        supabase.table("productos").insert({"modulo": m_n, "nombre": n_n.capitalize(), "precio": p_n, "cantidad": c_n, "created_at": datetime.now().isoformat()}).execute()
        st.success("Guardado"); time.sleep(1); st.rerun()

# TABLAS
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

tabs = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])
for i, tab in enumerate(tabs):
    mod = ["Comida", "Hogar", "Por Comprar"][i]
    with tab:
        df = df_all[df_all['modulo'] == mod].copy() if not df_all.empty else pd.DataFrame()
        if not df.empty:
            edit_df = st.data_editor(df[["id", "nombre", "precio", "cantidad"]], key=f"ed_{mod}", use_container_width=True, hide_index=True)
            c1, c2 = st.columns(2)
            if c1.button(f"🔄 Actualizar {mod}", key=f"up_{mod}"):
                for _, r in edit_df.iterrows(): supabase.table("productos").update({"precio": r['precio'], "cantidad": r['cantidad']}).eq("id", r['id']).execute()
                st.rerun()
            id_b = c2.number_input("ID a borrar", min_value=0, key=f"idb_{mod}", step=1)
            if c2.button(f"🗑️ Eliminar", key=f"del_{mod}"):
                supabase.table("productos").delete().eq("id", id_b).execute(); st.rerun()

# --- CHEF IA: 18 OPCIONES ---
st.divider()
st.subheader("👨‍🍳 Menú del Día (18 Sugerencias Reales)")

if not df_all.empty:
    comida = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]['nombre'].tolist()
    if comida:
        if st.button("✨ Generar Menú Completo", use_container_width=True):
            menu = generar_menu_extendido(comida)
            for momento, platos in menu.items():
                st.markdown(f"## {momento}")
                # Mostramos las 6 opciones en una cuadrícula de 3x2
                for i in range(0, 6, 2):
                    col1, col2 = st.columns(2)
                    with col1:
                        with st.expander(platos[i]['titulo']):
                            st.write(platos[i]['img'])
                            st.info(platos[i]['receta'])
                    with col2:
                        with st.expander(platos[i+1]['titulo']):
                            st.write(platos[i+1]['img'])
                            st.info(platos[i+1]['receta'])
