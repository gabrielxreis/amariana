# Mariana: secretária de IA para audiovisual

A Mariana encontra clientes para profissionais de audiovisual (filmmakers, editores, produtoras), escreve as mensagens, cuida das respostas e leva cada conversa até uma call, um briefing ou um orçamento. Ela roda na assinatura do Claude Code, sem custo de API.

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

0. Antes de perguntar do zero, puxe o que as IAs da pessoa já sabem: `mariana dossie` (ver o subcomando `dossie` no SKILL.md: memória do Claude Code, ChatGPT ou claude.ai). O resultado vai para `data/sobre.md`.
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
- **Brasil**: email + WhatsApp.
- **Resto do mundo**: email + LinkedIn (Instagram se a empresa tiver).
- **Idioma**: sempre o do país onde a empresa está (pelo DDI, pelo domínio e pela cidade): português, espanhol, inglês, francês...

Tudo cai na aba **Mensagens** do painel. A Mariana escreve; a pessoa aprova, clica em "Abrir no WhatsApp" (abre o WhatsApp dela com o texto pronto) ou "Copiar e abrir perfil" (LinkedIn/Instagram) e envia da própria conta. Nenhuma conta é automatizada, então não há risco de ban.
- `mariana whatsapp-check` confere a configuração.
- Modo `cloud_api` (opcional, `channels.whatsapp.mode`): envio automático pela API oficial da Meta, **só** para contatos marcados como opt-in (quem respondeu ou pediu contato). Precisa de `WHATSAPP_TOKEN` e `WHATSAPP_PHONE_NUMBER_ID` no `.env` (Meta for Developers > WhatsApp > API Setup). Nunca ofereça automação não oficial do WhatsApp Web.
- O login automatizado no LinkedIn do Mariana fica desligado (`automate_login: false`): ele viola os termos do LinkedIn.

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

## Referência técnica

A pasta do código se chama `harvey/` por motivo interno; o comando é `mariana`.

### Arquitetura
- **Ciclo** (`main.py`): a cada volta, confere o horário de silêncio, confere o orçamento, decide, faz, registra e dorme.
- **Cérebro** (`brain.py`): chama o `claude -p` em modo automático (ou o Codex) e registra os tokens de cada chamada em `usage_events`.
- **Estado** (`state.py`): SQLite em `data/harvey.db`, com migrações numeradas (`PRAGMA user_version`).
- **Uso** (`usage.py`, `integrations/quota.py`): conta só as chamadas da própria Mariana e lê a cota real da assinatura, freando antes de `usage.max_daily_claude_percent` para sobrar folga para o seu uso.
- **Base de conhecimento** (`skills/`): arquivos Markdown que entram nos prompts dos agentes.
- **Sinais** (`signals.py`): todo fato é uma linha em `observations`. Só sinais confirmados pelo usuário são coletados; `state.cohort(require, exclude)` monta o público em SQL.
- **Painel** (`dashboard.py` + `harvey/web/`): API FastAPI e HTML/CSS/JS servidos do disco, sem build.
- **Descoberta** (`collectors/discover.py`): estima antes, respeita teto de gasto, filtra lixo por padrão; o radar de eventos fica em `collectors/events.py`.
- **Mercado e canais** (`market.py`, `agents/channels.py`): país da empresa pelo DDI, domínio ou cidade; o país define o idioma, e Brasil/exterior define o canal.
- **Fechamento** (`proposal.py`, `pricing.py`, `production.py`, `agents/postjob.py`, `samples.py`, `metrics.py`, `notify.py`, `integrations/calendar.py`).

### Agentes
- **Scout**: o Python busca empresas e resolve emails (padrão primeiro, depois verificação de um candidato); o modelo só pontua e personaliza.
- **Writer**: sequências de 3 emails (menos de 75, 75 e 40 palavras), no idioma do mercado, com lista de frases proibidas.
- **Channels**: uma mensagem de WhatsApp (Brasil), LinkedIn (exterior) ou Instagram por lead, sempre enviada pelo usuário.
- **Sender**: agenda cada email na `outbox` (pending_review → approved → sent) e envia os aprovados com ritmo humano, limite diário, filtro antes do envio e parada quando a pessoa responde. A assinatura entra no envio.
- **Handler**: lê respostas (email, ou coladas/webhook dos outros canais), classifica, avança o estágio e rascunha a resposta com horários livres e portfólio. Detecta bounce e aciona o botão de pânico.
- **PostJob**: follow-up de proposta, lembrete de gravação, aviso de entrega, depoimento, indicação e retomada.
- **Analyst**: nos ciclos parados, gera `data/analytics.json`.

### Estágios da conversa
`initial_outreach → engaged → qualifying → presenting → negotiating → closing → closed_won / closed_lost`

### Prioridade
responder > enviar campanhas > escrever campanhas > prospectar > analisar

### Comandos principais
```bash
source .venv/bin/activate     # ativar o ambiente antes
mariana onboard               # primeiro uso
mariana run                   # o ciclo
mariana dashboard             # painel em http://localhost:5555
mariana status                # resumo (--check testa o cérebro)
mariana usage                 # cota e tokens por agente
mariana export                # leads entregáveis em CSV (--all: tudo)
mariana gmail auth|test       # Gmail + Google Agenda
mariana outbox                # --approve <id> / --approve-all / --reject <id>
mariana signals               # --confirm / --reject CÓDIGOS (ou free / all)
mariana discover              # --providers / --estimate / --provider <fonte>
mariana sending pause|resume  # botão de pânico
```

### Problemas comuns
- **"command not found: mariana"**: ative o ambiente (`source .venv/bin/activate`).
- **"ModuleNotFoundError" depois de instalar (Mac, Python 3.13)**: o Python ignora arquivos `.pth` com a marca de oculto do macOS. Rode `mariana install` de novo, ou: `ln -s "$(pwd)/harvey" .venv/lib/python3.13/site-packages/harvey`.
- **"externally-managed-environment"**: use o ambiente virtual, não o Python do sistema.
- **O Claude não responde em modo automático**: `claude login` e assinatura ativa.
- **Codex falhando** (`brain.provider: codex`): a mensagem do log diz o que fazer: `codex login` com ChatGPT, instalar a versão suportada (`mariana status --check` mostra o problema sem gastar chamada) ou tirar a configuração do Codex que força ferramentas. Nunca enfraqueça o isolamento para contornar.
- **Busca do Google limitada**: ela cai para DuckDuckGo e Bing sozinha; para busca confiável, uma chave do Serper.
