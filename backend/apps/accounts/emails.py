import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger(__name__)


def send_welcome_email(user):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <body style="margin:0;padding:0;background:#0d0d0d;font-family:Arial,sans-serif">
      <div style="max-width:520px;margin:40px auto;background:#1a1a1a;
                  border:1px solid #c9a227;border-radius:12px;overflow:hidden">

        <div style="background:linear-gradient(135deg,#1a1a1a,#2a2a2a);
                    padding:40px 32px;text-align:center;
                    border-bottom:2px solid #c9a227">
          <div style="font-size:3rem;margin-bottom:8px">⚔️</div>
          <h1 style="color:#c9a227;font-size:1.6rem;margin:0;letter-spacing:2px">
            GLINS STORE
          </h1>
          <p style="color:#888;font-size:0.85rem;margin:6px 0 0;letter-spacing:1px">
            O SEU REINO DE PRODUTOS
          </p>
        </div>

        <div style="padding:36px 32px">
          <h2 style="color:#fff;font-size:1.3rem;margin:0 0 12px">
            Bem-vindo, {user.name}! 🎉
          </h2>
          <p style="color:#bbb;line-height:1.7;margin:0 0 24px">
            Sua conta foi criada com sucesso. Agora você faz parte do reino da
            <strong style="color:#c9a227">Glins Store</strong> e pode explorar
            todos os nossos produtos!
          </p>

          <div style="text-align:center;margin:32px 0">
            <a href="{settings.FRONTEND_URL}/pages/products.html"
               style="background:#c9a227;color:#0d0d0d;text-decoration:none;
                      padding:14px 32px;border-radius:8px;font-weight:700;
                      font-size:1rem;letter-spacing:1px;display:inline-block">
              ⚔️ EXPLORAR PRODUTOS
            </a>
          </div>

          <p style="color:#666;font-size:0.82rem;line-height:1.6;margin:0">
            Se você não criou esta conta, ignore este e-mail.
          </p>
        </div>

        <div style="background:#111;padding:20px 32px;text-align:center;
                    border-top:1px solid #333">
          <p style="color:#555;font-size:0.78rem;margin:0">
            © 2025 Glins Store · Todos os direitos reservados
          </p>
        </div>

      </div>
    </body>
    </html>
    """

    msg = EmailMultiAlternatives(
        subject='⚔️ Bem-vindo à Glins Store!',
        body=f'Olá {user.name}, sua conta foi criada com sucesso na Glins Store!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)  # ← lança exceção se falhar

    logger.info(f"[EMAIL] ✅ Boas-vindas enviado para {user.email}")
