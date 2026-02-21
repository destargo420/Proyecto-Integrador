# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[
        DataRequired(message="El nombre de usuario es obligatorio"),
        Length(min=4, max=40, message="El usuario debe tener entre 4 y 40 caracteres")
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message="La contraseña es obligatoria"),
        Length(min=6, max=50, message="Debe tener entre 6 y 50 caracteres")
    ])
    submit = SubmitField('Iniciar sesión')


class RegisterForm(FlaskForm):
    fullname = StringField('Nombre completo', validators=[
        DataRequired(message="El nombre completo es obligatorio"),
        Length(min=3, max=50, message="Debe tener entre 3 y 50 caracteres")
    ])
    username = StringField('Usuario', validators=[
        DataRequired(),
        Length(min=4, max=40)
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(),
        Length(min=6, max=50)
    ])
    confirm_password = PasswordField('Confirmar contraseña', validators=[
        DataRequired(),
        EqualTo('password', message="Las contraseñas deben coincidir")
    ])
    submit = SubmitField('Registrarse')
