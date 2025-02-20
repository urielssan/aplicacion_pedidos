from flask import Flask, render_template, request, redirect, send_file
import pandas as pd
import os
from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER

app = Flask(__name__)

FILE_PATH = "pedidos.xlsx"
LOGO_PATH = os.path.join(os.getcwd(), "static", "logo.png")  # Ruta absoluta del logo

def init_excel():
    if not os.path.exists(FILE_PATH):
        df = pd.DataFrame(columns=[
            "Vendedor", "Cliente", "Dirección", "Teléfono", "Fecha de Entrega",
            "Horario de Entrega", "Método de Pago", "Monto", "Pagado",
            "Productos", "Cantidad", "Observaciones", "Estado"
        ])
        df.to_excel(FILE_PATH, index=False)

init_excel()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/enviar_pedido', methods=["POST"])
def enviar_pedido():
    df = pd.read_excel(FILE_PATH)
    pedido_id = len(df) + 1  # Número de orden basado en el ID de Excel

    vendedor = request.form["vendedor"]
    cliente = request.form["cliente"]
    direccion = request.form["direccion"]
    telefono = request.form["telefono"]
    fecha_entrega = request.form["fecha_entrega"]
    horario_entrega = request.form["horario_entrega"]
    metodo_pago = request.form["metodo_pago"]
    monto = float(request.form["monto"])
    pagado = request.form["pagado"]
    productos = request.form.getlist("productos[]")
    cantidades = request.form.getlist("cantidades[]")
    observaciones = request.form["observaciones"]
    estado = "Pendiente"

    # 🔹 **Nuevo: Diccionario de precios**
    precios_productos = {
        "Agua saborizada Naranja 3000ml": 3000,
        "Agua saborizada Naranja 1600ml": 1600,
        "Agua sin gas 2500ml": 2500,
        "Agua sin gas 1600ml": 1600,
        "Baguette Tradicional": 500,
        "BBQ Casera BBQ": 1500,
        "Champagne Brut Nature": 10000,
        "Cerveza Blond Ale": 2400,
        "Cerveza Porter": 2400,
        "Cerveza Scottish": 2400,
        "Vino Blanco Chardonay Orgánico": 8000,
        "Coca Cola Común 2L": 4000,
        "Coca Cola Común 500ml": 1800,
        "Coca Cola Zero 500ml": 1800,
        "Cordero Braseado Desmechado": 7500,
        "Criolla Casera": 1500,
        "Empanadas Ternera Suave": 1900,
        "Empanadas Cordero": 1900,
        "Empanadas Congeladas Cordero (12u)": 22800,
        "Empanadas Congeladas Carne (12u)": 22800,
        "Empanadas Espinaca": 1900,
        "Empanadas Congeladas Espinaca (12u)": 22800,
        "Empanadas Jamón y Queso": 1900,
        "Empanadas Congeladas Jamón y Queso (12u)": 22800,
        "Empanadas Congeladas Mozarella y Cebolla (12u)": 22800,
        "Empanadas Mozarella y Cebolla": 1900,
        "Empanadas Congeladas Pollo (12u)": 22800,
        "Empanadas Pollo": 1900,
        "Hamburguesa Novillo (2x)": 7200,
        "Hamburguesa Congeladas Crudas Cordero (2x)": 7500,
        "Hamburguesa Congeladas Crudas Novillo (2x)": 7500,
        "Helado Chocolate con Almendras": 5800,
        "Helado Dulce de Leche": 5800,
        "Helado Lemon Pie": 5800,
        "Helado Mascarpone": 5800,
        "Huevos de Campo (12u)": 2200,
        "Huevos de Campo (30u)": 4400,
        "Huevos de Campo (60u)": 8700,
        "Vino Malbec Orgánico": 8000,
        "Mayo de Morrón Casera": 1500,
        "Mignon Casero": 300,
        "Novillo Braseado Desmechado": 8000,
        "Pollo Braseado Desmechado": 8000,
        "Queso con Ciboulette": 1500,
        "Vino Rosado Orgánico": 8000,
        "Sándwich de Milanesa": 7200,
        "Sidra Red Delicious": 2400
    }

    # 🔹 **Nuevo: Obtener los precios correctos**
    precios = [precios_productos.get(p, 0) for p in productos]  # Si el producto no existe, asigna 0

    # Cálculo de descuento
    descuento = 0
    if metodo_pago in ["Efectivo", "Transferencia"]:
        descuento = 0.10 * monto if metodo_pago == "Efectivo" else 0.05 * monto
    total_final = monto - descuento

    # Guardar en Excel
    nuevo_pedido = pd.DataFrame([{
        "ID": pedido_id,
        "Vendedor": vendedor,
        "Cliente": cliente,
        "Dirección": direccion,
        "Teléfono": telefono,
        "Fecha de Entrega": fecha_entrega,
        "Horario de Entrega": horario_entrega,
        "Método de Pago": metodo_pago,
        "Monto": monto,
        "Pagado": pagado,
        "Productos": ", ".join([f"{p} (x{c})" for p, c in zip(productos, cantidades)]),
        "Observaciones": observaciones,
        "Estado": estado
    }])

    df = pd.concat([df, nuevo_pedido], ignore_index=True)
    df.to_excel(FILE_PATH, index=False)

    return generar_pdf(pedido_id, cliente, fecha_entrega, horario_entrega, metodo_pago, monto, descuento, total_final, pagado, productos, cantidades, precios, direccion, telefono, observaciones)

def generar_pdf(pedido_id, cliente, fecha_entrega, horario_entrega, metodo_pago, monto, descuento, total_final, pagado, productos, cantidades, precios, direccion, telefono, observaciones):
    pdf_path = f"orden_pedido_{pedido_id}.pdf"

    doc = SimpleDocTemplate(pdf_path, pagesize=(120 * mm, 250 * mm), leftMargin=5 * mm, rightMargin=5 * mm, topMargin=10 * mm, bottomMargin=5 * mm)
    elements = []
    styles = getSampleStyleSheet()
    styles["Normal"].fontSize = 10

    # Logo
    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=92, height=60)
        elements.append(logo)
    elements.append(Spacer(1, 10))

    # Sección 2: Número de Orden
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"<b>ORDEN DE PEDIDO #{pedido_id}</b>", styles["Heading3"]))
    elements.append(Spacer(1, 10))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", styles["Normal"]))

    # Sección 3: Tabla de Productos Minimalista
    table_data = [["Producto", "Cant.", "P. Unit", "Total"]]
    for producto, cantidad, precio in zip(productos, cantidades, precios):
        total_precio = precio * int(cantidad)
        table_data.append([producto, f"{cantidad}x", f"${precio:,.2f}", f"${total_precio:,.2f}"])

    table = Table(table_data, colWidths=[40 * mm, 25 * mm, 25 * mm, 25 * mm], hAlign='CENTER')
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 10))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", styles["Normal"]))

    # Sección 4: Subtotal, Descuento y Total
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Subtotal: ${monto:,.2f}", styles["Normal"]))
    if descuento > 0:
        elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Descuento: -${descuento:,.2f}", styles["Normal"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Total: ${total_final:,.2f}", styles["Normal"]))
    elements.append(Spacer(1, 10))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", styles["Normal"]))

    # Sección 5: Método de Pago y Envío
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Método de Pago: {metodo_pago}", styles["Normal"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Pagado: {pagado}", styles["Normal"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Fecha de Envío: {fecha_entrega}", styles["Normal"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Horario de Envío: {horario_entrega}", styles["Normal"]))
    elements.append(Spacer(1, 10))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", styles["Normal"]))

    # Sección 6: Datos del Cliente
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Cliente: {cliente}", styles["Normal"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Teléfono: {telefono}", styles["Normal"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Dirección: {direccion}", styles["Normal"]))
    elements.append(Spacer(1, 10))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", styles["Normal"]))

    # Sección 7: Observaciones
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Observaciones: {observaciones}", styles["Normal"]))

    # Aplicamos alineación centrada a los textos desde la sección 3 en adelante
    centered_style = styles["Normal"].clone('Centered')
    centered_style.alignment = TA_CENTER

    for i in range(3, len(elements)):  # Empezamos desde la tercera sección
        if isinstance(elements[i], Paragraph):  # Solo centramos los párrafos, no los Spacer ni Tablas
            elements[i].style = centered_style

    # Construimos el documento después de aplicar los estilos
    doc.build(elements)

    return send_file(pdf_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
