"""Configuração lida de variáveis de ambiente. Nenhuma chave fica no código."""
import os

DB_PATH = os.environ.get("FLUXO_DB", "fluxo.db")
DAILY_EMAIL_LIMIT = int(os.environ.get("FLUXO_DAILY_LIMIT", "20"))
DRY_RUN = os.environ.get("FLUXO_DRY_RUN", "1") == "1"  # padrão: não envia nada

FROM_EMAIL = os.environ.get("FLUXO_FROM_EMAIL", "")  # e-mail novo do negócio
FROM_NAME = os.environ.get("FLUXO_FROM_NAME", "Fluxo Barbearia (provisório)")
COMPANY_ADDRESS = os.environ.get("FLUXO_COMPANY_ADDRESS", "[endereço a definir]")
COMPANY_ID = os.environ.get("FLUXO_COMPANY_ID", "[CNPJ/MEI a definir]")
UNSUBSCRIBE_URL = os.environ.get("FLUXO_UNSUBSCRIBE_URL", "")  # URL pública de descadastro
LANDING_URL = os.environ.get(
    "FLUXO_LANDING_URL",
    "https://id-preview--b999a47c-126d-4762-bb83-4ff087819ee4.lovable.app",
)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("FLUXO_MODEL", "claude-haiku-5-5")
