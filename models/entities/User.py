from werkzeug.security import check_password_hash
from flask_login import UserMixin


class User:
    def __init__(self, Id, Username, Password, Fullname=None, Rol=None):
        self.Id = Id
        self.Username = Username
        self.Password = Password
        self.Fullname = Fullname
        self.Rol = Rol

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.Id)

        
    @classmethod    
    def check_password(self,hashed_password,password):    
        return check_password_hash(hashed_password,password)
    
