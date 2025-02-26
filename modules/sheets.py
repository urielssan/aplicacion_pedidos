import gspread
from google.auth import default

# Columnas ordenadas en la hoja "Pedidos"
COLUMNS_PEDIDOS = ["ID", "Vendedor", "Cliente", "Dirección", "Teléfono", "Fecha de Entrega",
                   "Horario de Entrega", "Método de Pago", "Monto", "Pagado", "Observaciones", 
                   "Estado", "Productos", "Cantidades"]

def conectar_sheets():
    creds, _ = default(scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    cliente = gspread.authorize(creds)
    sheet = cliente.open("Ventas - App")  # Nombre exacto del Google Sheet
    return sheet

def obtener_o_crear_hoja(sheet, nombre_hoja, columnas=None):
    try:
        hoja = sheet.worksheet(nombre_hoja)  # Intenta obtener la hoja
    except gspread.exceptions.WorksheetNotFound:
        hoja = sheet.add_worksheet(title=nombre_hoja, rows="1000", cols="20")  # Crea la hoja si no existe
        if columnas:
            hoja.append_row(columnas)  # Agregar encabezados
    return hoja

def guardar_en_sheets(datos, productos, cantidades):
    sheet = conectar_sheets()
    
    # Verificar y obtener la hoja "Pedidos"
    hoja_pedidos = obtener_o_crear_hoja(sheet, "Pedidos", COLUMNS_PEDIDOS)
    hoja_productos = obtener_o_crear_hoja(sheet, "Productos Vendidos")
    # Concatenamos productos y cantidades en un solo string
    productos_str = ", ".join(productos)
    cantidades_str = ", ".join(map(str, cantidades))

    # Crear fila de datos ordenada
    fila = [
        datos["ID"], datos["Vendedor"], datos["Cliente"], datos["Dirección"], datos["Teléfono"],
        datos["Fecha de Entrega"], datos["Horario de Entrega"], datos["Método de Pago"],
        datos["Monto"], datos["Pagado"], datos["Observaciones"], datos["Estado"],
        productos_str, cantidades_str
    ]
        # Agregar cada producto vendido a la hoja "Productos Vendidos"
    for producto, cantidad in zip(productos, cantidades):
        hoja_productos.append_row([
            datos["ID"],datos["Fecha de Entrega"], producto, cantidad
        ])
    # Agregar la fila en la hoja "Pedidos"
    hoja_pedidos.append_row(fila)