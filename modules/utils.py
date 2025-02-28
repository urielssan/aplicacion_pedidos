import os
import pandas as pd
import sass
from modules.config import Config  # Importamos la configuración

def compile_scss():
    """Compila el archivo SCSS y lo convierte en CSS."""
    scss_file = os.path.join("static", "css", "styles.scss")
    css_file = os.path.join("static", "css", "styles.css")
    
    with open(scss_file, "r") as scss:
        scss_content = scss.read()

    css_content = sass.compile(string=scss_content)
    
    with open(css_file, "w") as css:
        css.write(css_content)

def init_excel():
    """Inicializa el archivo de Excel si no existe."""
    if not os.path.exists(Config.FILE_PATH):
        df = pd.DataFrame(columns=[
            "Vendedor", "Cliente", "Dirección", "Teléfono", "Fecha de Entrega",
            "Horario de Entrega", "Método de Pago", "Monto", "Pagado",
            "Productos", "Cantidad", "Observaciones", "Estado"
        ])
        df.to_excel(Config.FILE_PATH, index=False)
