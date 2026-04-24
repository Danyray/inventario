import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario MI❤️AMOR JYI", layout="wide")

# --- LÓGICA DEL CHEF PROFESIONAL (18 SUGERENCIAS REALES) ---
def generar_menu_completo(productos):
    # Clasificación por comportamiento culinario
    proteinas = [p.capitalize() for p in productos if any(x in p.capitalize() for x in ["Carne", "Pollo", "Huevo", "Atun", "Cerdo", "Queso", "Mortadela", "Salchicha"])]
    harina_pan = [p.capitalize() for p in productos if "Harina pan" in p.capitalize()]
    harina_trigo = [p.capitalize() for p in productos if "Trigo" in p.capitalize()]
    carbo_cocidos = [p.capitalize() for p in productos if any(x in p.capitalize() for x in ["Arroz", "Pasta", "Papa", "Yuca", "Platano"])]
    pan = [p.capitalize() for p in productos if "Pan" in p.capitalize() and "Harina" not in p.capitalize()]

    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}
    
    # Función interna para rotar ingredientes sin repetir la misma receta exacta
    def armar_opciones(lista_base, lista_prot, momento, max_opciones=6):
        opciones = []
        if not lista_base or not lista_prot:
            return opciones
        
        for i in range(max_opciones):
            base = lista_base[i % len(lista_base)]
            prot = lista_prot[i % len(lista_prot)]
            
            if momento == "DESAYUNO":
                if "Trigo" in base:
                    titulo = f"Panquecas con {prot}"
                    receta = f"1. Mezcla {base} con agua/leche y sal.\n2. Cocina en sartén.\n3. Acompaña con {prot}."
                elif "Harina pan" in base:
                    titulo = f"Arepa de Maíz con {prot}"
                    receta = f"1. Haz la masa con {base}.\n2. Cocina en budare.\n3. Rellena con {prot} (rallado o frito)."
                else:
                    titulo = f"Sándwich de {prot}"
                    receta = f"1. Tuesta el {base}.\n2. Rellena con {prot} y mantequilla."
            
            elif momento == "ALMUERZO":
                titulo = f"{base} con {prot}"
                receta = f"1. Hierve el/la {base} con sal.\n2. Prepara el {prot} salteado o a la plancha.\n3. Sirve caliente."
            
            elif momento == "CENA":
                titulo = f"Cena ligera de {prot} y {base}"
                receta = f"1. Porción pequeña de {base}.\n2. Acompaña con {prot} preparado de forma sencilla."
            
            opciones.append({"titulo": titulo, "receta": receta})
        return opciones

    # Llenar las 6 opciones por categoría
    menu["☀️ DESAYUNO"] = armar_opciones(harina_pan + harina_trigo + pan, proteinas, "DESAYUNO")
    menu["🍴 ALMUERZO"] = armar_opciones(carbo_cocidos, [pr for pr in proteinas if "Queso" not in pr] or proteinas, "ALMUERZO")
    menu["🌙 CENA"] = armar_opciones(pan + carbo_cocidos, proteinas, "CENA")

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
    if st.button("🚀 GUARDAR"):
        if n_n:
            supabase.table("productos").insert({"modulo": m_n, "nombre": n_n.capitalize(), "precio": p_n, "cantidad": c_n, "created_at": datetime.now().isoformat()}).execute()
            st.success("¡Guardado!"); time.sleep(1); st.rerun()

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
                for _, r in edit_df.iterrows(): 
                    supabase.table("productos").update({"precio": r['precio'], "cantidad": r['cantidad']}).eq("id", r['id']).execute()
                st.success("Actualizado"); st.rerun()
            id_b = c2.number_input("ID a borrar", min_value=0, key=f"idb_{mod}", step=1)
            if c2.button(f"🗑️ Eliminar", key=f"del_{mod}"):
                supabase.table("productos").delete().eq("id", id_b).execute(); st.rerun()

# --- CHEF IA: 6 OPCIONES POR CATEGORÍA ---
st.divider()
st.subheader("👨‍🍳 Menú del Día (6 opciones por comida)")
if not df_all.empty:
    comida_list = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]['nombre'].tolist()
    if st.button("🪄 Generar Menú Completo", use_container_width=True):
        menu = generar_menu_completo(comida_list)
        for momento, platos in menu.items():
            if platos:
                st.markdown(f"## {momento}")
                # Grid de 3 columnas para mostrar las 6 opciones de forma compacta
                for i in range(0, len(platos), 3):
                    cols = st.columns(3)
                    for j in range(3):
                        if i + j < len(platos):
                            p = platos[i+j]
                            with cols[j]:
                                with st.expander(f"🍴 {p['titulo']}"):
                                    st.info(p['receta'])
