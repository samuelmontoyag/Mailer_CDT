from flask_wtf import Form
import wtforms as wt
from wtforms.validators import DataRequired, EqualTo, ValidationError


class LoginForm(Form):
    usuario = wt.TextField("Usuario", validators=[DataRequired()])
    contrasena = wt.PasswordField("Contraseña", validators=[DataRequired()])
