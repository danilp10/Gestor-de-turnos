const express = require('express');
const cors = require('cors');
const fs = require('fs').promises;
const path = require('path');
const app = express();
const port = 5701;

app.use(cors());
app.use(express.json());

// Ruta al archivo JSON
const DATA_FILE = path.join(__dirname, 'trabajadores/disponibilidades.json');

// Función para leer datos del archivo
async function leerDatos() {
    try {
        const data = await fs.readFile(DATA_FILE, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        if (error.code === 'ENOENT') {
            // Si el archivo no existe, crear uno nuevo con array vacío
            await fs.writeFile(DATA_FILE, JSON.stringify([], null, 2));
            return [];
        }
        throw error;
    }
}

// Función para guardar datos en el archivo
async function guardarDatos(datos) {
    await fs.writeFile(DATA_FILE, JSON.stringify(datos, null, 2));
}

// Función para determinar el estado del trabajador
function determinarEstado(reincorporacion) {
    if (!reincorporacion) return 'activo';
    const fechaReincorporacion = new Date(reincorporacion);
    const fechaActual = new Date();
    return fechaReincorporacion > fechaActual ? 'baja' : 'activo';
}

// Endpoint para recibir datos de recursos humanos
app.post('/api/recursos', async (req, res) => {
    try {
        const { id, nombre, apellidos, disponibilidad, diasNoDisponibles, excepciones } = req.body;

        // Validación básica de datos
        if (!id || !nombre || !apellidos || !disponibilidad) {
            return res.status(400).json({
                status: 'error',
                mensaje: 'Faltan campos obligatorios (id, nombre, apellidos, disponibilidad)'
            });
        }

        // Leer datos existentes
        const recursos = await leerDatos();

        // Verificar si ya existe un trabajador con ese ID
        const trabajadorExistente = recursos.find(r => r.id === id);
        if (trabajadorExistente) {
            return res.status(409).json({
                status: 'error',
                mensaje: 'Ya existe un trabajador con este ID',
                tipo: 'ID_DUPLICADO'
            });
        }

        // Determinar el estado del trabajador
        const estado = determinarEstado(excepciones?.reincorporacion);

        // Construir el objeto con timestamp y estado
        const recurso = {
            id,
            nombre,
            apellidos,
            estado,
            disponibilidad,
            diasNoDisponibles: diasNoDisponibles || [],
            excepciones: excepciones || {},
            timestamp: new Date().toISOString()
        };

        // Añadir al array y guardar en archivo
        recursos.push(recurso);
        await guardarDatos(recursos);

        console.log('Datos recibidos y guardados:', recurso);

        res.json({
            status: 'ok',
            mensaje: 'Datos recibidos y guardados correctamente',
            datos: recurso
        });
    } catch (error) {
        console.error('Error al procesar la solicitud:', error);
        res.status(500).json({
            status: 'error',
            mensaje: 'Error interno del servidor'
        });
    }
});

// Endpoint para actualizar datos de un recurso existente
app.put('/api/recursos/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const datosActualizados = req.body;

        const recursos = await leerDatos();
        const index = recursos.findIndex(r => r.id === id)

        if (index === -1) {
            return res.status(404).json({
                status: 'error',
                mensaje: 'Recurso no encontrado'
            });
        }

        // Actualizar estado
        datosActualizados.estado = determinarEstado(datosActualizados.excepciones?.reincorporacion);
        datosActualizados.timestamp = new Date().toISOString();

        recursos[index] = {
            ...recursos[index],
            ...datosActualizados
        };

        await guardarDatos(recursos);

        res.json({
            status: 'ok',
            mensaje: 'Datos actualizados correctamente',
            datos: recursos[index]
        });
    } catch (error) {
        console.error('Error al actualizar recurso:', error);
        res.status(500).json({
            status: 'error',
            mensaje: 'Error interno del servidor'
        });
    }
});

// Endpoint para obtener un recurso específico
app.get('/api/recursos/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const recursos = await leerDatos();
        const recurso = recursos.find(r => r.id === id)

        if (!recurso) {
            return res.status(404).json({
                status: 'error',
                mensaje: 'Recurso no encontrado'
            });
        }

        res.json(recurso);
    } catch (error) {
        console.error('Error al obtener recurso:', error);
        res.status(500).json({
            status: 'error',
            mensaje: 'Error interno del servidor'
        });
    }
});

// Endpoint para ver todos los recursos almacenados
app.get('/api/recursos', async (req, res) => {
    try {
        const recursos = await leerDatos();
        res.json({
            status: 'ok',
            total: recursos.length,
            recursos
        });
    } catch (error) {
        console.error('Error al obtener recursos:', error);
        res.status(500).json({
            status: 'error',
            mensaje: 'Error interno del servidor'
        });
    }
});

app.get('/start-server', (req, res) => {
    res.send('El servidor ya está en ejecución.');
});

app.listen(port, () => {
    console.log(`Servidor corriendo en http://localhost:${port}`);
});
