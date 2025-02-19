from flask import Flask, render_template, request, redirect
import pandas as pd
import os

app = Flask(__name__)

# Nombre del archivo donde se guardan los pedidos
FILE_PATH = "pedidos.xlsx"

# Si no existe el archivo, lo crea con columnas básicas
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
    df = pd.read_excel(FILE_PATH)  # Cargar archivo actual

    vendedor = request.form["vendedor"]
    cliente = request.form["cliente"]
    direccion = request.form["direccion"]
    telefono = request.form["telefono"]
    fecha_entrega = request.form["fecha_entrega"]
    horario_entrega = request.form.get("horario_entrega", "No especificado")
    metodo_pago = request.form["metodo_pago"]
    monto = request.form["monto"]
    pagado = request.form["pagado"]
    productos = request.form.getlist("productos[]")
    cantidades = request.form.getlist("cantidades[]")
    observaciones = request.form["observaciones"]
    estado = "Pendiente"

    # Unir productos con sus cantidades en un solo string
    productos_cantidades = ", ".join([f"{p} (x{c})" for p, c in zip(productos, cantidades)])

    # Crear nuevo DataFrame
    nuevo_pedido = pd.DataFrame([{
        "Vendedor": vendedor,
        "Cliente": cliente,
        "Dirección": direccion,
        "Teléfono": telefono,
        "Fecha de Entrega": fecha_entrega,
        "Horario de Entrega": horario_entrega,
        "Método de Pago": metodo_pago,
        "Monto": monto,
        "Pagado": pagado,
        "Productos": productos_cantidades,
        "Observaciones": observaciones,
        "Estado": estado
    }])

    # Asegurar que las columnas coincidan con el archivo Excel
    nuevo_pedido = nuevo_pedido[df.columns.intersection(nuevo_pedido.columns)]

    # Concatenar y guardar
    df = pd.concat([df, nuevo_pedido], ignore_index=True)
    df.to_excel(FILE_PATH, index=False)

    return redirect("/pedidos")



@app.route('/pedidos')
def pedidos():
    df = pd.read_excel(FILE_PATH)
    return render_template("pedidos.html", pedidos=df.to_dict(orient='records'))

@app.route('/preparado/<int:pedido_id>')
def marcar_preparado(pedido_id):
    df = pd.read_excel(FILE_PATH)
    df.at[pedido_id, "Estado"] = "Preparado"
    df.to_excel(FILE_PATH, index=False)
    return redirect("/pedidos")

if __name__ == '__main__':
    app.run(debug=True)
