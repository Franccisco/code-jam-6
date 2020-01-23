from flask_wtf import Form, RecaptchaField
from wtforms import PasswordField, StringField, validators


class RecaptchaForm(Form):
    """
    Used by password link and sending message.
    """
    recaptcha = RecaptchaField()


class SendMessageForm(Form):
    receiver = StringField("TO: ", [validators.DataRequired()])
    recaptcha = RecaptchaField()


class ViewMessageForm(Form):
    private_key = PasswordField("Your private key: ", [validators.DataRequired()])
