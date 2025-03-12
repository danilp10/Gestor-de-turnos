from flask import Flask, render_template


from trabajadores.modelo import actualizar_estados_iniciales
from trabajadores.rutas import configurar_rutas_trabajadores
from configuracion.rutas import configurar_rutas_configuracion
from planificacion.rutas import configurar_rutas_planificacion

app = Flask(__name__)

actualizar_estados_iniciales()

# Configurar rutas por módulos
configurar_rutas_trabajadores(app)
configurar_rutas_configuracion(app)
configurar_rutas_planificacion(app)

# Ruta principal con menú de opciones
@app.route('/')
def index():
    return render_template('inicio.html')

# Página de gestión de trabajadores
@app.route('/trabajadores')
def trabajadores():
    return render_template('gestionar_retenes.html')


if __name__ == "__main__":
    app.run(debug=True)
