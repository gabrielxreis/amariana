# Mariana: secretária de IA para audiovisual

A Mariana encontra clientes para profissionais de audiovisual (filmmakers, editores, produtoras), escreve as mensagens, cuida das respostas e leva cada conversa até uma call, um briefing ou um orçamento. Ela é um fork do Harvey (github.com/ethanplusai/harvey) e roda na assinatura do Claude Code, sem custo de API.

**Você (Claude) é o guia.** Fale em português do Brasil, uma coisa de cada vez, sem jargão. Nunca use travessão (em dash) em nada que escrever para o usuário ou em mensagens da Mariana.

---

## Quando alguém abre o projeto pela primeira vez

Cheque em silêncio:
1. `.venv/` existe e `mariana --help` roda? Senão: instalar (passo 1).
2. `data/onboarding.json` e `harvey.local.yaml` existem? Senão: onboarding (passo 2). **É sempre o primeiro passo depois de instalar.**
3. Email de envio configurado e testado? (`mariana email-check`)
4. Assinatura gerada? (`data/signature.html`)
5. `data/harvey.db` existe? Senão, a Mariana ainda não rodou.

Depois se apresente de acordo:
> "Oi! Eu vou te ajudar a configurar a Mariana, sua secretária que fecha trabalhos de vídeo. Primeiro ela precisa te conhecer bem: quanto mais souber de você, melhores ficam as mensagens."

---

## Fluxo de configuração

### Passo 1: instalar
```bash
python3.12 -m venv .venv && source .venv/bin/activate && pip install -e .
```
(Python 3.11+. No macOS o `python3` do sistema é 3.9; use `brew install python@3.12`.)

### Passo 2: onboarding (OBRIGATÓRIO no primeiro uso)
Objetivo: saber o máximo possível sobre a pessoa ou a empresa. Tudo o que a Mariana escreve, quem ela procura e o preço que ela cita vêm daqui.

1. Peça material: "Você tem algum arquivo falando de você ou da empresa? Pode ser um .md, .txt ou PDF: bio, tabela de preços, portfólio, apresentação. Se não tiver, tudo bem." Se a pessoa colar texto no chat, salve em `data/sobre.md`.
2. Peça links: site, portfólio/showreel, Instagram, LinkedIn.
3. Rode a análise e veja o que falta:
   ```bash
   mariana onboard --file data/sobre.md --site <site> --yes
   ```
   O comando lista as perguntas sem resposta.
4. Faça essas perguntas **no chat**, poucas por vez, e salve as respostas em `data/respostas.json` (`{"chave": "resposta"}`). Garanta pelo menos: nome, marca, como se apresenta, email de envio, WhatsApp, portfólio, serviços e preços de partida, clientes que podem ser citados, tipo de cliente desejado, cidades/países, quem NÃO atender, tom de voz e a oferta de entrada.
5. Rode de novo com as respostas:
   ```bash
   mariana onboard --file data/sobre.md --site <site> --answers data/respostas.json --yes
   ```
6. Mostre o resumo de `skills/product_knowledge.md` e pergunte se está certo. Corrija com novas respostas e rode de novo. (No terminal, `mariana onboard` sem flags faz a entrevista sozinho.)

Gera: `harvey.local.yaml` (config, fora do git), `skills/product_knowledge.md` (dossiê que todo agente lê), `data/onboarding.json` e a assinatura.

### Passo 3: assinatura de email
```bash
mariana signature                 # gera texto + HTML e abre a prévia
mariana signature --install-gmail # define como assinatura do Gmail conectado
```
A assinatura entra automaticamente em todo email enviado (depois do filtro de spam, então os links dela não contam contra o limite de links do email frio). Campos em `persona.signature` no `harvey.local.yaml`.

### Passo 4: email de envio
Recomende Gmail/Google Workspace num domínio próprio (para volume, um domínio secundário só de prospecção).
1. Google Cloud Console: criar projeto, ativar a Gmail API, criar credencial OAuth "Desktop app". Colocar `GMAIL_CLIENT_ID` e `GMAIL_CLIENT_SECRET` no `.env`.
2. `channels.email.provider: gmail` no `harvey.local.yaml`.
3. `mariana gmail auth` (abre o navegador; pede permissão de enviar, ler e ajustar a assinatura).
4. `mariana email-check --send-test`: confere MX, SPF, DKIM e DMARC do domínio, testa a conexão e manda um teste para o próprio email. Ajude a corrigir cada item marcado com ✗ (os registros sugeridos aparecem na saída).
Outras opções: Microsoft 365 (`docs/microsoft365.md`) ou SMTP/IMAP.

### Passo 5: WhatsApp, LinkedIn e Instagram
Regra de canal por mercado (automática, `harvey/market.py`):
- **Brasil**: email + WhatsApp, em português.
- **EUA e resto do mundo**: email + LinkedIn (Instagram se a empresa tiver), em inglês.

Tudo cai na aba **Mensagens** do painel. A Mariana escreve; a pessoa aprova, clica em "Abrir no WhatsApp" (abre o WhatsApp dela com o texto pronto) ou "Copiar e abrir perfil" (LinkedIn/Instagram) e envia da própria conta. Nenhuma conta é automatizada, então não há risco de ban.
- `mariana whatsapp-check` confere a configuração.
- Modo `cloud_api` (opcional, `channels.whatsapp.mode`): envio automático pela API oficial da Meta, **só** para contatos marcados como opt-in (quem respondeu ou pediu contato). Precisa de `WHATSAPP_TOKEN` e `WHATSAPP_PHONE_NUMBER_ID` no `.env` (Meta for Developers > WhatsApp > API Setup). Nunca ofereça automação não oficial do WhatsApp Web.
- O login automatizado no LinkedIn do Harvey fica desligado (`automate_login: false`): ele viola os termos do LinkedIn.

### Passo 5b: agenda, avisos e números
- **Agenda real:** ative a Google Calendar API no mesmo projeto do Gmail e rode `mariana gmail auth` de novo. `mariana agenda-check` mostra os próximos horários livres. Nas respostas a interessados, a Mariana oferece esses horários exatos (ou o link de `product.offer.booking_url`, se `booking_method: calendar_link`). Ajustes em `calendar:` no config (horário de trabalho, dias, duração).
- **Aviso no celular:** instale o app ntfy, assine um tópico difícil de adivinhar e coloque em `NTFY_TOPIC` no `.env` (ou use bot do Telegram). `mariana aviso-teste` testa. No Mac também aparece notificação.
- **Números:** aba Números do painel (taxa de resposta por mercado, canal e segmento).

### Passo 6: sinais e descoberta
```bash
mariana signals --confirm free   # inclui NO_VIDEO_ON_SITE, INSTAGRAM_PROFILE, LINKEDIN_COMPANY...
mariana discover --estimate      # quanto custa antes de gastar
mariana discover                 # OpenStreetMap, grátis
```
Termos que o OpenStreetMap entende: igreja/church, evento/event, casamento/wedding, academia/gym, imobiliária/real estate, restaurante, hotel, clínica, escola, agência, teatro, esporte, boate.

Radar de eventos (precisa de `SERPER_API_KEY`):
```bash
mariana eventos --estimate   # custo antes de gastar
mariana eventos              # organizadores com evento nos próximos 3 meses
```

### Passo 7: rodar
```bash
mariana dashboard   # http://localhost:5555 (Outbox = emails, Mensagens = WhatsApp/LinkedIn/Instagram)
mariana run         # ciclo a cada 15 min; nada sai sem aprovação
```

---

## Do interesse ao job
- **Resposta fora do email:** na aba Mensagens, nas enviadas, botão "Respondeu": cole o que a pessoa escreveu. Os emails pendentes são cancelados, a conversa abre e a Mariana rascunha a resposta no mesmo canal. Com a Cloud API e webhook, isso é automático para o WhatsApp.
- **Portfólio certo:** o onboarding guarda cada trabalho com o segmento; respostas e propostas usam o do mesmo segmento do cliente.
- **Proposta:** em Conversas, "Gerar proposta" (ou `mariana proposta --email x@y.com`): lê o briefing da conversa e gera o PDF em `data/propostas/` com serviços e preços do dossiê. Para um layout na identidade visual, passe o HTML para o Yoshi (/oyoshi).
- **Fechou:** botão "Fechou" na conversa cria o job (aba Jobs). Marque "Entreguei" e a data do próximo evento: a Mariana pede depoimento e indicação (3 dias depois) e volta a oferecer 45 dias antes do evento. Tudo como rascunho para aprovar.
- **Amostras:** `mariana amostras` escolhe os 5 leads mais quentes com YouTube/Instagram e gera o briefing em `data/amostras/` para o Gab (/ogab) cortar 15 s. Com o vídeo pronto: `mariana amostra-pronta --prospect ID --link URL`. A amostra vai só para o próprio lead, nunca é publicada.

---

## Regras que nunca mudam
- Nada é enviado sem aprovação (email: Outbox; outros canais: Mensagens).
- Opt-out em qualquer canal vale para todos, para sempre.
- A Mariana só cita clientes, trabalhos e preços que estão no dossiê.
- Respostas sempre no idioma em que o contato escreveu.
- Nunca usar travessão em mensagens.

---

## Referência técnica (herdada do Harvey)

O pacote Python interno continua se chamando `harvey` para não quebrar o código herdado; o comando `harvey` é sinônimo de `mariana`.

### Architecture
- **Heartbeat loop** (`main.py`): Every cycle → check quiet hours → check budget → decide → act → log → sleep
- **Brain** (`brain.py`): Wraps `claude -p --output-format json --dangerously-skip-permissions` for headless Claude calls; records exact per-call token usage into `usage_events`
- **State** (`state.py`): SQLite at `data/harvey.db` with tables for companies, prospects, campaigns, conversations, actions, usage
- **Usage tracking** (`usage.py`, `integrations/quota.py`): per-call attribution (agent/task/model/tokens) for Harvey's OWN Claude calls only — it never scans your other Claude Code sessions — plus a live subscription-quota gauge read the same way Claude Code's `/usage` does. The budget check throttles Harvey against real quota utilization so it always leaves headroom for your own interactive Claude use (`usage.max_daily_claude_percent`). Dashboard has a Usage tab; CLI has `harvey usage`.
- **Skills** (`skills/`): Markdown knowledge files injected into agent prompts
- **Signals** (`signals.py`, `state.py`): every fact Harvey learns is an OBSERVATION — a row in `observations`, never a column. A new signal needs no migration, re-observing over time is a free time series, and confidence + provenance travel with the fact. The vocabulary in `signal_codes` is governed (a trigger rejects any code not in it) and gated: only `status = 'confirmed'` signals are collected, and only a human sets that. `state.cohort(require, exclude)` does the set intersection in SQL.
- **Dashboard** (`dashboard.py` + `harvey/web/`): FastAPI JSON API plus plain HTML/CSS/JS served from disk — no build step. Edit `harvey/web/app.css` or `app.js` and reload the page.
- **DISCOVER** (`collectors/discover.py`): the only stage that spends money, so cost discipline lives in the collector, not the database — every run estimates first, checks a spend cap between batches, reads a kill switch, and flushes observations per batch. Providers are adapters behind one interface (`DiscoveryProvider`); adding one is a small class. Junk filtering matches *patterns*, not a literal blocklist. Entity resolution is the normalised domain, falling back to the provider's `external_id` for businesses with no website.

### Sub-Agents
- **Scout**: Python does all web searching (DuckDuckGo → Bing → Google → Serper API) and email resolution (pattern-first: cache → scraped mailto → Hunter domain search → default, then verify one candidate via Reoon/ZeroBounce/Hunter/SMTP; catch-alls flagged `risky`). Claude only scores/personalizes found data. Scout also collects **buying signals**: tech stack detected on each company's site (HubSpot, Shopify, Intercom, ~35 tools — zero extra requests) and hiring signals from careers pages. With `pip install python-jobspy` (optional), a job-board strategy discovers companies actively hiring for roles in `icp.hiring_signals` (falls back to `icp.titles`) — the strongest in-market signal. Signals land in prospects' personalization notes and boost their score.
- **Writer**: Generates 3-email sequences (Email 1 < 75 words, Email 2 < 75, Email 3 < 40). Strict ban list on AI patterns.
- **Sender**: Native providers (gmail/smtp) render merge vars per prospect and STAGE each email into the `outbox` (pending_review → approved → sent) with a scheduled send time; each heartbeat drains due, approved items with human-like pacing, the daily cap, the deterministic pre-send gate, and stop-on-reply. Legacy Instantly path deploys campaigns via API. Enforces daily send limits either way.
- **Handler**: Polls the provider (or Instantly) for replies, dedups them, classifies intent, advances conversation stage, and queues auto-responses through the same outbox approval ladder. On native providers it also detects bounces → marks the address invalid, cancels the prospect's queued sends, and trips a global kill switch past a bounce-rate threshold.
- **Analyst**: Runs on idle cycles. Generates `data/analytics.json` with pipeline stats and insights.

### Conversation Stages
`initial_outreach → engaged → qualifying → presenting → negotiating → closing → closed_won / closed_lost`

### Priority Order
handle_replies > send_campaigns > write_campaigns > prospect > idle (run analyst)

### Key Commands
```bash
source .venv/bin/activate    # Always activate venv first
harvey run                   # Start the heartbeat loop
harvey dashboard             # Web UI at http://localhost:5555
harvey setup                 # Re-run setup wizard
harvey train <url>           # Train on a product website
harvey status                # Pipeline summary
harvey usage                 # Claude quota gauges + per-agent token usage (no dollar costs — subscription plans aren't billed per token)
harvey export                # Deliverable prospects → sequencer-ready CSV (prospects.csv)
harvey export --all          # Full raw list, no filters
harvey gmail auth            # One-time Gmail OAuth (when provider: gmail)
harvey gmail test            # Verify the Gmail connection
harvey outbox                # Review queued emails; --approve <id> / --approve-all / --reject <id>
harvey signals               # The signal vocabulary; --confirm / --reject CODES (or 'free' / 'all')
harvey discover              # Find businesses; --providers / --estimate / --provider <key>
harvey sending pause|resume  # Kill switch for all outbound
```

### Common Issues
- **"command not found: harvey"**: Activate venv first: `source .venv/bin/activate`
- **"ModuleNotFoundError: No module named 'harvey'" after install (macOS)**: Python 3.13 silently ignores `.pth` files that carry the macOS hidden file flag, and some Macs propagate that flag into `.venv`. Run `harvey install` again (it auto-fixes by linking the package), or manually: `ln -s "$(pwd)/harvey" .venv/lib/python3.13/site-packages/harvey`
- **"externally-managed-environment"**: Use a venv, not system Python
- **SQLite errors**: The `data/` directory is created automatically on first run
- **Claude headless mode fails**: User needs `claude login` and an active Max subscription
- **Codex calls fail** (`brain.provider: codex`): the log line says why — `codex login` with ChatGPT (also when the login "has expired or is due for renewal": Harvey never renews it), install the supported Codex version (`harvey status --check` shows what's wrong without a model call; while Codex is unusable Harvey pauses whole cycles on purpose), pick a `brain.model` without code mode, or remove whatever Codex config layer is forcing tools/hooks/MCP back on. Never weaken Harvey's isolation checks to get past it.
- **Instantly API 401**: Wrong API key or needs the Growth plan for API access
- **Google search rate limiting**: Harvey automatically falls back to DuckDuckGo and Bing. For reliable search, add a Serper API key ($5/mo).
