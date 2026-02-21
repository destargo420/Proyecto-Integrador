from werkzeug.security import generate_password_hash, check_password_hash
from models.entities.User import User

class ModelUser:

    # -----------------------------
    # LOGIN DE USUARIO
    # -----------------------------
    @classmethod
    def login(cls, db, user):
        try:
            cursor = db.connection.cursor()
            sql = "SELECT Id, Username, Password, Fullname, Rol FROM user WHERE Username = %s"
            cursor.execute(sql, (user.Username,))
            data = cursor.fetchone()

            if data:
                valid_password = check_password_hash(data[2], user.Password)
                if valid_password:
                    # Password correcto → retornamos objeto User con datos
                    return User(data[0], data[1], True, data[3], data[4])
                else:
                    # Contraseña incorrecta
                    return User(data[0], data[1], False, data[3], data[4])
            else:
                # Usuario no existe
                return None
        except Exception as ex:
            raise Exception(ex)

    # -----------------------------
    # OBTENER USUARIO POR ID
    # -----------------------------
    @classmethod
    def get_by_id(cls, db, id):
        try:
            cursor = db.connection.cursor()
            sql = "SELECT Id, Username, Fullname, Rol FROM user WHERE Id = %s"
            cursor.execute(sql, (id,))
            data = cursor.fetchone()

            if data:
                return User(data[0], data[1], None, data[2], data[3])
            return None
        except Exception as ex:
            raise Exception(ex)

    # -----------------------------
    # REGISTRO DE USUARIOS
    # -----------------------------
    @classmethod
    def register(cls, db, user):
        try:
            cursor = db.connection.cursor()
            hashed_password = generate_password_hash(user.Password)

            sql = """INSERT INTO user (Username, Password, Fullname, Rol)
                     VALUES (%s, %s, %s, %s)"""
            cursor.execute(sql, (user.Username, hashed_password, user.Fullname, user.Rol))
            db.connection.commit()
            return True
        except Exception as ex:
            raise Exception(ex)
