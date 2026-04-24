import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario Gourmet JYI", layout="wide")

# --- LÓGICA DEL CHEF CREATIVO 3.0 ---
def generar_menu_inteligente(productos):
    p_list = [str(p).lower() for p in productos]
    
    # Clasificación por palabras clave para mayor flexibilidad
    tiene = lambda x: any(x in item for item in p_list)
    
    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}

    # --- IDEAS DE DESAYUNO ---
    if tiene("harina de maiz") or tiene("harina pan"):
        if tiene("queso"):
            menu["☀️ DESAYUNO"].append({
                "titulo": "Arepas de Maíz con Costra de Queso",
                "receta": "1. Prepara la masa clásica. 2. Ralla el queso y colócalo directamente en el sartén caliente; pon la arepa encima para que el queso se tueste y se pegue a la masa. 3. Sirve crocante.",
                "img": ""
            })
    if tiene("harina de trigo"):
        menu["☀️ DESAYUNO"].append({
            "titulo": "Torrejas Dulces de Trigo",
            "receta": "1. Crea una mezcla líquida con harina de trigo, agua y el azúcar que tienes en inventario. 2. Fríe porciones pequeñas hasta que doren. 3. Espolvorea un poco más de azúcar al salir.",
            "img": ""
        })

    # --- IDEAS DE ALMUERZO (USANDO ESPECIAS) ---
    if tiene("carne bistec"):
        base = "Pasta" if tiene("pasta") else ("Arroz" if tiene("arroz") else "Maíz")
        receta_carne = "1. Corta la carne en trozos pequeños. 2. Sazona con el **Comino** y la **Sal** de tu lista para darle un sabor profundo. 3. Saltea a fuego alto y mezcla con la base cocida."
        
        menu["🍴 ALMUERZO"].append({
            "titulo": f"Salteado de Carne al Comino con {base}",
            "receta": receta_carne,
            "img": ""
        })
        
        if tiene("queso"):
            menu["🍴 ALMUERZO"].append({
                "titulo": "Bistec 'A Caballo' con Queso Fundido",
                "receta": "1. Cocina el bistec sazonado con sal y comino. 2. Antes de retirar, coloca láminas de queso arriba y tapa el sartén para que se funda. 3. Sirve sobre pasta.",
                "img": ""
            })

    # --- IDEAS DE CENA ---
    if tiene("pasta") and tiene("queso"):
        menu["🌙 CENA"].append({
            "titulo": "Pasta al Burro con Queso Rallado",
            "receta": "1. Cocina la pasta al dente. 2. Mezcla con mantequilla (si tienes) o un toque de aceite y sal. 3. Agrega el queso rallado finamente para crear una salsa cremosa simple.",
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
    st.title("🔐 Acceso")
    with st.form("login"):
        u, p = st.text_input("Usuario").lower().strip(), st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar") and u in ["ignacio", "joseilys"] and p == "yosa0325":
            st.session_state.auth, st.session_state.user = True, u.capitalize()
            st.rerun()
    st.stop()

# --- INTERFAZ PRINCIPAL ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# --- SECCIÓN RECUPERADA: AGREGAR PRODUCTOS ---
with st.expander("➕ REGISTRAR NUEVO PRODUCTO", expanded=False):
    c1, c2 = st.columns(2)
    m_n = c1.selectbox("Lista", ["Comida", "Hogar", "Por Comprar"])
    n_n = c1.text_input("Nombre del artículo")
    p_n = c2.number_input("Precio $", min_value=0.0)
    c_n = c2.number_input("Cantidad", min_value=0) # Permitir 0 para el maíz/pan que vi en tu foto
    if st.button("💾 GUARDAR EN INVENTARIO", use_container_width=True):
        if n_n:
            supabase.table("productos").insert({"modulo": m_n, "nombre": n_n.capitalize(), "precio": p_n, "cantidad": c_n, "created_at": datetime.now().isoformat()}).execute()
            st.success("¡Producto registrado!"); time.sleep(1); st.rerun()

# --- TABLAS DE DATOS ---
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

t1, t2, t3 = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 COMPRAS"])
listas = ["Comida", "Hogar", "Por Comprar"]

for i, tab in enumerate([t1, t2, t3]):
    with tab:
        df = df_all[df_all['modulo'] == listas[i]].copy() if not df_all.empty else pd.DataFrame()
        if not df.empty:
            edit_df = st.data_editor(df[["id", "nombre", "precio", "cantidad"]], key=f"editor_{listas[i]}", use_container_width=True, hide_index=True)
            col1, col2 = st.columns(2)
            if col1.button(f"🔄 Actualizar {listas[i]}", key=f"up_{listas[i]}"):
                for _, r in edit_df.iterrows():
                    supabase.table("productos").update({"precio": r['precio'], "cantidad": r['cantidad']}).eq("id", r['id']).execute()
                st.rerun()
            id_borrar = col2.number_input("ID a eliminar", min_value=0, key=f"del_{listas[i]}")
            if col2.button(f"🗑️ Eliminar Registro", key=f"btn_del_{listas[i]}"):
                supabase.table("productos").delete().eq("id", id_borrar).execute(); st.rerun()

# --- CHEF DINÁMICO ---
st.divider()
st.subheader("👨‍🍳 Ideas del Chef (Mezclas con lo que tienes)")

if not df_all.empty:
    # Filtramos solo lo que tiene cantidad > 0
    comida_stock = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]['nombre'].tolist()
    
    if st.button("🪄 Generar Sugerencias Reales", use_container_width=True):
        recetas = generar_menu_inteligente(comida_stock)
        
        hay_algo = False
        for cat, platos in recetas.items():
            if platos:
                hay_algo = True
                st.markdown(f"### {cat}")
                cols = st.columns(len(platos) if len(platos) < 3 else 3)
                for idx, p in enumerate(platos):
                    with cols[idx % 3]:
                        with st.expander(f"⭐ {p['titulo']}"):
                            st.write(p['img'])
                            st.info(p['receta'])
        
        if not hay_algo:
            st.warning("Parece que falta stock de ingredientes base (Harina, Pasta o Carne) para darte ideas elaboradas.")
