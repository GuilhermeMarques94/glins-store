import resend
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.RESEND_API_KEY


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

    try:
        resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [user.email],
            "subject": "⚔️ Bem-vindo à Glins Store!",
            "html": html_content,
        })
        logger.info(f"[EMAIL] ✅ Boas-vindas enviado para {user.email}")
    except Exception as e:
        logger.error(f"[EMAIL] ❌ Falha ao enviar boas-vindas para {user.email}: {e}")
        raise


# ── NOVO: E-mail de reset de senha ────────────────────────────────────────

def send_password_reset_email(user, uid, token):
    reset_link = f"{settings.FRONTEND_URL}/pages/reset-password.html?uid={uid}&token={token}"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <body style="margin:0;padding:0;background:#0d0d0d;font-family:Arial,sans-serif">
      <div style="max-width:520px;margin:40px auto;background:#1a1a1a;
                  border:1px solid #c9a227;border-radius:12px;overflow:hidden">

        <div style="background:linear-gradient(135deg,#1a1a1a,#2a2a2a);
                    padding:40px 32px;text-align:center;
                    border-bottom:2px solid #c9a227">
          <div style="font-size:3rem;margin-bottom:8px">🔑</div>
          <h1 style="color:#c9a227;font-size:1.6rem;margin:0;letter-spacing:2px">
            GLINS STORE
          </h1>
          <p style="color:#888;font-size:0.85rem;margin:6px 0 0;letter-spacing:1px">
            RECUPERAÇÃO DE SENHA
          </p>
        </div>

        <div style="padding:36px 32px">
          <h2 style="color:#fff;font-size:1.3rem;margin:0 0 12px">
            Olá, {user.name}! 👋
          </h2>
          <p style="color:#bbb;line-height:1.7;margin:0 0 24px">
            Recebemos uma solicitação para redefinir a senha da sua conta na
            <strong style="color:#c9a227">Glins Store</strong>.
            Clique no botão abaixo para criar uma nova senha:
          </p>

          <div style="text-align:center;margin:32px 0">
            <a href="{reset_link}"
               style="background:#c9a227;color:#0d0d0d;text-decoration:none;
                      padding:14px 32px;border-radius:8px;font-weight:700;
                      font-size:1rem;letter-spacing:1px;display:inline-block">
              🗡️ REDEFINIR SENHA
            </a>
          </div>

          <div style="background:#111;border:1px solid #333;border-radius:8px;
                      padding:16px 20px;margin-bottom:24px">
            <p style="color:#888;font-size:0.78rem;margin:0 0 8px;letter-spacing:0.05em">
              OU COPIE O LINK ABAIXO:
            </p>
            <p style="color:#c9a227;font-size:0.78rem;margin:0;word-break:break-all;line-height:1.6">
              {reset_link}
            </p>
          </div>

          <p style="color:#666;font-size:0.82rem;line-height:1.6;margin:0">
            ⏳ Este link é válido por <strong style="color:#888">24 horas</strong>.<br/>
            Se você não solicitou a redefinição, ignore este e-mail — sua senha permanece a mesma.
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

    try:
        resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to":   [user.email],
            "subject": "🔑 Redefinição de senha — Glins Store",
            "html": html_content,
        })
        logger.info(f"[EMAIL] ✅ Reset de senha enviado para {user.email}")
    except Exception as e:
        logger.error(f"[EMAIL] ❌ Falha ao enviar reset para {user.email}: {e}")
        raise
