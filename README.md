# Fluxo Barbearia — operação automatizada

Automação de prospecção, envio e relatório para a oferta de agendamento automático a barbearias de Campinas-SP.

## Estado atual

- Landing page: Lovable (ver `FLUXO_LANDING_URL`), leads guardados no banco da landing.
- Prospects: `data/campinas_barbearias_saloes.csv` (27 registros, Google Places). **Não há e-mail nesses dados.** O envio por e-mail só alcança quem tiver e-mail público, e precisa ser completado antes de escalar.
- Envio real: **desligado por padrão** (`FLUXO_DRY_RUN=1`). Ligue apenas com remetente próprio, Resend configurado e link de descadastro público.

## Rodar

```bash
python -m unittest discover -s tests -v
python -m fluxo.import_prospects data/campinas_barbearias_saloes.csv
python -m fluxo.send_emails          # dry-run por padrão
python -m fluxo.report
```

## Variáveis (sem chaves no código)

| Variável | Uso |
|---|---|
| `FLUXO_DRY_RUN` | `1` simula, `0` envia de verdade |
| `FLUXO_DAILY_LIMIT` | limite diário de e-mails (padrão 20) |
| `FLUXO_FROM_EMAIL`, `FLUXO_FROM_NAME` | remetente do negócio |
| `FLUXO_UNSUBSCRIBE_URL` | link público de descadastro |
| `FLUXO_COMPANY_ID`, `FLUXO_COMPANY_ADDRESS` | identificação exigida no rodapé |
| `RESEND_API_KEY` | envio (Resend) |
| `ANTHROPIC_API_KEY` | classificação de respostas (sem chave, usa regras simples) |

No GitHub, configure as chaves como *Secrets* e as demais como *Variables*. O workflow `daily.yml` roda às 09:00 de São Paulo, testa, envia (ou simula) e gera o relatório.

## Regras

- Nada de mensagem automática em massa no WhatsApp pessoal ou no WhatsApp Business sem a API oficial e aprovação da Meta.
- Todo e-mail tem identificação e descadastro. Descadastros são respeitados antes de qualquer envio.
- Dados de prospects são públicos de empresas, e o uso segue a LGPD. Pedidos de remoção são atendidos.
