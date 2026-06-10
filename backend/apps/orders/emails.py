# backend/apps/orders/emails.py
import resend
import logging
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)
resend.api_key = settings.RESEND_API_KEY


def send_order_email(template_name, subject, order, extra_context=None, recipient=None):
    """Função genérica — renderiza template e envia via Resend."""
    context = {'order': order, 'frontend_url': settings.FRONTEND_URL}
    if extra_context:
        context.update(extra_context)

    html_content = render_to_string(f'emails/{template_name}', context)
    to_email = recipient or order.user.email

    try:
        resend.Emails.send({
            "from":    settings.DEFAULT_FROM_EMAIL,
            "to":      [to_email],
            "subject": subject,
            "html":    html_content,
        })
        logger.info(f"[EMAIL] ✅ '{subject}' enviado para {to_email}")
    except Exception as e:
        logger.error(f"[EMAIL] ❌ Falha ao enviar '{subject}' para {to_email}: {e}")
        raise


def send_order_created_email(order):
    send_order_email(
        'order_created.html',
        f'⏳ Pedido #{order.id} criado — Aguardando pagamento',
        order,
    )

def send_payment_approved_email(order):
    send_order_email(
        'payment_approved.html',
        f'✅ Pagamento aprovado — Pedido #{order.id}',
        order,
    )
    send_order_email(
        'new_sale_admin.html',
        f'💰 Nova venda — Pedido #{order.id} — R$ {order.total}',
        order,
        recipient=settings.ADMIN_EMAIL,
    )

def send_order_preparing_email(order):
    send_order_email(
        'order_preparing.html',
        f'🔧 Pedido #{order.id} em preparação',
        order,
    )

def send_order_shipped_email(order):
    send_order_email(
        'order_shipped.html',
        f'🚚 Pedido #{order.id} enviado!',
        order,
    )

def send_order_delivered_email(order):
    send_order_email(
        'order_delivered.html',
        f'🎊 Pedido #{order.id} entregue!',
        order,
    )

def send_order_cancelled_email(order):
    send_order_email(
        'order_cancelled.html',
        f'❌ Pedido #{order.id} cancelado',
        order,
    )

def send_tracking_code_email(order):
    send_order_email(
        'order_shipped.html',
        f'🚚 Seu pedido #{order.id} foi enviado! Rastreie aqui',
        order,
    )
