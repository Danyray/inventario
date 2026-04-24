import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario MI❤️AMOR JYI", layout="wide")

# --- LÓGICA DEL CHEF INTELIGENTE (SIN REPETICIONES) ---
def generar_menu_variado(productos):
    # Diccionario de verbos de cocina
    procesos = {
        "Carne": "cortada en tiras y salteada",
        "Pollo": "en cubitos dorados a la plancha",
        "Huevo": "en revoltillo o frito",
        "Queso": "rallado o en rebanadas frescas",
        "Mortadela": "doradita en el sartén",
        "Atun": "mezclado con un toque de aderezo",
        "Salchicha": "sofrita en rodajas"
    }

    # Clasificación de inventario real
    proteinas = [p.capitalize() for p in productos if any(x in p.capitalize() for x in ["Carne", "Pollo", "Huevo", "Atun", "Cerdo", "Queso", "Mortadela", "Salchicha"])]
    carbohidratos = [p.capitalize() for p in productos if any(x in p.capitalize() for x in ["Arroz", "Pasta", "Harina", "Pan", "Papa", "Platano", "Yuca"])]
    
    def obtener_accion(nombre):
        for k, v in procesos.items():
            if k in nombre: return v
        return "preparado a tu gusto"

    menu = {"☀️ DESAYUNO": [], "🍴 ALMUERZO": [], "🌙 CENA": []}

    # Generamos combinaciones ÚNICAS (sin repetir la misma pareja proteína-carbohidrato)
    vistas = set()
    
    for c in carbohidratos:
        for p in proteinas:
            combinacion = f"{p}-{c}"
            if combinacion not in vistas:
                accion = obtener_accion(p)
                
                # Clasificación lógica de la receta según el carbohidrato
                if any(x in c.lower() for x in ["harina", "pan"]):
                    menu["☀️ DESAYUNO"].append({
                        "titulo": f"{c} rellena con {p}",
                        "receta": f"1. Prepara el {c} (tuesta el pan o haz la arepa).\n2. Cocina el {p} hasta que esté {accion}.\n3. Rellena y sirve caliente.",
                        "img": ""
                    })
                
                elif any(x in c.lower() for x in ["arroz", "pasta", "papa", "yuca"]):
                    menu["🍴 ALMUERZO"].append({
                        "titulo": f"Plato de {c} con {p}",
                        "receta": f"1. Cocina el {c} en agua con sal hasta que esté tierno.\n2. Prepara el {p} {accion}.\n3. Sirve una porción generosa de ambos.",
                        "img": ""
                    })
                
                # La cena usa lo que quede, pero en porción ligera
                if len(menu["🌙 CENA"]) < 4: # Límite para no saturar la cena
                    menu["🌙 CENA"].append({
                        "titulo": f"Cena ligera: {p} con {c}",
                        "receta": f"1. Prepara una porción pequeña de {c}.\n2. Acompaña con {p} {accion}.\n3. Ideal para cerrar el día.",
                        "img": ""
                    })
                
                vistas.add(combinacion)

    # Limitar a máximo 6 por categoría por si tienes demasiados ingredientes
    for k in menu:
        menu[k] = menu[k][:6]
        
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

# --- CHEF IA: RESULTADOS ÚNICOS ---
st.divider()
st.subheader("👨‍🍳 Sugerencias Reales (Sin repeticiones)")

if not df_all.empty:
    comida = df_all[(df_all['modulo'] == 'Comida') & (df_all['cantidad'] > 0)]['nombre'].tolist()
    if comida:
        if st.button("✨ Ver opciones disponibles", use_container_width=True):
            menu = generar_menu_variado(comida)
            for momento, platos in menu.items():
                if platos: # Solo mostrar la categoría si tiene recetas
                    st.markdown(f"## {momento}")
                    # Mostrar en filas de 2 columnas
                    for i in range(0, len(platos), 2):
                        cols = st.columns(2)
                        for j in range(2):
                            if i + j < len(platos):
                                with cols[j]:
                                    p = platos[i+j]
                                    with st.expander(f"🍴 {p['titulo']}"):
                                        st.write(p['img'])
                                        st.info(p['receta'])
                else:
                    st.write(f"No hay suficientes ingredientes para nuevas opciones de {momento.lower()}.")
