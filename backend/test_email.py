import os
import sys
import django

# Garante que o backend está no path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

# Carrega o .env manualmente
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("=== Teste de E-mail ===")
print(f"Backend:  {settings.EMAIL_BACKEND}")
print(f"Host:     {settings.EMAIL_HOST}")
print(f"Port:     {settings.EMAIL_PORT}")
print(f"User:     {'✅ Configurado' if settings.EMAIL_HOST_USER else '❌ NÃO configurado'}")
print(f"Password: {'✅ Configurada' if settings.EMAIL_HOST_PASSWORD else '❌ NÃO configurada'}")
print(f"From:     {settings.DEFAULT_FROM_EMAIL}")
print()

try:
    send_mail(
        subject='Teste Glins Store - Brevo',
        message='Se você recebeu este e-mail, o Brevo está funcionando! 🚀',
        from_email=None,  # usa o DEFAULT_FROM_EMAIL
        recipient_list=['consulting.guilherme@gmail.com'],
        fail_silently=False,
    )
    print("✅ E-mail enviado com sucesso!")
except Exception as e:
    print(f"❌ Erro ao enviar: {e}")
