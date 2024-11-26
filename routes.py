from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from db_connection import get_db_connection  # Asegúrate de que esta función devuelve una conexión a la base de datos
from forms import VueloForm, ReservaForm, LoginForm, RegistroForm
from models import obtener_ticket_por_vuelo_id

app_routes = Blueprint('app_routes', __name__)

# Página de inicio
@app_routes.route('/')
def index():
    return render_template('index.html')

# Ruta para iniciar sesión
@app_routes.route('/iniciar_sesion', methods=['GET', 'POST'])
def iniciar_sesion():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM usuario WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and user[4] == password:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[5]

            flash('¡Inicio de sesión exitoso!', 'success')

            if user[5] == 'administrador':
                return redirect(url_for('app_routes.admin_dashboard'))
            return redirect(url_for('app_routes.bienvenida_cliente'))
        flash('Nombre de usuario o contraseña incorrectos.', 'danger')

        cursor.close()
        connection.close()

    return render_template('iniciar_sesion.html', form=form)

@app_routes.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'administrador':
        flash("No tienes permisos para acceder a esta página", "danger")
        return redirect(url_for('app_routes.iniciar_sesion'))

    connection = get_db_connection()
    cursor = connection.cursor()

    # Obtener los vuelos registrados
    cursor.execute("""
        SELECT id, vuelo_id, operador, precio, salida, fecha_salida, hora_salida, 
               llegada, fecha_llegada, hora_llegada, tipo_vuelo, modo_vuelo, matricula
        FROM vueloandm
    """)
    vuelos = cursor.fetchall()

    # Obtener los pagos registrados
    cursor.execute("""
        SELECT p.pago_id, p.reserva_id, p.monto, p.fecha_pago, p.metodo_pago, 
               p.estado_pago, p.ultimos_cuatro_digitos
        FROM pagos p
    """)
    pagos = cursor.fetchall()

    # Obtener reservas pagadas
    cursor.execute("""
        SELECT r.reserva_id, u.nombre AS cliente_nombre, v.salida, v.llegada, 
               v.fecha_salida, v.hora_salida, v.fecha_llegada, v.hora_llegada, 
               v.modo_vuelo, v.precio, p.fecha_pago, p.estado_pago
        FROM reservas r
        JOIN usuario u ON r.usuario_id = u.id
        JOIN vueloandm v ON r.vuelo_id = v.vuelo_id
        JOIN pagos p ON p.reserva_id = r.reserva_id
        WHERE p.estado_pago = 'Pagado'
    """)
    reservas_pagadas = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        'admin_dashboard.html', 
        vuelos=vuelos, pagos=pagos, reservas_pagadas=reservas_pagadas
    )


# Crear nuevo vuelo
@app_routes.route('/crear_vuelo', methods=['GET', 'POST'])
def crear_vuelo():
    if request.method == 'POST':
        # Procesar datos del formulario
        vuelo_id = request.form['vuelo_id']
        operador = request.form['operador']
        matricula = request.form['matricula']
        precio = request.form['precio']
        salida = request.form['salida']
        llegada = request.form['llegada']
        fecha_salida = request.form['fecha_salida']
        hora_salida = request.form['hora_salida']
        fecha_llegada = request.form['fecha_llegada']
        hora_llegada = request.form['hora_llegada']
        tipo_vuelo = request.form['tipo_vuelo']
        modo_vuelo = request.form['modo_vuelo']

        # Insertar datos en la base de datos
        connection = get_db_connection()
        cursor = connection.cursor()
        query = """
        INSERT INTO vueloandm (vuelo_id, operador, matricula, precio, salida, llegada, fecha_salida, hora_salida,
                               fecha_llegada, hora_llegada, tipo_vuelo, modo_vuelo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (vuelo_id, operador, matricula, precio, salida, llegada, fecha_salida, hora_salida,
                               fecha_llegada, hora_llegada, tipo_vuelo, modo_vuelo))
        connection.commit()
        cursor.close()
        connection.close()

        flash('Vuelo creado exitosamente.', 'success')
        return redirect(url_for('app_routes.admin_dashboard'))

    # Opciones dinámicas para tipo y modo de vuelo
    tipos_vuelo = ["ida", "redondo", "directo", "escalas"]
    modos_vuelo = ["comercial", "privado", "publico", "ejecutivo"]

    return render_template('crear_vuelo.html', tipos_vuelo=tipos_vuelo, modos_vuelo=modos_vuelo)

@app_routes.route('/actualizar_vuelo/<int:vuelo_id>', methods=['GET', 'POST'])
def actualizar_vuelo(vuelo_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    if request.method == 'POST':
        # Obtén los datos del formulario
        operador = request.form.get('operador')
        precio = request.form.get('precio')
        salida = request.form.get('salida')
        llegada = request.form.get('llegada')
        fecha_salida = request.form.get('fecha_salida')
        fecha_llegada = request.form.get('fecha_llegada')

        # Actualiza los datos en la base de datos
        cursor.execute("""
            UPDATE vueloandm
            SET operador = %s, precio = %s, salida = %s, llegada = %s, fecha_salida = %s, fecha_llegada = %s
            WHERE vuelo_id = %s
        """, (operador, precio, salida, llegada, fecha_salida, fecha_llegada, vuelo_id))

        connection.commit()
        flash('Vuelo actualizado exitosamente', 'success')
        cursor.close()
        connection.close()

        return redirect(url_for('app_routes.admin_dashboard'))

    # Obtén la información del vuelo
    cursor.execute("SELECT * FROM vueloandm WHERE vuelo_id = %s", (vuelo_id,))
    vuelo = cursor.fetchone()

    cursor.close()
    connection.close()

    return render_template('actualizar_vuelo.html', vuelo=vuelo)

@app_routes.route('/reservas_pagadas')
def reservas_pagadas():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""SELECT * FROM reservas_pagadas""")  # Modifica la consulta según tus datos
    reservas_pagadas = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('reservas_pagadas.html', reservas_pagadas=reservas_pagadas)

@app_routes.route('/vuelos_pagados', methods=['GET', 'POST'])
def vuelos_pagados():
    connection = get_db_connection()
    cursor = connection.cursor()

    if request.method == 'POST':
        # Si se envió un formulario, procesamos la creación de un nuevo vuelo
        vuelo_id = request.form.get('vuelo_id')
        matricula = request.form.get('matricula')
        operador = request.form.get('operador')
        precio = request.form.get('precio')
        salida = request.form.get('salida')
        fecha_salida = request.form.get('fecha_salida')
        hora_salida = request.form.get('hora_salida')
        llegada = request.form.get('llegada')
        fecha_llegada = request.form.get('fecha_llegada')
        hora_llegada = request.form.get('hora_llegada')
        tipo_vuelo = request.form.get('tipo_vuelo')
        modo_vuelo = request.form.get('modo_vuelo')

        # Insertar nuevo vuelo
        cursor.execute("""
            INSERT INTO vueloandm (id, vuelo_id, matricula, operador, precio, salida, fecha_salida, hora_salida, llegada, fecha_llegada, hora_llegada, tipo_vuelo, modo_vuelo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (session['user_id'], vuelo_id, matricula, operador, precio, salida, fecha_salida, hora_salida, llegada, fecha_llegada, hora_llegada, tipo_vuelo, modo_vuelo))
        connection.commit()
        flash('Vuelo creado exitosamente', 'success')

    # Obtener vuelos pagados
    cursor.execute("""
        SELECT v.vuelo_id, v.operador, v.precio, v.salida, v.llegada, v.fecha_salida, v.fecha_llegada, v.tipo_vuelo, v.modo_vuelo
        FROM vueloandm v
        JOIN pagos p ON v.vuelo_id = p.reserva_id
        WHERE p.estado_pago = 'Pagado'
    """)
    vuelos_pagados = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('vuelos_pagados.html', vuelos_pagados=vuelos_pagados)


@app_routes.route('/borrar_vuelo/<int:vuelo_id>', methods=['POST'])
def borrar_vuelo(vuelo_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Elimina el vuelo
    cursor.execute("DELETE FROM vueloandm WHERE vuelo_id = %s", (vuelo_id,))
    connection.commit()

    flash('Vuelo eliminado exitosamente', 'success')
    cursor.close()
    connection.close()

    return redirect(url_for('app_routes.admin_dashboard'))


@app_routes.route('/reporte_ganancias', methods=['GET'])
def reporte_ganancias():
    if 'user_id' not in session or session.get('role') != 'administrador':
        flash("No tienes permisos para acceder a esta página", "danger")
        return redirect(url_for('app_routes.iniciar_sesion'))

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Consulta SQL
        cursor.execute("""
            SELECT DATE(fecha_pago) AS fecha, SUM(monto) AS total_ganancias
            FROM pagos
            WHERE estado_pago = 'Pagado'
            GROUP BY DATE(fecha_pago)
            ORDER BY fecha DESC
        """)
        ganancias = cursor.fetchall()
        print("Ganancias obtenidas:", ganancias)

    except Exception as e:
        print("Error al obtener los datos:", e)
        flash("Error al generar el reporte de ganancias.", "danger")
        ganancias = []

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

    return render_template('reporte_ganancias.html', ganancias=ganancias)



# Estadísticas de métodos de pago
@app_routes.route('/estadisticas_pago', methods=['GET'])
def estadisticas_pago():
    if 'user_id' not in session or session.get('role') != 'administrador':
        flash("No tienes permisos para acceder a esta página", "danger")
        return redirect(url_for('app_routes.iniciar_sesion'))

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT metodo_pago, COUNT(*) AS cantidad
        FROM pagos
        WHERE estado_pago = 'Pagado'
        GROUP BY metodo_pago
        ORDER BY cantidad DESC
    """)
    estadisticas = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('estadisticas_pago.html', estadisticas=estadisticas)
@app_routes.route('/recomendaciones', methods=['GET'])
def recomendaciones():
    # Obtener las recomendaciones de la base de datos
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT recomendacion_id, titulo, descripcion, imagen_url FROM recomendaciones")
    recomendaciones = cursor.fetchall()  # La tupla ahora incluye recomendacion_id
    cursor.close()
    connection.close()

    # Pasar las recomendaciones al template
    return render_template('recomendaciones.html', recomendaciones=recomendaciones)

@app_routes.route('/eliminar_recomendacion/<int:id>', methods=['POST'])
def eliminar_recomendacion(id):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Eliminar la recomendación
    cursor.execute("DELETE FROM recomendaciones WHERE recomendacion_id = %s", (id,))
    connection.commit()
    cursor.close()
    connection.close()

    flash("Recomendación eliminada exitosamente.", "success")
    return redirect(url_for('app_routes.recomendaciones'))
import os
from flask import Flask, request, render_template, redirect, url_for, flash, Blueprint
from werkzeug.utils import secure_filename



# Configuración para subir imágenes
UPLOAD_FOLDER = 'static/uploads'  # Carpeta donde se guardarán las imágenes
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


@app_routes.route('/actualizar_recomendacion/<int:id>', methods=['GET', 'POST'])
def actualizar_recomendacion(id):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Obtener los datos actuales de la recomendación
    cursor.execute("SELECT recomendacion_id, titulo, descripcion, imagen_url FROM recomendaciones WHERE recomendacion_id = %s", (id,))
    recomendacion = cursor.fetchone()

    if not recomendacion:
        flash("Recomendación no encontrada.", "danger")
        return redirect(url_for('app_routes.recomendaciones'))

    if request.method == 'POST':
        # Capturar los datos actualizados desde el formulario
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')

        # Manejo de la imagen subida
        if 'imagen' in request.files and request.files['imagen']:
            imagen = request.files['imagen']
            nombre_archivo = secure_filename(imagen.filename)
            ruta_imagen = os.path.join(UPLOAD_FOLDER, nombre_archivo)
            imagen.save(ruta_imagen)
        else:
            nombre_archivo = recomendacion[3]  # Mantener la imagen anterior

        # Actualizar la recomendación en la base de datos
        cursor.execute("""
            UPDATE recomendaciones
            SET titulo = %s, descripcion = %s, imagen_url = %s
            WHERE recomendacion_id = %s
        """, (titulo, descripcion, nombre_archivo, id))
        connection.commit()

        flash("Recomendación actualizada exitosamente.", "success")
        return redirect(url_for('app_routes.recomendaciones'))

    # Renderizar el formulario con los datos actuales
    cursor.close()
    connection.close()
    return render_template('actualizar_recomendacion.html', recomendacion=recomendacion)




def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Asegúrate de que la carpeta exista
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app_routes.route('/crear_recomendacion', methods=['GET', 'POST'])
def crear_recomendacion():
    if request.method == 'POST':
        # Capturar los datos del formulario
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        imagen = request.files.get('imagen')

        # Guardar la imagen en la carpeta uploads
        if imagen:
            nombre_archivo = secure_filename(imagen.filename)
            ruta_imagen = os.path.join(UPLOAD_FOLDER, nombre_archivo)
            imagen.save(ruta_imagen)

            # Guardar la recomendación en la base de datos
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO recomendaciones (titulo, descripcion, imagen_url)
                VALUES (%s, %s, %s)
            """, (titulo, descripcion, nombre_archivo))
            connection.commit()
            cursor.close()
            connection.close()

            flash("Recomendación creada exitosamente.", "success")
            return redirect(url_for('app_routes.recomendaciones'))

    return render_template('crear_recomendacion.html')


@app_routes.route('/admin/crear_promocion', methods=['GET', 'POST'])
def crear_promocion():
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        descripcion = request.form.get('descripcion')
        descuento = request.form.get('descuento')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO promociones (codigo, descripcion, descuento, fecha_inicio, fecha_fin)
            VALUES (%s, %s, %s, %s, %s)
        """, (codigo, descripcion, descuento, fecha_inicio, fecha_fin))
        connection.commit()
        cursor.close()
        connection.close()

        flash('Promoción creada exitosamente.', 'success')
        return redirect(url_for('app_routes.listar_promociones'))

    return render_template('crear_promocion.html')

@app_routes.route('/admin/promociones', methods=['GET'])
def listar_promociones():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT promocion_id, codigo, descripcion, descuento, fecha_inicio, fecha_fin
        FROM promociones
    """)
    promociones = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('administrar_promociones.html', promociones=promociones)


@app_routes.route('/admin/promociones/editar/<int:promocion_id>', methods=['GET', 'POST'])
def editar_promocion(promocion_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        codigo = request.form.get('codigo')
        descripcion = request.form.get('descripcion')
        descuento = request.form.get('descuento')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')

        cursor.execute("""
            UPDATE promociones
            SET codigo = %s, descripcion = %s, descuento = %s, fecha_inicio = %s, fecha_fin = %s
            WHERE promocion_id = %s
        """, (codigo, descripcion, descuento, fecha_inicio, fecha_fin, promocion_id))
        connection.commit()
        cursor.close()
        connection.close()

        flash('Promoción actualizada exitosamente.', 'success')
        return redirect(url_for('app_routes.listar_promociones'))

    cursor.execute("SELECT * FROM promociones WHERE promocion_id = %s", (promocion_id,))
    promocion = cursor.fetchone()
    cursor.close()
    connection.close()

    return render_template('editar_promocion.html', promocion=promocion)

@app_routes.route('/admin/promociones/borrar/<int:promocion_id>', methods=['POST'])
def borrar_promocion(promocion_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM promociones WHERE promocion_id = %s", (promocion_id,))
    connection.commit()
    cursor.close()
    connection.close()

    flash('Promoción eliminada exitosamente.', 'success')
    return redirect(url_for('app_routes.listar_promociones'))



@app_routes.route('/bienvenida')
def bienvenida_cliente():
    # Verifica si el cliente inició sesión
    if 'user_id' not in session or session.get('role') != 'cliente':
        flash("Por favor, inicia sesión primero", "danger")
        return redirect(url_for('app_routes.iniciar_sesion'))
    # Muestra la página de bienvenida
    return render_template('bienvenida_cliente_aerolinea.html')


@app_routes.route('/cliente_dashboard', methods=['GET'])
def cliente_dashboard():
    if 'user_id' not in session or session.get('role') != 'cliente':
        flash("No tienes permisos para acceder a esta página", "danger")
        return redirect(url_for('app_routes.iniciar_sesion'))

    cliente_id = session['user_id']

    try:
        # Conexión a la base de datos
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Consulta para obtener las reservas del cliente
        cursor.execute("""
            SELECT r.reserva_id, v.salida, v.llegada, v.fecha_salida, v.hora_salida,
                   v.fecha_llegada, v.hora_llegada, v.precio
            FROM reservas r
            JOIN vueloandm v ON r.vuelo_id = v.vuelo_id
            WHERE r.usuario_id = %s
        """, (cliente_id,))
        reservas = cursor.fetchall()

        cursor.close()
        connection.close()

        # Renderizar la plantilla con las reservas
        return render_template('cliente_dashboard.html', reservas=reservas)

    except Exception as e:
        flash(f"Error al cargar las reservas: {str(e)}", "danger")
        return render_template('cliente_dashboard.html', reservas=[])



@app_routes.route('/buscar_vuelo', methods=['POST'])
def buscar_vuelo():
    salida = request.form.get('salida')
    llegada = request.form.get('llegada')
    tipo_vuelo = request.form.get('tipo_vuelo')  # Filtro adicional
    modo_vuelo = request.form.get('modo_vuelo')  # Filtro adicional

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT * FROM vueloandm 
        WHERE salida = %s AND llegada = %s
    """
    params = [salida, llegada]

    if tipo_vuelo:
        query += " AND tipo_vuelo = %s"
        params.append(tipo_vuelo)

    if modo_vuelo:
        query += " AND modo_vuelo = %s"
        params.append(modo_vuelo)

    cursor.execute(query, params)
    vuelos = cursor.fetchall()

    cursor.close()
    connection.close()

    if vuelos:
        return render_template('cliente_dashboard.html', vuelos=vuelos, busqueda_realizada=True)
    else:
        flash("No se encontraron vuelos con los criterios seleccionados.", "warning")
        return render_template('cliente_dashboard.html', vuelos=[], busqueda_realizada=True)


@app_routes.route('/cancelar_ticket/<int:ticket_id>', methods=['GET', 'POST'])
def cancelar_ticket(ticket_id):
    # Verifica si el usuario tiene acceso
    if 'user_id' not in session:
        flash("Debes iniciar sesión para realizar esta acción.", "warning")
        return redirect(url_for('app_routes.iniciar_sesion'))

    # Lógica para cancelar el ticket
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Eliminar el ticket basado en su ID
        cursor.execute("DELETE FROM tickets WHERE id = %s", (ticket_id,))
        connection.commit()
        flash("El ticket ha sido cancelado exitosamente.", "success")
    except Exception as e:
        connection.rollback()
        flash(f"Error al cancelar el ticket: {str(e)}", "danger")
    finally:
        cursor.close()
        connection.close()

    # Redirige a la página de bienvenida o a la lista de tickets
    return redirect(url_for('app_routes.bienvenida_cliente_aerolinea.html'))


@app_routes.route('/promociones_cliente', methods=['GET'])
def mostrar_promociones_cliente():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT promocion_id, codigo, descripcion, descuento, fecha_inicio, fecha_fin
        FROM promociones
    """)
    promociones = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('promociones_cliente.html', promociones=promociones)


@app_routes.route('/seleccionar_vuelo/<int:vuelo_id>', methods=['GET', 'POST'])
def seleccionar_vuelo(vuelo_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Obtener los detalles del vuelo seleccionado
    cursor.execute("SELECT * FROM vueloandm WHERE vuelo_id = %s", (vuelo_id,))
    vuelo = cursor.fetchone()

    cursor.close()
    connection.close()

    if request.method == 'POST':
        flash(f"Has seleccionado el vuelo {vuelo_id} correctamente.", "success")
        return redirect(url_for('app_routes.reservar_vuelo', vuelo_id=vuelo_id))

    return render_template('seleccionar_vuelo.html', vuelo=vuelo)


@app_routes.route('/reservar_vuelo/<int:vuelo_id>', methods=['GET', 'POST'])
def reservar_vuelo(vuelo_id):
    if 'user_id' not in session or session.get('role') != 'cliente':
        flash("No tienes permisos para realizar una reserva", "danger")
        return redirect(url_for('app_routes.iniciar_sesion'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM vueloandm WHERE vuelo_id = %s", (vuelo_id,))
    vuelo = cursor.fetchone()
    cursor.close()
    connection.close()

    if vuelo is None:
        flash("Vuelo no encontrado", "danger")
        return redirect(url_for('app_routes.buscar_vuelo'))

    if request.method == 'POST':
        usuario_id = session['user_id']
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO reservas (usuario_id, vuelo_id) VALUES (%s, %s)", (usuario_id, vuelo_id))
        connection.commit()
        reserva_id = cursor.lastrowid
        cursor.close()
        connection.close()

        flash('Reserva realizada exitosamente', 'success')
        return redirect(url_for('app_routes.pago', reserva_id=reserva_id))

    return render_template('confirmar_reserva.html', vuelo=vuelo)

@app_routes.route('/pago/<int:reserva_id>', methods=['GET', 'POST'])
def pago(reserva_id):
    # Verificar si el usuario tiene permisos
    if 'user_id' not in session or session.get('role') != 'cliente':
        flash("No tienes permisos para acceder a esta página", "danger")
        return redirect(url_for('app_routes.iniciar_sesion'))

    try:
        # Conexión a la base de datos
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Obtener el precio de la reserva
        cursor.execute("""
            SELECT v.precio
            FROM reservas r
            JOIN vueloandm v ON r.vuelo_id = v.vuelo_id
            WHERE r.reserva_id = %s
        """, (reserva_id,))
        reserva = cursor.fetchone()

        if not reserva:
            flash("Reserva no encontrada", "danger")
            return redirect(url_for('app_routes.cliente_dashboard'))

        precio = reserva['precio']

        if request.method == 'POST':
            # Procesar el pago
            metodo_pago = request.form.get('metodo_pago')
            ultimos_cuatro_digitos = request.form.get('ultimos_cuatro_digitos')

            if not metodo_pago:
                flash("Selecciona un método de pago", "danger")
                return render_template('pago.html', reserva_id=reserva_id, precio=precio)

            if metodo_pago in ['tarjeta_credito', 'tarjeta_debito'] and not ultimos_cuatro_digitos:
                flash("Los últimos cuatro dígitos de la tarjeta son obligatorios para este método de pago.", "danger")
                return render_template('pago.html', reserva_id=reserva_id, precio=precio)

            # Insertar pago en la base de datos
            cursor.execute("""
                INSERT INTO pagos (reserva_id, monto, metodo_pago, ultimos_cuatro_digitos, estado_pago, fecha_pago)
                VALUES (%s, %s, %s, %s, 'Pagado', NOW())
            """, (reserva_id, precio, metodo_pago, ultimos_cuatro_digitos))
            connection.commit()

            flash('Pago realizado exitosamente', 'success')
            return redirect(url_for('app_routes.confirmacion_pago', reserva_id=reserva_id))

        return render_template('pago.html', reserva_id=reserva_id, precio=precio)

    except Exception as e:
        flash(f"Error en el proceso de pago: {str(e)}", "danger")
        return redirect(url_for('app_routes.cliente_dashboard'))

    finally:
        # Asegurar el cierre de la conexión
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()


@app_routes.route('/confirmacion_pago/<int:reserva_id>')
def confirmacion_pago(reserva_id):
    if 'user_id' not in session or session.get('role') != 'cliente':
        flash("No tienes permisos para acceder a esta página", "danger")
        return redirect(url_for('app_routes.iniciar_sesion'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT r.reserva_id, u.nombre AS nombre_cliente, v.salida, v.llegada, 
               v.fecha_salida, v.hora_salida, v.fecha_llegada, v.hora_llegada, 
               v.modo_vuelo, v.precio, p.estado_pago
        FROM reservas r
        JOIN usuario u ON r.usuario_id = u.id
        JOIN vueloandm v ON r.vuelo_id = v.vuelo_id
        JOIN pagos p ON p.reserva_id = r.reserva_id
        WHERE r.reserva_id = %s
    """, (reserva_id,))
    
    ticket = cursor.fetchone()
    cursor.close()
    connection.close()
    
    if ticket is None:
        flash("Detalles del ticket no encontrados", "danger")
        return redirect(url_for('app_routes.cliente_dashboard'))

    return render_template('confirmacion_pago.html', ticket=ticket)
@app_routes.route('/ver_recomendaciones', methods=['GET'])
def ver_recomendaciones():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Obtener recomendaciones
    cursor.execute("SELECT recomendacion_id, titulo, descripcion, imagen_url FROM recomendaciones")
    recomendaciones = cursor.fetchall()

    cursor.close()
    connection.close()

    # Imprimir datos para depuración
    print(recomendaciones)

    return render_template('ver_recomendaciones.html', recomendaciones=recomendaciones)
@app_routes.route('/boleto', methods=['POST'])
def generar_boleto():
    vuelo_id = request.form.get('vuelo_id')
    if not vuelo_id:
        flash('ID del vuelo no proporcionado.', 'danger')
        return redirect(url_for('app_routes.cliente_dashboard'))

    ticket = obtener_ticket_por_vuelo_id(vuelo_id)
    if not ticket:
        flash('No se encontró información para este ID de vuelo.', 'danger')
        return redirect(url_for('app_routes.cliente_dashboard'))

    return render_template('boleto.html', ticket=ticket)


def obtener_ticket_por_vuelo_id(vuelo_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT t.ticket_id, t.nombre_cliente, t.vuelo_id, v.salida, v.llegada, 
                   v.fecha_salida, v.hora_salida, v.fecha_llegada, v.hora_llegada, v.precio
            FROM tickets t
            JOIN vueloandm v ON t.vuelo_id = v.vuelo_id
            WHERE t.vuelo_id = %s
        """, (vuelo_id,))

        ticket = cursor.fetchone()

        cursor.close()
        connection.close()

        return ticket
    except Exception as e:
        print(f"Error al obtener los datos del ticket: {str(e)}")
        return None
    
@app_routes.route('/mis_reservas', methods=['GET'])
def mis_reservas():
    # Verificar si el cliente está autenticado
    if 'user_id' not in session or session.get('role') != 'cliente':
        flash("Debes iniciar sesión para acceder a tus reservas.", "danger")
        return redirect(url_for('app_routes.iniciar_sesion'))

    cliente_id = session['user_id']

    try:
        # Conexión a la base de datos
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Obtener las reservas pagadas del cliente
        cursor.execute(
            """
            SELECT r.reserva_id, v.vuelo_id, v.salida, v.llegada, v.fecha_salida, 
                   v.hora_salida, v.fecha_llegada, v.hora_llegada, v.precio, p.estado_pago
            FROM reservas r
            JOIN vueloandm v ON r.vuelo_id = v.vuelo_id
            JOIN pagos p ON p.reserva_id = r.reserva_id
            WHERE r.usuario_id = %s AND p.estado_pago = 'Pagado'
            """,
            (cliente_id,)
        )

        reservas = cursor.fetchall()

        cursor.close()
        connection.close()

        # Renderizar las reservas
        return render_template('mis_reservas.html', reservas=reservas)

    except Exception as e:
        flash(f"Ocurrió un error al obtener tus reservas: {str(e)}", "danger")
        return render_template('mis_reservas.html', reservas=[])


@app_routes.route('/imprimir_boleto/<int:reserva_id>', methods=['GET'])
def imprimir_boleto(reserva_id):
    # Verificar si el cliente está autenticado
    if 'user_id' not in session or session.get('role') != 'cliente':
        flash("Debes iniciar sesión para imprimir tu boleto.", "danger")
        return redirect(url_for('app_routes.iniciar_sesion'))

    try:
        # Conexión a la base de datos
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Obtener los detalles de la reserva y vuelo
        cursor.execute(
            """
            SELECT r.reserva_id, u.nombre AS nombre_cliente, v.salida, v.llegada, 
                   v.fecha_salida, v.hora_salida, v.fecha_llegada, v.hora_llegada, 
                   v.precio, p.estado_pago
            FROM reservas r
            JOIN usuario u ON r.usuario_id = u.id
            JOIN vueloandm v ON r.vuelo_id = v.vuelo_id
            JOIN pagos p ON p.reserva_id = r.reserva_id
            WHERE r.reserva_id = %s AND p.estado_pago = 'Pagado'
            """,
            (reserva_id,)
        )

        ticket = cursor.fetchone()

        cursor.close()
        connection.close()

        if not ticket:
            flash("No se encontraron los detalles del boleto.", "danger")
            return redirect(url_for('app_routes.mis_reservas'))

        # Renderizar el boleto para imprimir
        return render_template('boleto_imprimir.html', ticket=ticket)

    except Exception as e:
        flash(f"Ocurrió un error al obtener los datos del boleto: {str(e)}", "danger")
        return redirect(url_for('app_routes.mis_reservas'))



@app_routes.route('/registro', methods=['GET', 'POST'])
def registro():
    form = RegistroForm()

    if form.validate_on_submit():
        nombre = form.nombre.data
        correo = form.correo.data
        username = form.username.data
        password = form.password.data
        role = form.role.data

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM usuario WHERE username = %s OR correo = %s", (username, correo))
        if cursor.fetchone():
            flash('El nombre de usuario o correo ya está en uso.', 'danger')
        else:
            cursor.execute("""
                INSERT INTO usuario (nombre, correo, username, password, role)
                VALUES (%s, %s, %s, %s, %s)
            """, (nombre, correo, username, password, role))
            connection.commit()
            flash('¡Registro exitoso! Puedes iniciar sesión ahora.', 'success')
            return redirect(url_for('app_routes.iniciar_sesion'))

        cursor.close()
        connection.close()

    return render_template('registro.html', form=form)

@app_routes.route('/cerrar_sesion')
def cerrar_sesion():
    session.clear()
    flash('¡Has cerrado sesión exitosamente!', 'success')
    return redirect(url_for('app_routes.iniciar_sesion'))
