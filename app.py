from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from functools import wraps

app = Flask(__name__)

# Configuración de la base de datos
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'proyecto_pa'
mysql = MySQL(app)

# Configuración de la aplicación
app.secret_key = 'mysecretkey'

# Decorador para verificar inicio de sesión
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Debe iniciar sesión primero.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para verificar roles
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("rol") != "administrador":
            flash("Acceso denegado. Se requiere rol de administrador.")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

# Rutas de autenticación
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"]
        contraseña = request.form["contraseña"]

        cur = mysql.connection.cursor()
        cur.execute("SELECT id_usuario, rol FROM usuarios WHERE correo = %s AND contraseña = %s", 
                    (correo, contraseña))
        usuario = cur.fetchone()
        
        if usuario:
            session["usuario_id"] = usuario[0]
            session["rol"] = usuario[1]
            flash("Inicio de sesión exitoso")
            return redirect(url_for("index"))
        else:
            flash("Correo o contraseña incorrectos")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.")
    return redirect(url_for("login"))

# Ruta principal: Vista general
@app.route("/")
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT i.id_inscripcion, c.nombre AS curso, e.nombre AS estudiante
        FROM inscripciones i
        JOIN cursos c ON i.id_curso = c.id_curso
        JOIN estudiantes e ON i.id_estudiante = e.id_estudiante
    """)
    data = cur.fetchall()
    return render_template("index.html", inscripciones=data)

# Ruta para el panel de administrador
@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    return render_template("admin_dashboard.html")

# CRUD de Usuarios
@app.route("/usuarios")
@login_required
@admin_required
def ver_usuarios():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM usuarios")
    usuarios = cur.fetchall()
    return render_template("usuarios.html", usuarios=usuarios)

@app.route("/add_usuario", methods=["POST"])
@login_required
@admin_required
def add_usuario():
    nombre_usuario = request.form.get("nombre_usuario")
    correo = request.form.get("correo")
    contraseña = request.form.get("contraseña")
    rol = request.form.get("rol")

    if not all([nombre_usuario, correo, contraseña, rol]):
        flash("Todos los campos son obligatorios.")
        return redirect(url_for("ver_usuarios"))

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO usuarios (nombre_usuario, correo, contraseña, rol)
        VALUES (%s, %s, %s, %s)
    """, (nombre_usuario, correo, contraseña, rol))
    mysql.connection.commit()
    flash("Usuario agregado exitosamente")
    return redirect(url_for("ver_usuarios"))

@app.route("/edit_usuario/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_usuario(id):
    cur = mysql.connection.cursor()
    if request.method == "POST":
        nombre_usuario = request.form.get("nombre_usuario")
        correo = request.form.get("correo")
        rol = request.form.get("rol")

        if not all([nombre_usuario, correo, rol]):
            flash("Todos los campos son obligatorios.")
            return redirect(url_for("edit_usuario", id=id))

        cur.execute("""
            UPDATE usuarios
            SET nombre_usuario = %s, correo = %s, rol = %s
            WHERE id_usuario = %s
        """, (nombre_usuario, correo, rol, id))
        mysql.connection.commit()
        flash("Usuario actualizado correctamente")
        return redirect(url_for("ver_usuarios"))
    else:
        cur.execute("SELECT * FROM usuarios WHERE id_usuario = %s", (id,))
        usuario = cur.fetchone()
        return render_template("edit_usuario.html", usuario=usuario)

@app.route("/delete_usuario/<int:id>")
@login_required
@admin_required
def delete_usuario(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id,))
    mysql.connection.commit()
    flash("Usuario eliminado correctamente")
    return redirect(url_for("ver_usuarios"))

# Más rutas aquí (CRUD de Cursos, Estudiantes, Inscripciones y Calificaciones)

# Agregar un nuevo curso
@app.route("/add_curso", methods=["POST"])
@login_required
def add_curso():
    if request.method == 'POST':
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        id_profesor = request.form["id_profesor"]
        if not all([nombre, descripcion, id_profesor]):
            flash("Todos los campos son obligatorios.")
            return redirect(url_for("index"))
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Cursos (nombre, descripcion, id_profesor) VALUES (%s, %s, %s)", 
                    (nombre, descripcion, id_profesor))
        mysql.connection.commit()
        flash("Curso agregado satisfactoriamente")
        return redirect(url_for('index'))

# Agregar un nuevo estudiante
@app.route("/add_estudiante", methods=["POST"])
@login_required
def add_estudiante():
    if request.method == 'POST':
        nombre = request.form["nombre"]
        matricula = request.form["matricula"]
        carrera = request.form["carrera"]
        if not all([nombre, matricula, carrera]):
            flash("Todos los campos son obligatorios.")
            return redirect(url_for("index"))
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Estudiantes (nombre, matricula, carrera) VALUES (%s, %s, %s)", 
                    (nombre, matricula, carrera))
        mysql.connection.commit()
        flash("Estudiante agregado satisfactoriamente")
        return redirect(url_for('index'))

# Inscribir un estudiante en un curso
@app.route("/inscribir", methods=["POST"])
@login_required
def inscribir():
    if request.method == 'POST':
        id_estudiante = request.form["id_estudiante"]
        id_curso = request.form["id_curso"]
        if not all([id_estudiante, id_curso]):
            flash("Todos los campos son obligatorios.")
            return redirect(url_for("index"))
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Inscripciones (id_estudiante, id_curso, fecha_inscripcion) VALUES (%s, %s, NOW())", 
                    (id_estudiante, id_curso))
        mysql.connection.commit()
        flash("Estudiante inscrito satisfactoriamente")
        return redirect(url_for('index'))

# Eliminar una inscripción
@app.route("/delete_inscripcion/<int:id>")
@login_required
def delete_inscripcion(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM Inscripciones WHERE id_inscripcion = %s", (id,))
    mysql.connection.commit()
    flash("Inscripción eliminada satisfactoriamente")
    return redirect(url_for('index'))

# Agregar una calificación a un estudiante en un curso
@app.route("/add_calificacion", methods=["POST"])
@login_required
def add_calificacion():
    if request.method == 'POST':
        id_inscripcion = request.form["id_inscripcion"]
        nota = request.form["nota"]
        comentarios = request.form["comentarios"]
        if not id_inscripcion or nota is None:
            flash("La inscripción y la nota son obligatorias.")
            return redirect(url_for("index"))
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Calificaciones (id_inscripcion, nota, comentarios) VALUES (%s, %s, %s)", 
                    (id_inscripcion, nota, comentarios))
        mysql.connection.commit()
        flash("Calificación agregada satisfactoriamente")
        return redirect(url_for('index'))

# Ver las calificaciones de un estudiante en un curso
@app.route("/ver_calificaciones")
@login_required
def ver_calificaciones():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT e.nombre AS estudiante, c.nombre AS curso, cal.nota, cal.comentarios
        FROM Calificaciones cal
        JOIN Inscripciones i ON cal.id_inscripcion = i.id_inscripcion
        JOIN Estudiantes e ON i.id_estudiante = e.id_estudiante
        JOIN Cursos c ON i.id_curso = c.id_curso
    """)
    calificaciones = cur.fetchall()
    return render_template("ver_calificaciones.html", calificaciones=calificaciones)

# Eliminar una calificación
@app.route("/delete_calificacion/<int:id>")
@login_required
def delete_calificacion(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM Calificaciones WHERE id_calificacion = %s", (id,))
    mysql.connection.commit()
    flash("Calificación eliminada satisfactoriamente")
    return redirect(url_for('ver_calificaciones'))

# Ruta para editar un curso
@app.route("/edit_curso/<int:id>", methods=["GET", "POST"])
@login_required
def edit_curso(id):
    cur = mysql.connection.cursor()
    if request.method == "POST":
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        id_profesor = request.form["id_profesor"]
        if not all([nombre, descripcion, id_profesor]):
            flash("Todos los campos son obligatorios.")
            return redirect(url_for("edit_curso", id=id))
        cur.execute("""
            UPDATE Cursos
            SET nombre = %s, descripcion = %s, id_profesor = %s
            WHERE id_curso = %s
        """, (nombre, descripcion, id_profesor, id))
        mysql.connection.commit()
        flash("Curso actualizado satisfactoriamente")
        return redirect(url_for('index'))
    else:
        cur.execute("SELECT * FROM Cursos WHERE id_curso = %s", (id,))
        curso = cur.fetchone()
        return render_template("edit_curso.html", curso=curso)

if __name__ == "__main__":
    app.run(port=3000, debug=True)