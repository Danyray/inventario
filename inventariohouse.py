import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario MI❤️AMOR JYI", layout="wide")

# --- LÓGICA DEL CHEF PROFESIONAL (6 SUGERENCIAS POR MOMENTO DEL DÍA) ---
def generar_menu_diario(productos):
    # Clasificación inteligente
    categorias = {
        "proteinas": ["Pollo", "Carne", "Huevo", "Atun", "Cerdo", "Queso", "Mortadela", "Salchicha"],
        "carbohidratos": ["Arroz", "Pasta", "Harina pan", "Pan", "Papa", "Platano", "Yuca"],
        "extras": ["Granola", "Leche", "Mantequilla", "Mayonesa", "Salsa", "Azucar"]
    }
    
    disp = {"p": [], "c": [], "e": []}
    for p in productos:
        name = p.capitalize()
        if any(x in name for x in categorias["proteinas"]): disp["p"].append(name)
        elif any(x in name for x in categorias["carbohidratos"]): disp["c"].append(name)
        else: disp["e"].append(name)

    # Selección de ingredientes base para evitar errores
    p1 = disp["p"][0] if len(disp["p"]) > 0 else "Huevo"
    p2 = disp["p"][1] if len(disp["p"]) > 1 else "Queso"
    c1 = disp["c"][0] if len(disp["c"]) > 0 else "Harina pan"
    c2 = disp["c"][1] if len(disp["c"]) > 1 else "Arroz"

    menu = [
        {"momento": "☀️ DESAYUNO", "platos": [
            {
                "titulo": f"🫓 Arepas con {p1}",
                "receta": f"1. Amasa la Harina Pan con agua y sal.\n2. Haz las arepas y asínalas en el budare.\n3. Rellena generosamente con {p1}.",
                "img": ""
            },
            {
                "titulo": "🥣 Bowl de Granola Energético",
                "receta": "1. Sirve la granola en un tazón.\n2. Agrega leche o yogurt si tienes.\n3. Perfecto para un inicio de día ligero y rápido.",
                "img": ""
            }
        ]},
        {"momento": "🍴 ALMUERZO", "platos": [
            {
                "titulo": f"🍛 {c2} con {p1} Salteado",
                "receta": f"1. Cocina el {c2} hasta que esté sueltecito.\n2. Corta el {p1} en tiras y saltéalo con un toque de aceite.\n3. Sirve y acompaña con plátano si tienes disponible.",
                "img": ""
            },
            {
                "titulo": f"🍝 Pasta con {p2} y Mantequilla",
                "receta": f"1. Cocina la pasta al dente en agua hirviendo.\n2. Escurre y mezcla con mantequilla y {p2} rallado.\n3. Un clásico rápido y sabroso.",
                "img": ""
            }
        ]},
        {"momento": "🌙 CENA", "platos": [
            {
                "titulo": f"🥪 Sándwich Premium JYI",
                "receta": f"1. Tuesta el pan con un poco de mantequilla.\n2. Rellena con {p1} o {p2}.\n3. Agrega un toque de mayonesa para suavizar.",
                "img": ""
            },
            {
                "titulo": f"🍳 Revoltillo de {p1} con Pan",
                "receta": f"1. Bate los huevos o saltea la {p1}.\n2. Cocina a fuego medio hasta que esté en su punto.\n3. Acompaña con pan tostado.",
                "img": ""
            }
        ]}
    ]
    return menu

# --- CONEXIÓN SUPABASE ---
@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar_supabase()

# --- SISTEMA DE LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔐 Acceso al Inventario")
    with st.form("login"):
        u = st.text_input("Usuario").lower().strip()
        p = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            if u in ["ignacio", "joseilys"] and p == "yosa0325":
                st.session_state.auth = True
                st.session_state.user = u.capitalize()
                st.rerun()
            else: st.error("Acceso incorrecto")
    st.stop()

# --- INTERFAZ PRINCIPAL ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# SECCIÓN AGREGAR
with st.expander("➕ REGISTRAR NUEVO PRODUCTO", expanded=False):
    c1, c2 = st.columns(2)
    m_n = c1.selectbox("Ubicación", ["Comida", "Hogar", "Por Comprar"])
    n_n = c1.text_input("Nombre del artículo")
    p_n = c2.number_input("Precio ($)", min_value=0.0, step=0.1)
    c_n = c2.number_input("Cantidad", min_value=1, step=1)
    if st.button("💾 GUARDAR EN BASE DE DATOS", use_container_width=True):
        if n_n:
            supabase.table("productos").insert({"modulo": m_n, "nombre": n_n.capitalize(), "precio": p_n, "cantidad": c_n, "created_at": datetime.now().isoformat()}).execute()
            st.success("¡Producto guardado exitosamente!")
            time.sleep(1)
            st.rerun()

# TABLAS DE DATOS
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

t1, t2, t3 = st.tabs(["🍕 DESPENSA", "🏠 HOGAR", "🛒 LISTA DE COMPRAS"])
modulos = ["Comida", "Hogar", "Por Comprar"]

for i, tab in enumerate([t1, t2, t3]):
    with tab:
        df = df_all[df_all['modulo'] == modulos[i]].copy() if not df_all.empty else pd.DataFrame()
        if not df.empty:
            edit_df = st.data_editor(df[["id", "nombre", "precio", "cantidad"]], key=f"editor_{modulos[i]}", use_container_width=True, hide_index=True)
            col_b1, col_b2 = st.columns(2)
            if col_b1.button(f"🔄 Actualizar {modulos[i]}", key=f"upd_{modulos[i]}"):
                for _, row in edit_df.iterrows():
                    supabase.table("productos").update({"precio": row['precio'], "cantidad": row['cantidad']}).eq("id", row['id']).execute()
                st.rerun()
            id_borrar = col_b2.number_input("ID a eliminar", min_value=0, key=f"id_{modulos[i]}", step=1)
            if col_b2.button(f"🗑️ Eliminar registro", key=f"del_{modulos[i]}"):
                supabase.table("productos").delete().eq("id", id_borrar).execute()
                st.rerun()
        else: st.info("No hay artículos registrados.")

# --- SECCIÓN CHEF IA: LAS 6 SUGERENCIAS ---
st.divider()
st.subheader("👨‍🍳 Planificador de Comidas JYI")
st.write("Selecciona qué momento del día quieres organizar:")

if not df_all.empty:
    comida_actual = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]['nombre'].tolist()
    if comida_actual:
        if st.button("🪄 Generar Menú Sugerido (6 Opciones)", use_container_width=True):
            menu_completo = generar_menu_diario(comida_actual)
            
            for momento in menu_completo:
                st.markdown(f"### {momento['momento']}")
                cols = st.columns(2)
                for idx, plato in enumerate(momento['platos']):
                    with cols[idx]:
                        with st.expander(plato['titulo']):
                            st.write(plato['img'])
                            st.write("**Preparación:**")
                            st.info(plato['receta'])
    else:
        st.warning("No hay suficientes ingredientes en la despensa.")
