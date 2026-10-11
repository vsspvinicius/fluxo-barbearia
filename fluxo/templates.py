"""Texto do primeiro e-mail. Curto, pessoal, sem link e sem preço (ajuda a não cair no spam).
O único pedido é uma resposta "sim"; preço e detalhes vêm na conversa."""
from . import config

SUBJECT = "pergunta rápida sobre a {name}"

GOOGLE_LINE = "Vi que vocês têm {rating} estrelas e {count} avaliações no Google. Cliente satisfeito não falta por aí.\n\n"

BODY_TEXT = """Oi, pessoal da {name}, tudo bem?

{google_line}O que costuma escapar é outra coisa: a mensagem que chega às 22h pedindo horário e só é vista no dia seguinte. Até lá, o cliente já marcou em outro lugar. Junta isso com quem marca e não aparece, e no fim da semana são algumas cadeiras vazias.

Eu monto um atendimento automático que responde no WhatsApp e no Instagram a qualquer hora, já marca o horário e manda um lembrete antes do corte. A rotina da barbearia continua igual.

Faz sentido eu te mostrar como ficaria aí na {name}? Responde só com um "sim" que eu te explico em 2 minutos, por aqui mesmo.

{from_name}
Fluxo Barbearia · Campinas

Se não quiser receber outro e-mail, é só responder "remover".
"""


def _google_line(contact):
    rating, count = contact.get("rating"), contact.get("rating_count")
    try:
        rating, count = float(rating), int(count)
    except (TypeError, ValueError):
        return ""
    if rating < 4.0 or count < 5:
        return ""
    stars = f"{rating:.1f}".replace(".", ",")
    return GOOGLE_LINE.format(rating=stars, count=count)


def render(contact):
    body = BODY_TEXT.format(
        name=contact["name"],
        google_line=_google_line(contact),
        from_name=config.FROM_NAME,
    )
    return SUBJECT.format(name=contact["name"]), body
