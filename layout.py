import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="WMS Cámaras - Frigosa SAC", layout="wide", page_icon="❄️")

ID_SPREADSHEET = "1cX-C1Lrgp8SznxDs-_cjiMN6DptNusCmNoNopxBmJlg"
NOMBRE_HOJA = "POSICIONES_CAMARAS"

LISTA_PRODUCTOS = [
    "AF 300 - 500 g/pza",
    "AF 500- 1000 g/pza",
    "AF 1000 g/pza - UP",
    "AF 1000 g/pza - CV",
    "APC 300 g/pza - UP",
    "ANILLAS S/M S/T",
    "BOTONES S/M S/T",
    "CONOS",
    "FF S/M S/T 2000-4000 g/pza",
    "FF C/M C/T 500 g/pza - 1000 g/pz",
    "FF C/M C/T 1000 g/pza - 2000 g/pza",
    "FF C/M C/T 2000 g/pza - 4000 g/pza",
    "FF C/M C/T 2000 g/pza - 4000 g/pza MANTO ",
    "FF C/M C/T 2000 g/pza - 4000 g/pza CORTADO ",
    "FPC 7mm - 10 mm",
    "FPC PANZA 7mm - 10 mm",
    "FPC MEMBRANA 7mm - 10 mm",
    "FPC PANZA 8 mm - 14 mm",
    "FPC MEMBRANA 8 mm - 14 mm",
    "DESHILACHADO",
    "DESHILACHADO F2",
    "FPC 10mm - 14 mm",
    "NF 100 g/pza - 300 g/pza",
    "NF 300 g/pza - 500 g/pza",
    "NF 500g/pza -UP",
    "NF 0 -50 g/pza",
    "RECORTE PRECOCIDO",
    "RECORTE FRESCO S/M S/T",
    "REPRODUCTOR MAYOR A 50 cm",
    "REPRODUCTOR MENOR A 50 cm",
    "TB C/U C/V 300 g/pza - 500 g/pza",
    "TB C/U C/V 500 g/pza - 1000 g/pza",
    "TB S/U S/V 300 g/pza - 500 g/pza",
    "TB S/U S/V 2000 g/pza - 3000 g/pza",
    "TB S/U S/V 1000g /pza-UP",
    "OTRO (Digitar manualmente)"
]

ENCABEZADOS_OFICIALES = [
    "COD_POSICION", "CAMARA", "RACK", "COLUMNA", "NIVEL", "ESTADO",
    "LOTE", "PRODUCTO", "BULTOS", "PLACAS", "TUNEL", "CAJAS",
    "TURNO", "FECHA_DE_PRODUCCION", "OPERADOR", "OBSERVACION"
]

@st.cache_resource
def obtener_cliente():
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # Normalización de la clave privada para evitar errores RSA
    if "private_key" in creds_dict:
        pk = creds_dict["private_key"]
        if "\\n" in pk:
            creds_dict["private_key"] = pk.replace("\\n", "\n")
            
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def obtener_hoja():
    client = obtener_cliente()
    sh = client.open_by_key(ID_SPREADSHEET)
    try:
        return sh.worksheet(NOMBRE_HOJA)
    except Exception:
        ws = sh.add_worksheet(title=NOMBRE_HOJA, rows=1500, cols=20)
        ws.append_row(ENCABEZADOS_OFICIALES)
        return ws

def cargar_posiciones_df():
    ws = obtener_hoja()
    data = ws.get_all_records()
    if not data:
        return pd.DataFrame(columns=ENCABEZADOS_OFICIALES)
    return pd.DataFrame(data)

def poblar_matriz_si_vacia():
    ws = obtener_hoja()
    filas = []
    for cam in [1, 2]:
        for rk in [1, 2, 3]:
            for col in range(1, 73):
                for niv in [3, 2, 1]:
                    cod = f"C{cam}-R{rk}-C{col:02d}-N{niv}"
                    niv_txt = "N3 (SUPERIOR)" if niv == 3 else ("N2 (MEDIO)" if niv == 2 else "N1 (SUELO)")
                    filas.append([
                        cod, f"CAMARA {cam}", f"RACK {rk}", col, niv_txt, "DISPONIBLE",
                        "", "", 0, 0, 0, 0, "", "", "", ""
                    ])
    ws.clear()
    ws.append_row(ENCABEZADOS_OFICIALES)
    ws.append_rows(filas)

# --- MENÚ LATERAL ---
with st.sidebar:
    st.markdown("### ❄️ Control de Almacén")
    modulo_sel = st.radio(
        "Módulos Operativos:",
        ["🗺️ 1. Layout 2D y Mapa de Cámaras", "📥 2. Ingreso y Ubicación de Pallets"],
        index=0
    )
    st.markdown("---")
    if st.button("🔄 Refrescar Datos en Pantalla", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

try:
    df_pos = cargar_posiciones_df()
except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
    st.info("Verifica que las credenciales en 'Secrets' contengan el email y la llave de la cuenta de servicio.")
    st.stop()

# Auto-generación de matriz base
if df_pos.empty or len(df_pos) < 100:
    st.warning("⚠️ La hoja `POSICIONES_CAMARAS` aún no tiene las 648 celdas de Cámara 1 y Cámara 2 creadas.")
    if st.button("⚡ Auto-generar Matriz de 648 Celdas en Sheets", type="primary"):
        with st.spinner("Creando estructura física..."):
            poblar_matriz_si_vacia()
        st.success("✅ ¡Matriz física generada!")
        st.rerun()
    st.stop()

# =========================================================================
# MÓDULO 1: LAYOUT 2D Y MAPA VISUAL
# =========================================================================
if "1. Layout 2D" in modulo_sel:
    st.subheader("🗺️ Layout Visual y Elevación 2D de Cámaras")

    c_nav1, c_nav2, c_nav3 = st.columns([1.5, 1.5, 2.5])
    with c_nav1:
        cam_sel = st.selectbox("Cámara:", ["CAMARA 1", "CAMARA 2"])
    with c_nav2:
        rack_sel = st.selectbox("Rack:", ["RACK 1", "RACK 2", "RACK 3"])
    with c_nav3:
        tramo_sel = st.radio(
            "Profundidad (Columnas):",
            ["01 al 24", "25 al 48", "49 al 72"],
            horizontal=True
        )

    if "01 al 24" in tramo_sel:
        col_ini, col_fin = 1, 24
    elif "25 al 48" in tramo_sel:
        col_ini, col_fin = 25, 48
    else:
        col_ini, col_fin = 49, 72

    df_rack = df_pos[(df_pos["CAMARA"] == cam_sel) & (df_pos["RACK"] == rack_sel)]

    # Métricas
    total_pos = len(df_rack)
    ocupadas = len(df_rack[df_rack["ESTADO"] == "OCUPADO"])
    libres = len(df_rack[df_rack["ESTADO"] == "DISPONIBLE"])
    pct_rack = (ocupadas / total_pos * 100) if total_pos > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Posiciones Totales Rack", total_pos)
    m2.metric("Ocupadas", f"{ocupadas} pallets")
    m3.metric("Disponibles", f"{libres} libres")
    m4.metric("% Ocupación", f"{pct_rack:.1f}%")

    st.markdown("---")
    st.markdown(f"##### Elevación Frontal: {cam_sel} | {rack_sel} (Columnas {col_ini:02d} a {col_fin:02d})")

    niveles = ["N3 (SUPERIOR)", "N2 (MEDIO)", "N1 (SUELO)"]
    columnas_tramo = list(range(col_ini, col_fin + 1))

    # Encabezado de columnas
    c_head = st.columns([1.4] + [1] * len(columnas_tramo))
    c_head[0].markdown("**Nivel**")
    for idx, c_n in enumerate(columnas_tramo):
        c_head[idx + 1].markdown(f"<div style='text-align:center; font-weight:bold; font-size:11px;'>C{c_n:02d}</div>", unsafe_allow_html=True)

    # Filas de la cuadrícula
    for niv in niveles:
        f_cols = st.columns([1.4] + [1] * len(columnas_tramo))
        lbl_n = "N3 (SUP)" if "N3" in niv else ("N2 (MED)" if "N2" in niv else "N1 (PISO)")
        f_cols[0].markdown(f"**{lbl_n}**")

        for idx, c_n in enumerate(columnas_tramo):
            match = df_rack[(df_rack["COLUMNA"] == c_n) & (df_rack["NIVEL"] == niv)]
            with f_cols[idx + 1]:
                if not match.empty:
                    row = match.iloc[0]
                    est = str(row["ESTADO"]).upper()
                    if est == "OCUPADO":
                        bg_c = "#2B6CB0"
                        txt_c = "white"
                        b_val = row["BULTOS"]
                        l_abrev = str(row["LOTE"])[-7:] if row["LOTE"] else "OCP"
                        tip = f"{row['COD_POSICION']} | {row['PRODUCTO']} | {row['LOTE']} | {b_val} bultos | Op: {row['OPERADOR']}"
                        body = f"<b>{l_abrev}</b><br/>{b_val}b"
                    elif est == "BLOQUEADO":
                        bg_c = "#E53E3E"
                        txt_c = "white"
                        tip = f"{row['COD_POSICION']} | BLOQUEADO / CALIDAD"
                        body = "BLQ"
                    else:
                        bg_c = "#EDF2F7"
                        txt_c = "#A0AEC0"
                        tip = f"{row['COD_POSICION']} | DISPONIBLE"
                        body = "—"

                    st.markdown(
                        f"""
                        <div title="{tip}" style="background-color: {bg_c}; color: {txt_c}; border-radius: 4px; padding: 5px 1px; text-align: center; font-size: 9.5px; border: 1px solid #CBD5E0; cursor: pointer;">
                            {body}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    # Detalle de Celda Seleccionada
    st.markdown("---")
    st.markdown("##### 🔍 Consulta Detallada de Posición")
    pos_lista = df_rack["COD_POSICION"].tolist()
    sel_pos_view = st.selectbox("Seleccione Posición a Examinar:", pos_lista)
    r_det = df_rack[df_rack["COD_POSICION"] == sel_pos_view].iloc[0]

    cd1, cd2, cd3, cd4 = st.columns(4)
    cd1.info(f"**Posición:** {r_det['COD_POSICION']}\n\n**Estado:** {r_det['ESTADO']}")
    cd2.info(f"**Producto:** {r_det['PRODUCTO'] or 'Sin Producto'}\n\n**Lote:** {r_det['LOTE'] or 'Sin Lote'}")
    cd3.info(f"**Total Bultos:** {r_det['BULTOS']}\n\n**Placas:** {r_det['PLACAS']} | **Túnel:** {r_det['TUNEL']} | **Cajas:** {r_det['CAJAS']}")
    cd4.info(f"**Fec. Prod:** {r_det['FECHA_DE_PRODUCCION'] or '-'}\n\n**Turno:** {r_det['TURNO'] or '-'}\n\n**Operador:** {r_det['OPERADOR'] or '-'}")

# =========================================================================
# MÓDULO 2: INGRESO Y UBICACIÓN DE PALLETS (PUT-AWAY)
# =========================================================================
else:
    st.subheader("📥 Ingreso y Ubicación de Pallets en Racks")
    st.caption("Registra el producto terminado que ingresa a cámara y asígnalo directamente a una celda libre.")

    col_ing1, col_ing2 = st.columns([2, 2])

    with col_ing1:
        st.markdown("#### 1. Datos de Producción / Lote")
        fec_prod = st.date_input("Fecha de Producción:", value=date.today())
        lote_ing = st.text_input("N° Lote (ej. LT 026.252):").strip().upper()
        
        prod_ing = st.selectbox("Producto / Presentación:", LISTA_PRODUCTOS)
        if prod_ing == "OTRO (Digitar manualmente)":
            prod_ing = st.text_input("Escriba la presentación:").strip().upper()

        c_t1, c_t2 = st.columns(2)
        with c_t1:
            turno_ing = st.selectbox("Turno:", ["TURNO DIA", "TURNO NOCHE"])
        with c_t2:
            operador_ing = st.text_input("Operador / Montacarguista:").strip().upper()

        st.markdown("##### Desglose de Carga del Pallet")
        c_b1, c_b2, c_b3 = st.columns(3)
        with c_b1:
            placas_val = st.number_input("Placas (bultos):", min_value=0, value=0, step=1)
        with c_b2:
            tunel_val = st.number_input("Túnel (bultos):", min_value=0, value=0, step=1)
        with c_b3:
            cajas_val = st.number_input("Cajas (unidades):", min_value=0, value=0, step=1)

        total_bultos_calc = placas_val + tunel_val + cajas_val
        st.metric("Total Bultos en Pallet:", f"{total_bultos_calc:,}")

        obs_ing = st.text_area("Observación (Opcional):", height=65)

    with col_ing2:
        st.markdown("#### 2. Selección de Posición Destino")
        c_cam, c_rk = st.columns(2)
        with c_cam:
            cam_dest = st.selectbox("Cámara Destino:", ["CAMARA 1", "CAMARA 2"], key="cam_dest_sel")
        with c_rk:
            rk_dest = st.selectbox("Rack Destino:", ["RACK 1", "RACK 2", "RACK 3"], key="rk_dest_sel")

        df_libres = df_pos[
            (df_pos["CAMARA"] == cam_dest) &
            (df_pos["RACK"] == rk_dest) &
            (df_pos["ESTADO"] == "DISPONIBLE")
        ]

        st.markdown(f"**Posiciones Libres en {cam_dest} - {rk_dest}:** `{len(df_libres)} de {len(df_pos[(df_pos['CAMARA'] == cam_dest) & (df_pos['RACK'] == rk_dest)])}`")

        todas_pos_rack = df_pos[(df_pos["CAMARA"] == cam_dest) & (df_pos["RACK"] == rk_dest)]["COD_POSICION"].tolist()

        modo_asignacion = st.radio("Filtro de Posición:", ["Solo Mostrar Posiciones Libres", "Ver Todo el Rack (Permite Sobreescribir)"], horizontal=True)

        if modo_asignacion == "Solo Mostrar Posiciones Libres":
            opciones_celdas = df_libres["COD_POSICION"].tolist()
            if not opciones_celdas:
                st.error("🚫 ¡No hay posiciones disponibles en este Rack! Seleccione otro rack o cámara.")
                celda_elegida = None
            else:
                celda_elegida = st.selectbox("Seleccione Posición Libre:", opciones_celdas)
        else:
            celda_elegida = st.selectbox("Seleccione Posición:", todas_pos_rack)

        if celda_elegida:
            celda_info = df_pos[df_pos["COD_POSICION"] == celda_elegida].iloc[0]
            if celda_info["ESTADO"] == "OCUPADO":
                st.warning(f"⚠️ ¡Atención! La celda **{celda_elegida}** actualmente está ocupada por el lote **{celda_info['LOTE']}** ({celda_info['BULTOS']} b).")
            else:
                st.success(f"✅ Celda **{celda_elegida}** disponible para estibar.")

        st.markdown("---")
        btn_ingreso = st.button("💾 Registrar Ingreso y Ubicar Pallet", type="primary", use_container_width=True)

        if btn_ingreso:
            if not celda_elegida:
                st.error("Debe seleccionar una celda válida.")
            elif not lote_ing:
                st.error("Ingrese el N° de Lote de producción.")
            elif total_bultos_calc <= 0:
                st.error("El total de bultos del pallet debe ser mayor a 0.")
            else:
                try:
                    with st.spinner("Actualizando ubicación en Google Sheets..."):
                        ws = obtener_hoja()
                        cods_list = ws.col_values(1)
                        fila_target = cods_list.index(celda_elegida) + 1

                        datos_actualizar = [
                            "OCUPADO",                  # F: ESTADO
                            lote_ing,                   # G: LOTE
                            prod_ing,                   # H: PRODUCTO
                            int(total_bultos_calc),     # I: BULTOS
                            int(placas_val),            # J: PLACAS
                            int(tunel_val),             # K: TUNEL
                            int(cajas_val),             # L: CAJAS
                            turno_ing,                  # M: TURNO
                            str(fec_prod),              # N: FECHA_DE_PRODUCCION
                            operador_ing,               # O: OPERADOR
                            obs_ing                     # P: OBSERVACION
                        ]

                        ws.update(f"F{fila_target}:P{fila_target}", [datos_actualizar])
                        st.success(f"🎉 ¡Pallet del lote {lote_ing} ubicado con éxito en la celda {celda_elegida}!")
                        st.cache_resource.clear()
                        st.rerun()
                except Exception as err:
                    st.error(f"Error al registrar en Sheets: {err}")
