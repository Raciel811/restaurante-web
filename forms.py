from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, IntegerField, TextAreaField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')

class MenuForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired()])
    description = TextAreaField('Descripción')
    price = FloatField('Precio', validators=[DataRequired()])
    category = SelectField('Categoría', choices=[('entrada', 'Entrada'), ('plato_fuerte', 'Plato Fuerte'), ('bebida', 'Bebida'), ('postre', 'Postre')])
    stock = IntegerField('Stock', validators=[DataRequired()])
    image = StringField('Imagen URL')
    submit = SubmitField('Guardar')

class OrderForm(FlaskForm):
    address = TextAreaField('Dirección de Domicilio (si aplica)')
    is_delivery = BooleanField('Solicitar Domicilio')
    submit = SubmitField('Confirmar Pedido')

class ExpenseForm(FlaskForm):
    description = TextAreaField('Descripción', validators=[DataRequired()])
    amount = FloatField('Monto', validators=[DataRequired()])
    submit = SubmitField('Registrar Gasto')