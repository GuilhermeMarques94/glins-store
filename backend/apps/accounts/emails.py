from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_welcome_email(user):
    html_content = render_to_string('emails/welcome.html', {'user': user})

    msg = EmailMultiAlternatives(
        subject='🎉 Bem-vindo à Glins Store!',
        body='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)
