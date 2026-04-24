import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inventario JYI Pro v3", layout="wide")

# --- CONEXIÓN ---
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

# --- TASA BCV (SIDEBAR) ---
st.sidebar.title("💰 Cambio del Día")
tasa_bcv = st.sidebar.number_input("Tasa BCV (Bs/$)", min_value=0.1, value=36.5, step=0.01, format="%.2f")

# --- 1. AGREGAR NUEVO PRODUCTO (AHORA AL INICIO) ---
st.title(f"📦 INVENTARIO JYI - {st.session_state.user}")

with st.expander("➕ REGISTRAR NUEVO PRODUCTO", expanded=True):
    f1, f2 = st.columns(2)
    m_new = f1.selectbox("Destino", ["Comida", "Hogar", "Por Comprar"])
    n_new = f1.text_input("Nombre del producto")
    # Aseguramos que el precio sea float para evitar errores de cálculo
    p_new = f2.number_input("Precio Unitario $", min_value=0.0, step=0.01, format="%.2f")
    c_new = f2.number_input("Cantidad inicial", min_value=1, step=1)
    
    if st.button("🚀 REGISTRAR E INSERTAR"):
        if n_new:
            supabase.table("productos").insert({
                "modulo": m_new, "nombre": n_new.capitalize(), 
                "precio": float(p_new), "cantidad": int(c_new), 
                "created_at": datetime.now().isoformat()
            }).execute()
            st.success(f"✅ {n_new} agregado con éxito.")
            time.sleep(1)
            st.rerun()

st.divider()

# --- CARGA DE DATOS ---
res = supabase.table("productos").select("*").order("id").execute()
df_all = pd.DataFrame(res.data if res.data else [])

# --- LÓGICA DE CÁLCULO FINANCIERO BLINDADA ---
def render_tabla_financiera(df_seccion, nombre_mod):
    if not df_seccion.empty:
        # Asegurar tipos numéricos para evitar errores de 'string * float'
        df_seccion['precio'] = pd.to_numeric(df_seccion['precio'], errors='coerce').fillna(0.0)
        df_seccion['cantidad'] = pd.to_numeric(df_seccion['cantidad'], errors='coerce').fillna(0).astype(int)
        
        # CÁLCULO FILA POR FILA
        # Subtotal USD = Precio Unitario * Cantidad
        df_seccion['Total USD'] = df_seccion['precio'] * df_seccion['cantidad']
        # Subtotal BS = Subtotal USD * Tasa
        df_seccion['Total Bs.'] = df_seccion['Total USD'] * tasa_bcv
        
        # Mostrar tabla
        st.data_editor(
            df_seccion[["id", "nombre", "precio", "cantidad", "Total USD", "Total Bs."]], 
            use_container_width=True, 
            hide_index=True, 
            disabled=["Total USD", "Total Bs."], 
            key=f"editor_{nombre_mod}"
        )
        
        # TOTALES GENERALES (Suma de los subtotales calculados arriba)
        suma_usd = df_seccion['Total USD'].sum()
        suma_bs = df_seccion['Total Bs.'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric(f"Monto Total {nombre_mod} ($)", f"{suma_usd:.2f} $")
        c2.metric(f"Monto Total {nombre_mod} (Bs)", f"{suma_bs:.2f} Bs")
    else:
        st.info(f"No hay registros en {nombre_mod}.")

# --- PESTAÑAS ---
t_comida, t_hogar, t_compras = st.tabs(["🍕 COMIDA", "🏠 HOGAR", "🛒 POR COMPRAR"])

with t_comida:
    df_c = df_all[df_all['modulo'] == 'Comida'].copy() if not df_all.empty else pd.DataFrame()
    if not df_c.empty:
        # En comida no mostramos totales de dinero para no saturar, o puedes usar la función financiera
        st.dataframe(df_c[["id", "nombre", "precio", "cantidad"]], use_container_width=True, hide_index=True)
        
        st.write("---")
        st.subheader("⚙️ Gestión de Comida")
        p_sel = st.selectbox("Seleccionar producto:", df_c['nombre'].tolist())
        item = df_c[df_c['nombre'] == p_sel].iloc[0]

        col_a, col_b = st.columns(2)
        
        # Lógica de envío a compras (Anti-duplicados)
        if col_a.button(f"🛒 Enviar '{p_sel}' a Compras"):
            st.session_state.confirm_move = True
        
        if st.session_state.get('confirm_move'):
            st.warning(f"¿Mover {p_sel} a la lista de compras?")
            if st.button("SÍ, CONFIRMAR ENVÍO"):
                # Buscar si ya existe en la lista de compras
                existe = supabase.table("productos").select("*").eq("modulo", "Por Comprar").eq("nombre", item['nombre']).execute()
                if existe.data:
                    # Sumamos la cantidad actual de comida a la que ya estaba en compras
                    nueva_cant = int(existe.data[0]['cantidad']) + int(item['cantidad'])
                    supabase.table("productos").update({"cantidad": nueva_cant}).eq("id", existe.data[0]['id']).execute()
                    # Borramos el registro original de comida
                    supabase.table("productos").delete().eq("id", item['id']).execute()
                else:
                    # Si no existe, simplemente cambiamos el módulo
                    supabase.table("productos").update({"modulo": "Por Comprar"}).eq("id", item['id']).execute()
                
                st.session_state.confirm_move = False
                st.rerun()

        if col_b.button(f"🗑️ Eliminar '{p_sel}'"):
            st.session_state.confirm_del = True
            
        if st.session_state.get('confirm_del'):
            st.error(f"¿Eliminar permanentemente {p_sel}?")
            if st.button("SÍ, ELIMINAR"):
                supabase.table("productos").delete().eq("id", item['id']).execute()
                st.session_state.confirm_del = False
                st.rerun()
    else:
        st.info("Inventario de comida vacío.")

with t_hogar:
    df_h = df_all[df_all['modulo'] == 'Hogar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla_financiera(df_h, "Hogar")

with t_compras:
    df_p = df_all[df_all['modulo'] == 'Por Comprar'].copy() if not df_all.empty else pd.DataFrame()
    render_tabla_financiera(df_p, "Por Comprar")
