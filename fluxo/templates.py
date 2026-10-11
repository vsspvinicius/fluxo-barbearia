"""Textos de e-mail. Sem nome de pessoa, sem promessa de resultado."""
from . import config

SUBJECT = "Agendamento automático para {name}"

BODY_TEXT = """Olá, equipe da {name}.

Vi a barbearia no Google e quis apresentar uma solução simples: uma automação que responde clientes no WhatsApp e Instagram fora do horário, agenda o horário, envia lembrete antes do atendimento e reduz faltas sem aviso.

Implantação em até 7 dias. Para as três primeiras barbearias de Campinas, o valor de implantação é R$ 500 (regular R$ 700), com mensalidade de R$ 250.

Mais detalhes e formulário: {landing}

Se não quiser mais receber estes e-mails, responda com "remover" ou use o link abaixo.

{unsubscribe}

{from_name}
{address}
Identificação: {company_id}
"""


def render(contact):
    unsub = config.UNSUBSCRIBE_URL or "Para descadastrar, responda este e-mail com a palavra REMOVER."
    body = BODY_TEXT.format(
        name=contact["name"],
        landing=config.LANDING_URL,
        unsubscribe=unsub,
        from_name=config.FROM_NAME,
        address=config.COMPANY_ADDRESS,
        company_id=config.COMPANY_ID,
    )
    return SUBJECT.format(name=contact["name"]), body
