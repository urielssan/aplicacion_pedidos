from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
from modules.utils import compile_scss, init_excel
from modules.pdf_generator import generar_pdf
from modules.precios_productos import precios_productos
from modules.sheets import conectar_sheets, guardar_en_sheets, obtener_o_crear_hoja
from functools import wraps
from datetime import datetime

import os

app = Flask(__name__)
app.secret_key = "clave_secreta"


#Datos de autenticación
USUARIO_ADMIN = "admin"
CONTRASEÑA_ADMIN = "admin123"


# Configuraciones
FILE_PATH = os.path.join(os.getcwd(), "pedidos.xlsx")
LOGO_PATH = os.path.join(os.getcwd(), "static", "images", "logo.png")
# Inicializar configuraciones
compile_scss()
init_excel()


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        contraseña = request.form["contraseña"]

        if usuario == USUARIO_ADMIN and contraseña == CONTRASEÑA_ADMIN:
            session["usuario"] = usuario
            next_page = request.args.get("next")  # 🔹 Ver si había una página previa
            return redirect(next_page or url_for("index"))  # 🔹 Ir a la página previa o index

        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")

    return render_template("login.html")



# 🔹 Decorador para proteger rutas

def login_requerido(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))  # 🔹 Redirigir a login si no está autenticado
        return f(*args, **kwargs)
    return decorador


@app.route('/logout')
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))

@app.errorhandler(500)
def error_servidor(e):
    return redirect(url_for("login"))



@app.route('/')
@login_requerido
def index():
    return render_template("index.html")

@app.route('/ver_pedidos')
@login_requerido
def ver_pedidos():
    """Trae los pedidos de Google Sheets y los muestra en una tabla."""
    sheet = conectar_sheets()
    hoja_pedidos = sheet.worksheet("Pedidos")  # Asegurate de que el nombre coincida con el de la hoja en Google Sheets

    pedidos = hoja_pedidos.get_all_values()  # Obtiene todos los pedidos en forma de lista de listas

    if not pedidos:
        return render_template("ver_pedidos.html", pedidos=[])

    # Convertimos los datos en una lista de diccionarios
    headers = pedidos[0]  # La primera fila son los encabezados
    datos_pedidos = [dict(zip(headers, row)) for row in pedidos[1:]]  # Excluimos la primera fila

    return render_template("ver_pedidos.html", pedidos=datos_pedidos)


@app.route('/enviar_pedido', methods=["POST"])
@login_requerido
def enviar_pedido():
    df_pedidos = pd.read_excel(FILE_PATH, sheet_name="Pedidos", engine="openpyxl")
    try:
        df_productos = pd.read_excel(FILE_PATH, sheet_name="Productos Vendidos", engine="openpyxl")
    except ValueError:
        df_productos = pd.DataFrame(columns=["ID Venta", "Producto", "Cantidad"])

    pedido_id = len(df_pedidos) + 1

    vendedor = request.form["vendedor"]
    cliente = request.form["cliente"]
    direccion = request.form["direccion"]
    telefono = request.form["telefono"]
    
    fecha_entrega = request.form["fecha_entrega"]  # mantenelo como str directamente
    
    horario_entrega = request.form["horario_entrega"]
    metodo_pago = request.form["metodo_pago"]
    monto = float(request.form["monto"])
    pagado = request.form["pagado"]
    productos = request.form.getlist("productos[]")
    cantidades = [int(c) for c in request.form.getlist("cantidades[]")]
    observaciones = request.form["observaciones"]
    estado = request.form["estado"]

    precios = [precios_productos.get(p, 0) for p in productos]

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

    df_pedidos = pd.concat([df_pedidos, nuevo_pedido], ignore_index=True)

    productos_vendidos = pd.DataFrame([
        {"ID Venta": pedido_id, "Producto": p, "Cantidad": c}
        for p, c in zip(productos, cantidades)
    ])

    df_productos = pd.concat([df_productos, productos_vendidos], ignore_index=True)

    with pd.ExcelWriter(FILE_PATH, engine="openpyxl") as writer:
        df_pedidos.to_excel(writer, sheet_name="Pedidos", index=False)
        df_productos.to_excel(writer, sheet_name="Productos Vendidos", index=False)

    datos_pedido = {
        "ID": pedido_id,
        "Vendedor": vendedor,
        "Cliente": cliente,
        "Dirección": direccion,
        "Teléfono": telefono,
        "Fecha de Entrega": fecha_entrega,  # Se mantiene el formato YYYY-MM-DD
        "Horario de Entrega": horario_entrega,
        "Método de Pago": metodo_pago,
        "Monto": monto,
        "Pagado": pagado,
        "Observaciones": observaciones,
        "Estado": estado
    }

    guardar_en_sheets(datos_pedido, productos, cantidades)

    return generar_pdf(pedido_id, cliente, fecha_entrega, horario_entrega, metodo_pago, monto, 0, monto, pagado, productos, cantidades, precios, direccion, telefono, observaciones)

@app.route("/editar_pedidos")
def editar_pedidos():
    """Trae los pedidos de Google Sheets y los muestra en una tabla editable."""
    sheet = conectar_sheets()
    hoja_pedidos = sheet.worksheet("Pedidos")
    pedidos = hoja_pedidos.get_all_values()  # Obtiene todos los pedidos

    # Convertimos los datos en una lista de diccionarios
    headers = pedidos[0]
    datos_pedidos = [dict(zip(headers, row)) for row in pedidos[1:]]  # Excluimos la primera fila (encabezados)

    return render_template("editar_pedidos.html", pedidos=datos_pedidos)

@app.route("/actualizar_pedido", methods=["POST"])
def actualizar_pedido():
    pedido_id = request.form["id"].strip()
    estado = request.form["estado"]
    metodo_pago = request.form["metodo_pago"]
    descuentoOn = request.form["descuentoOn"]
    monto = float(request.form["monto"][1:])  # Eliminar el símbolo "$"
    pagado = request.form["pagado"]
    horario_entrega = request.form["horario_entrega"]

    # Obtener productos editados
    productos = request.form.getlist("productos[]")
    cantidades = [int(c) for c in request.form.getlist("cantidades[]")]

    # Conectar con Google Sheets
    sheet = conectar_sheets()
    hoja_pedidos = sheet.worksheet("Pedidos")
    hoja_productos = sheet.worksheet("Productos Vendidos")

    # Buscar pedido en la hoja
    pedidos = hoja_pedidos.get_all_values()
    pedido_encontrado = False

    for i, row in enumerate(pedidos):
        row_id = str(row[0]).strip()
        if row_id == pedido_id:
            print(f"✅ Pedido encontrado en fila {i+1}")

            # Recalcular monto con descuento
            subtotal = sum(precios_productos.get(p, 0) * c for p, c in zip(productos, cantidades))
            descuento = 0.05 if descuentoOn == "Sí" else 0
            total_final = subtotal - (subtotal * descuento)

            # Actualizar Google Sheets con la fecha en formato "YYYY-MM-DD"
            hoja_pedidos.update(f"G{i+1}", [[horario_entrega]])  # Horario de entrega
            hoja_pedidos.update(f"H{i+1}", [[metodo_pago]])  # Metodo de pago
            hoja_pedidos.update(f"I{i+1}", [[total_final]])  # Monto
            hoja_pedidos.update(f"J{i+1}", [[pagado]])  # Pagado
            hoja_pedidos.update(f"M{i+1}", [[estado]])  # Estado
            # Escribir productos en la columna K
            # Asegúrate de que productos y cantidades sean listas
            productos = list(productos)
            cantidades = list(cantidades)

            # Concatenar productos en una sola cadena separada por comas
            productos_str = ",".join(productos)

            # Concatenar cantidades en una sola cadena separada por comas
            cantidades_str = ",".join(map(str, cantidades))

            # Escribir productos en la columna K
            hoja_pedidos.update(f"K{i + 1}", [[productos_str]])

            # Escribir cantidades en la columna L
            hoja_pedidos.update(f"L{i + 1}", [[cantidades_str]])
                        

            # Actualizar tabla de "Productos Vendidos"
            hoja_productos.clear()
            for p, c in zip(productos, cantidades):
                hoja_productos.append_row([pedido_id, p, c])

            pedido_encontrado = True
            break

    if not pedido_encontrado:
        print(f"❌ Error: No se encontró el pedido con ID {pedido_id}")
        return f"Error: Pedido {pedido_id} no encontrado", 404

    return redirect(url_for("editar_pedidos"))




if __name__ == '__main__':
    app.run(debug=True)
