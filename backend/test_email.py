import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.core.mail import send_mail

send_mail(
    subject="✅ Teste Glins Store - Brevo",
    message="E-mail de teste funcionando!",
    from_email="Glins Store <glins.store.cardgame@gmail.com>",
    recipient_list=["glins.store.cardgame@gmail.com"],
    html_message="<h2>✅ Funcionou!</h2><p>Brevo + Django rodando no Render.</p>",
)

print("E-mail enviado com sucesso!")
