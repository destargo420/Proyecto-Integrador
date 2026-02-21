# Importaciones necesarias
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_mysqldb import MySQL
from functools import wraps
from io import BytesIO
from datetime import datetime
from markupsafe import escape
from werkzeug.security import generate_password_hash
# Configuración y modelos
from config import config
from models.ModelUser import ModelUser
from models.entities.User import User
from forms import LoginForm, RegisterForm
# aplicación Flask
app = Flask(__name__)
#herramienta para proteger aplicación web contra ataques de falsificación de solicitudes entre sitios (CSRF)
csrf = CSRFProtect()
#conexion db
db = MySQL(app)
#importacion para generar PDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from flask import make_response

# Ruta home
@app.route('/')
@app.route('/Home_')
def home():
    return render_template('pagina/home.html')

#ruta login manager
login_manager_app = LoginManager(app)
login_manager_app.login_view = 'login'
login_manager_app.login_message = None  
@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(db, id)

# eliminar retroceso
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, public, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

#constructor roles
def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.Rol not in roles:
                flash("Acceso Denegado.", "danger")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_view
    return wrapper


# Ruta Login
@app.route('/Login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User(0, username, password)
        logged_user = ModelUser.login(db, user)

        if logged_user is not None and logged_user.Password:
            login_user(logged_user)
            flash(f"Bienvenido {logged_user.Fullname}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Usuario o contraseña incorrectos.", "danger")
            return redirect(url_for('login'))

    return render_template('aplicacion/login.html', form=form)

# Ruta Usuarios
@app.route('/Usuarios')
@login_required
@role_required('Administrador')
def ver_usuarios():
    try:
        cursor = db.connection.cursor()
        cursor.execute("SELECT Id, Username, Fullname, Rol FROM user ORDER BY Id DESC;")
        usuarios = cursor.fetchall()
        cursor.close()
        return render_template('dashboard/usuarios.html', usuarios=usuarios)
    except Exception as ex:
        flash(f"Error al obtener usuarios: {str(ex)}", "danger")
        return redirect(url_for('dashboard'))

#Ruta Propietarios
@app.route('/Propietarios')
@login_required
@role_required('Administrador')
def ver_propietarios():
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT p.IdPropietario, p.NombreCompleto, p.Cedula, p.Telefono,
                   p.CorreoElectronico, p.FechaRegistro,
                   ST_AsText(p.Ubicacion) AS Coordenadas,
                   u.Username AS Usuario
            FROM Propietarios p
            JOIN user u ON p.IdUsuario = u.Id
            ORDER BY p.IdPropietario DESC;
        """)
        propietarios = cursor.fetchall()
        cursor.close()
        return render_template('dashboard/propietarios.html', propietarios=propietarios)
    except Exception as ex:
        flash(f"Error al obtener propietarios: {str(ex)}", "danger")
        return redirect(url_for('dashboard'))
    
#Generar Pdf
@app.route('/descargar_propietarios_pdf')
@login_required
@role_required('Administrador')
def descargar_propietarios_pdf():
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT p.IdPropietario, p.NombreCompleto, p.Cedula, p.Telefono,
                   p.CorreoElectronico, p.FechaRegistro
            FROM Propietarios p
            ORDER BY p.IdPropietario ASC
        """)
        propietarios = cursor.fetchall()
        cursor.close()

        # Crear PDF en memoria
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.setTitle("Listado de Propietarios")

        # Encabezado
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(200, 750, "Listado de Propietarios")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, 735, f"Total de registros: {len(propietarios)}")

        # Encabezados de tabla
        y = 710
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(50, y, "ID")
        pdf.drawString(90, y, "Nombre")
        pdf.drawString(250, y, "Cédula")
        pdf.drawString(330, y, "Teléfono")
        pdf.drawString(420, y, "Correo")
        y -= 15

        # Filas
        pdf.setFont("Helvetica", 9)
        for propietario in propietarios:
            if y < 50:  # Salto de página
                pdf.showPage()
                y = 750
            pdf.drawString(50, y, str(propietario[0]))
            pdf.drawString(90, y, propietario[1][:25])
            pdf.drawString(250, y, propietario[2])
            pdf.drawString(330, y, propietario[3])
            pdf.drawString(420, y, propietario[4][:25])
            y -= 15

        pdf.save()
        buffer.seek(0)

        # Enviar PDF al navegador
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=propietarios.pdf'
        return response

    except Exception as ex:
        flash(f"Error al generar PDF: {str(ex)}", "danger")
        return redirect(url_for('ver_propietarios'))
    

# rUTA DESCARGAR uSUARIOS pdf
@app.route('/descargar_usuarios_pdf')
@login_required
@role_required('Administrador')
def descargar_usuarios_pdf():
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT Id, Username, Fullname, Rol
            FROM user
            ORDER BY Id ASC
        """)
        usuarios = cursor.fetchall()
        cursor.close()

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.setTitle("Listado de Usuarios")

        # Encabezado
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(200, 750, "Listado de Usuarios")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, 735, f"Total de registros: {len(usuarios)}")

        # Cabeceras
        y = 710
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(50, y, "ID")
        pdf.drawString(90, y, "Usuario")
        pdf.drawString(250, y, "Nombre Completo")
        pdf.drawString(450, y, "Rol")
        y -= 15

        # Filas
        pdf.setFont("Helvetica", 9)
        for u in usuarios:
            if y < 50:
                pdf.showPage()
                y = 750
            pdf.drawString(50, y, str(u[0]))
            pdf.drawString(90, y, u[1][:20])
            pdf.drawString(250, y, u[2][:30])
            pdf.drawString(450, y, u[3])
            y -= 15

        pdf.save()
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=usuarios.pdf'
        return response

    except Exception as ex:
        flash(f"Error al generar PDF: {str(ex)}", "danger")
        return redirect(url_for('dashboard'))


# Ruta para descargar Viviendas en PDF
@app.route('/descargar_viviendas_pdf')
@login_required
@role_required('Administrador')
def descargar_viviendas_pdf():
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT v.IdVivienda, v.Direccion, v.TipoVivienda, v.AnioConstruccion,
                   v.DescripcionDanio, p.NombreCompleto
            FROM Viviendas v
            LEFT JOIN Propietarios p ON v.IdPropietario = p.IdPropietario
            ORDER BY v.IdVivienda ASC
        """)
        viviendas = cursor.fetchall()
        cursor.close()

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.setTitle("Listado de Viviendas")

        # Encabezado
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(200, 750, "Listado de Viviendas")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, 735, f"Total de registros: {len(viviendas)}")

        # Cabeceras
        y = 710
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(50, y, "ID")
        pdf.drawString(90, y, "Dirección")
        pdf.drawString(250, y, "Tipo")
        pdf.drawString(350, y, "Año")
        pdf.drawString(400, y, "Daño")
        pdf.drawString(520, y, "Propietario")
        y -= 15

        # Filas
        pdf.setFont("Helvetica", 9)
        for v in viviendas:
            if y < 50:
                pdf.showPage()
                y = 750
            pdf.drawString(50, y, str(v[0]))
            pdf.drawString(90, y, v[1][:25])
            pdf.drawString(250, y, v[2])
            pdf.drawString(350, y, str(v[3]))
            pdf.drawString(400, y, v[4][:20])
            pdf.drawString(520, y, v[5][:20] if v[5] else "Sin propietario")
            y -= 15

        pdf.save()
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=viviendas.pdf'
        return response

    except Exception as ex:
        flash(f"Error al generar PDF: {str(ex)}", "danger")
        return redirect(url_for('dashboard'))

    
#Ruta Logout
@app.route('/logout')
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for('home'))

# Ruta Register 
@app.route('/Register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        fullname = escape(form.fullname.data.strip())
        username = escape(form.username.data.strip())
        password = form.password.data
        cedula = escape(request.form['cedula'].strip())
        telefono = escape(request.form['telefono'].strip())
        correo = escape(request.form['correo'].strip())
        ubicacion_texto = escape(request.form.get('ubicacion', '').strip())

        # Validar que cédula y teléfono sean numéricos
        if not cedula.isdigit() or not telefono.isdigit():
            flash("Los campos Cédula y Teléfono deben contener solo números.", "danger")
            return redirect(url_for('register'))

        # Validar formato de coordenadas si el campo no está vacío
        lat, lon = None, None
        if ubicacion_texto:
            try:
                lat, lon = map(float, ubicacion_texto.replace(" ", "").split(","))
            except ValueError:
                flash("Formato de ubicación incorrecto. Use 'latitud,longitud'.", "danger")
                return redirect(url_for('register'))

        # Determinar rol automáticamente
        rol = 'Administrador' if username.lower() == 'destargo' else 'Propietario'

        new_user = User(0, username, password, fullname, rol)

        try:
            cursor = db.connection.cursor()
            hashed_password = generate_password_hash(new_user.Password)
            sql_user = """INSERT INTO user (Username, Password, Fullname, Rol)
                          VALUES (%s, %s, %s, %s)"""
            cursor.execute(sql_user, (new_user.Username, hashed_password, new_user.Fullname, new_user.Rol))
            db.connection.commit()
            new_user_id = cursor.lastrowid

            # Insertar en Propietarios solo si el rol es Propietario
            if rol == 'Propietario':
                if lat is not None and lon is not None:
                    sql_prop = """INSERT INTO Propietarios (IdUsuario, NombreCompleto, Cedula, Telefono,
                                  CorreoElectronico, FechaRegistro, Ubicacion)
                                  VALUES (%s, %s, %s, %s, %s, %s, ST_GeomFromText(%s))"""
                    point = f'POINT({lat} {lon})'
                    cursor.execute(sql_prop, (new_user_id, fullname, cedula, telefono, correo, datetime.now(), point))
                else:
                    #Si el propietario no digita ubicacion se guarda un valor por defecto (0,0)
                    sql_prop = """INSERT INTO Propietarios (IdUsuario, NombreCompleto, Cedula, Telefono,
                                  CorreoElectronico, FechaRegistro, Ubicacion)
                                  VALUES (%s, %s, %s, %s, %s, %s, ST_GeomFromText('POINT(0 0)'))"""
                    cursor.execute(sql_prop, (new_user_id, fullname, cedula, telefono, correo, datetime.now()))

                db.connection.commit()

            flash("Registro completado.", "success")
            return redirect(url_for('login'))

        except Exception as ex:
            db.connection.rollback()
            flash(f"Error al registrar usuario: {str(ex)}", "danger")
            return redirect(url_for('register'))

    return render_template('aplicacion/register.html', form=form)


# Ruta DashBoard
@app.route('/DashBoard')
@login_required
def dashboard():
    return render_template('dashboard/dashboard.html')


# Ruta por rol
@app.route('/Admin')
@login_required
@role_required('Administrador')
def admin_panel():
    return render_template('roles/admin.html')

# Ruta Propietario
@app.route('/Propietario', methods=['GET', 'POST'])
@login_required
@role_required('Propietario', 'Administrador')
def propietario_panel():
    cursor = db.connection.cursor()
    imagen = None  

    #  usuario ADMINISTRADOR TODAS las viviendas
    if current_user.Rol == 'Administrador':
        try:
            cursor.execute("""
                SELECT v.IdVivienda, v.Direccion, v.TipoVivienda, v.AnioConstruccion,
                       v.DescripcionDanio,
                       COALESCE(p.NombreCompleto, 'Sin propietario') AS Propietario,
                       COALESCE(u.Username, 'Desconocido') AS Usuario
                FROM Viviendas v
                LEFT JOIN Propietarios p ON v.IdPropietario = p.IdPropietario
                LEFT JOIN user u ON p.IdUsuario = u.Id
                ORDER BY v.IdVivienda DESC;
            """)
            viviendas = cursor.fetchall()
            cursor.close()
            return render_template('roles/propietario.html', viviendas=viviendas, admin_view=True)
        except Exception as ex:
            cursor.close()
            flash(f"Error al obtener viviendas: {str(ex)}", "danger")
            return redirect(url_for('dashboard'))

    # usuario PROPIETARIO ver y registrar solo las suyas
    if request.method == 'POST':
        direccion = request.form.get('direccion', '').strip()
        tipo = request.form.get('tipo', '').strip()
        anio = request.form.get('anio', '').strip()
        danio = request.form.get('danio', '').strip()
        imagen = request.files.get('imagen')

    
        if not imagen:
            flash(" Debe seleccionar una imagen válida.", "danger")
            return redirect(url_for('propietario_panel'))

      
        mime_type = imagen.mimetype
        tipos_permitidos = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp']
        if mime_type not in tipos_permitidos:
            flash("Solo se permiten archivos de imagen (JPG, JPEG, PNG o WEBP).", "danger")
            return redirect(url_for('propietario_panel'))

        try:
            imagen_bytes = imagen.read()
            cursor.execute("SELECT IdPropietario FROM Propietarios WHERE IdUsuario = %s", (current_user.Id,))
            data = cursor.fetchone()

            if not data:
                flash("No se encontró un propietario vinculado a este usuario.", "danger")
                return redirect(url_for('propietario_panel'))

            id_prop = data[0]
            sql = """INSERT INTO Viviendas (Direccion, TipoVivienda, AnioConstruccion,
                     ImagenEstadoActual, DescripcionDanio, IdPropietario)
                     VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (direccion, tipo, int(anio), imagen_bytes, danio, id_prop))
            db.connection.commit()
            flash("Vivienda registrada correctamente.", "success")

        except Exception as ex:
            db.connection.rollback()
            flash(f"Error al registrar vivienda: {str(ex)}", "danger")

    # Mostrar viviendas del propietario
    try:
        cursor.execute("""
            SELECT v.IdVivienda, v.Direccion, v.TipoVivienda, v.AnioConstruccion,
                   v.DescripcionDanio, p.NombreCompleto
            FROM Viviendas v
            JOIN Propietarios p ON v.IdPropietario = p.IdPropietario
            WHERE p.IdUsuario = %s
            ORDER BY v.IdVivienda DESC;
        """, (current_user.Id,))
        viviendas = cursor.fetchall()
        cursor.close()
        return render_template('roles/propietario.html', viviendas=viviendas, admin_view=False)
    except Exception as ex:
        cursor.close()
        flash(f"Error al obtener las viviendas: {str(ex)}", "danger")
        return redirect(url_for('dashboard'))




# Errores 

def status_401(error):
    return redirect(url_for('home'))

def status_404(error):
    return "<h1>Página no encontrada</h1>", 404

# Ejecutar main
if __name__ == '__main__':
    app.config.from_object(config['development'])
    csrf.init_app(app)
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run(debug=True)
