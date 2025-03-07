import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Definir los permisos (alcances) para Google Sheets y Google Drive
SCOPES = [
    "https://spreadsheets.google.com/feeds", 
    "https://www.googleapis.com/auth/drive"
]


# Archivo JSON con credenciales de la cuenta de servicio
CREDENTIALS_FILE = "app-ventas-fgv-eaa46cb9da87.json"  # Reemplaza con tu archivo JSON

def conectar_sheets():
    """Autentica con Google Sheets y Drive"""
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
    cliente = gspread.authorize(creds)
    
    # Abrimos la hoja correctamente
    sheet_id = "1hi-XTGV1Asu1KAvw-hE7UKWgY6nJq3IakaR2OykrA8c"  # El ID de tu Google Sheet
    sheet = cliente.open_by_key(sheet_id)
 # Asegura que el nombre es correcto
    return sheet

# Columnas ordenadas en la hoja "Pedidos"
COLUMNS_PEDIDOS = ["ID", "Vendedor", "Cliente", "Dirección", "Teléfono", "Fecha de Entrega",
                   "Horario de Entrega", "Método de Pago", "Monto", "Pagado", "Observaciones", 
                   "Estado", "Productos", "Cantidades"]

COLUMNS_PRODUCTOS = ["ID Venta", "Fecha de Entrega", "Monto", "Vendedor", "Método de Pago", "Cliente", "Producto", "Cantidad"]

def obtener_o_crear_hoja(sheet, nombre_hoja, columnas=None):
    """Obtiene la hoja si existe, o la crea con encabezados"""
    try:
        hoja = sheet.worksheet(nombre_hoja)  # Intenta obtener la hoja
    except gspread.exceptions.WorksheetNotFound:
        hoja = sheet.add_worksheet(title=nombre_hoja, rows="1000", cols="20")  # Crea la hoja si no existe
        if columnas:
            hoja.append_row(columnas)  # Agregar encabezados
    return hoja

def guardar_en_sheets(datos, productos, cantidades):
    """Guarda los datos en las hojas de Google Sheets"""
    sheet = conectar_sheets()
    
    # Obtener o crear hojas
    hoja_pedidos = obtener_o_crear_hoja(sheet, "Pedidos", COLUMNS_PEDIDOS)
    hoja_productos = obtener_o_crear_hoja(sheet, "Productos Vendidos", COLUMNS_PRODUCTOS)

    # Concatenamos productos y cantidades en un solo string
    productos_str = ", ".join(productos)
    cantidades_str = ", ".join(map(str, cantidades))

    # Crear fila de datos ordenada
    fila = [
        datos["ID"], datos["Vendedor"], datos["Cliente"], datos["Dirección"], datos["Teléfono"], datos["Fecha de Entrega"], datos["Horario de Entrega"], datos["Método de Pago"], datos["Monto"], datos["Pagado"], productos_str, cantidades_str
    ]

    # 🔹 Agregar la fila en la hoja "Pedidos"
    hoja_pedidos.append_row(fila)

    # 🔹 Agregar cada producto vendido en la hoja "Productos Vendidos"
    for producto, cantidad in zip(productos, cantidades):
        hoja_productos.append_row([
            datos["ID"], datos["Fecha de Entrega"], datos["Monto"], 
            datos["Vendedor"], datos["Método de Pago"], datos["Cliente"], producto, int(cantidad)
        ])

    print("✅ Pedido guardado en Google Sheets")
