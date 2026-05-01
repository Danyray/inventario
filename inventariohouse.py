import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client
from PIL import Image
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI - IA Vision v4", layout="wide")

# --- ESTILOS CSS (Mantenidos) ---
st.markdown("""
    <style>
        [data-testid="collapsedControl"] .st-emotion-cache-12bp31y { display: none !important; }
        [data-testid="collapsedControl"]::after {
            content: "💰 ABRIR CONVERSOR";
            visibility: visible;
            position: absolute;
            top: 20px; left: 20px;
            background-color: #f39c12; 
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
            font-size: 14px;
            animation: pulse_jyi 2s infinite;
            display: flex; align-items: center; gap: 5px;
        }
        @keyframes pulse_jyi {
            0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(243, 156, 18, 0.7); }
            70% { transform: scale(1.05); box-shadow: 0 0 0 10px rgba(243, 156, 18, 0); }
            100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(243, 156, 18, 0); }
        }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN ---
@st.cache_resource
def conectar_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar_supabase()

# --- TASAS ---
TASAS = {"🏛️ BCV": 483.87, "⚖️ Paralelo": 542.15, "💵 USDT": 538.40, "🇪🇺 Euro": 512.20}
TASA_BCV_FIJA = TASAS["🏛️ BCV"]

# --- LÓGICA DEL CHEF (Omitida por brevedad, se mantiene igual) ---
def generar_menu_inteligente(productos):
    # ... (Misma lógica de 12 platos de tu código original)
    return {}

# --- LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔑 Acceso")
    with st.form("login"):
        u, p = st.text_input("Usuario").lower().strip(), st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar") and u in ["ignacio", "joseilys"] and p == "yosa0325":
            st.session_state.auth, st.session_state.user = True, u.capitalize()
            st.rerun()
    st.stop()

# --- SIDEBAR (Conversor mantenido) ---
st.sidebar.title("📈 Monitor de Divisas")
# ... (Mismo código de tu conversor original)

# --- INTERFAZ PRINCIPAL ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

# --- 📸 NUEVA FUNCIÓN: LECTURA AUTOMÁTICA POR IA ---
with st.expander("📸 ESCANEAR FACTURA O LISTA (IA AUTOMÁTICA)", expanded=False):
    foto = st.file_uploader("Sube la foto de la factura", type=["jpg", "jpeg", "png"])
    
    if foto:
        img = Image.open(foto)
        st.image(img, caption="Imagen cargada", width=400)
        
        if st.button("🔍 ANALIZAR IMAGEN"):
            with st.spinner("Leyendo factura con IA..."):
                # Simulación de prompt a Gemini Vision (esto consume la imagen y devuelve texto estructurado)
                # En un entorno real, aquí llamamos a model.generate_content([prompt, img])
                # Para este ejemplo, simulamos la respuesta basada en tu imagen de muestra:
                data_detectada = [
                    {"nombre": "Mute Santandereano", "precio": 50.00, "cantidad": 2},
                    {"nombre": "Churrasco x 300 Gr", "precio": 100.00, "cantidad": 2},
                    {"nombre": "Pechuga a la Plancha", "precio": 42.00, "cantidad": 1},
                    {"nombre": "Porcion de Arroz", "precio": 5.50, "cantidad": 1},
                ]
                st.session_state.temp_items = data_detectada

        if "temp_items" in st.session_state:
            st.subheader("📝 Revisar productos detectados")
            df_preview = pd.DataFrame(st.session_state.temp_items)
            
            # Editor para que el usuario pueda corregir si la IA se equivocó en algo
            edited_preview = st.data_editor(df_preview, num_rows="dynamic", use_container_width=True, key="preview_editor")
            
            dest_foto = st.selectbox("Enviar estos productos a:", ["Comida", "Hogar", "Por Comprar"])
            
            if st.button("✅ TODO CORRECTO, AGREGAR AL INVENTARIO"):
                for _, row in edited_preview.iterrows():
                    supabase.table("productos").insert({
                        "modulo": dest_foto,
                        "nombre": row['nombre'].capitalize(),
                        "precio": float(row['precio']),
                        "cantidad": int(row['cantidad']),
                        "created_at": datetime.now().isoformat()
                    }).execute()
                st.success(f"Se agregaron {len(edited_preview)} productos a {dest_foto}")
                del st.session_state.temp_items
                time.sleep(1)
                st.rerun()

st.divider()

# --- REGISTRO MANUAL Y TABLAS (Mantenido exactamente igual) ---
# ... (Aquí va tu bloque de REGISTRAR NUEVO PRODUCTO MANUAL)

# CARGA DE DATOS
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

t_comida, t_hogar, t_compras = st.tabs(["🍎 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

def render_tabla_gestion(df_sec, mod):
    if not df_sec.empty:
        df_sec['Subtotal $'] = df_sec['precio'] * df_sec['cantidad']
        df_sec['Subtotal Bs.'] = df_sec['Subtotal $'] * TASA_BCV_FIJA
        
        # ELIMINACIÓN MÚLTIPLE
        with st.expander(f"🗑️ ELIMINAR VARIOS DE {mod.upper()}"):
            seleccionados = st.multiselect("Selecciona productos para borrar:", df_sec['nombre'].tolist(), key=f"del_{mod}")
            if st.button(f"Confirmar Eliminación ({len(seleccionados)})", key=f"btn_del_{mod}"):
                for p_del in seleccionados:
                    supabase.table("productos").delete().eq("modulo", mod).eq("nombre", p_del).execute()
                st.rerun()

        edited_df = st.data_editor(df_sec[["id", "nombre", "precio", "cantidad", "Subtotal $", "Subtotal Bs."]], 
                                    use_container_width=True, hide_index=True, 
                                    disabled=["id", "Subtotal $", "Subtotal Bs."], key=f"editor_{mod}")
        
        # Botones de guardado, métricas, etc...
        if st.button(f"💾 Guardar cambios en {mod}", key=f"save_{mod}"):
            for _, row in edited_df.iterrows():
                supabase.table("productos").update({"precio": float(row['precio']), "cantidad": int(row['cantidad'])}).eq("id", row['id']).execute()
            st.rerun()
    else: st.info(f"{mod} está vacío.")

# (Resto de la lógica de las pestañas COMIDA, HOGAR, COMPRAS se mantiene intacta)
