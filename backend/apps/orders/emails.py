from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_order_email(template_name, subject, order, extra_context=None, recipient=None):
    """Função genérica de disparo de e-mail."""
    context = {'order': order}
    if extra_context:
        context.update(extra_context)

    html_content = render_to_string(f'emails/{template_name}', context)
    to_email = recipient or order.user.email

    msg = EmailMultiAlternatives(
        subject=subject,
        body='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)


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
    # Notifica admin também
    send_order_email(
        'new_sale_admin.html',
        f'💰 Nova venda — Pedido #{order.id} — R$ {order.total_price}',
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
