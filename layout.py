import re

@st.cache_resource
def obtener_cliente():
    creds_raw = dict(st.secrets["gcp_service_account"])
    
    # 1. Asegurar tipo diccionario mutable
    creds_dict = {k: v for k, v in creds_raw.items()}
    
    # 2. Reconstrucción estricta de la clave PEM
    pk = str(creds_dict.get("private_key", ""))
    
    # Si viene con \n escapados como texto, convertirlos a saltos reales
    pk = pk.replace("\\n", "\n").strip()
    
    # Limpiar encabezados si están duplicados o pegados en una sola línea
    cuerpo = pk.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "")
    # Quitar cualquier espacio en blanco o salto residual en el cuerpo Base64
    cuerpo_limpio = "".join(cuerpo.split())
    
    # Reconstruir el PEM con saltos cada 64 caracteres según el estándar RFC 7468
    lineas = [cuerpo_limpio[i:i+64] for i in range(0, len(cuerpo_limpio), 64)]
    pk_formateada = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(lineas) + "\n-----END PRIVATE KEY-----\n"
    
    creds_dict["private_key"] = pk_formateada

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)
