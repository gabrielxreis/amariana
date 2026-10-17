# Mariana

**A secretária de IA que fecha trabalhos de audiovisual e edição.** Feita para filmmakers, editores de vídeo e produtoras. Roda na sua assinatura do Claude Code (ou do ChatGPT, pelo Codex): sem cobrança por uso de API.

A Mariana encontra quem precisa de vídeo, descobre algo específico sobre cada um, escreve a mensagem certa no canal certo, lê as respostas, conduz a conversa até a call, monta a proposta, faz o follow-up e, depois que você fecha, cuida da produção e do pós-venda. Tudo na sua máquina, em ciclos, e **nada sai sem a sua aprovação**.

## O que ela faz

- **Te conhece no primeiro uso.** Você manda um `.md` sobre você ou a empresa, o site e o portfólio; ela pergunta o que faltar (serviços, preços, clientes, mercados, tom de voz) e monta o dossiê que guia todo o resto.
- **Encontra quem compra vídeo:** igrejas, eventos, casamentos, marcas, agências, academias, imobiliárias, times. Sinais como "site sem vídeo", canal do YouTube, Instagram e LinkedIn da empresa.
- **Radar de eventos:** acha eventos dos próximos meses e aborda o organizador com antecedência.
- **Canal certo por mercado:** Brasil = email + WhatsApp, em português. EUA e exterior = email + LinkedIn, em inglês. Instagram quando a empresa tem.
- **Assinatura de email** gerada e aplicada em todo envio (texto + HTML), com instalação direta no Gmail.
- **Email pronto pra enviar:** confere MX, SPF, DKIM e DMARC do domínio, testa a conexão e manda um teste.
- **WhatsApp sem risco de ban:** você aprova e envia do seu próprio WhatsApp com um clique. A API oficial da Meta só para quem deu opt-in.
- **Respostas em qualquer canal:** se o cliente responde no WhatsApp ou no LinkedIn, os emails pendentes param e ela rascunha a resposta no mesmo canal.
- **Agenda de verdade:** oferece seus horários livres do Google Agenda e marca a call.
- **Portfólio certo pra cada cliente:** igreja recebe vídeo de igreja; time recebe vídeo de esporte.
- **Proposta em PDF** a partir da conversa, com seus serviços e preços, e sugestão de preço pelo histórico dos jobs que você já fechou.
- **Follow-up de proposta** quando o cliente some (3 e 5 dias, só se não houver resposta).
- **Job fechado vira projeto:** cria a pasta do cliente com briefing e memória da marca, pronta pro /ogab editar.
- **Produção:** lembrete na véspera da gravação (horário, endereço, checklist), aviso de entrega, contagem de rodadas de revisão.
- **Pós-venda:** pede depoimento e indicação depois da entrega e volta a oferecer antes do próximo evento do cliente.
- **Amostras:** escolhe os leads mais quentes e prepara o briefing de um corte de 15 s pro /ogab.
- **Avisos no celular** quando alguém responde com interesse (app ntfy ou Telegram, e notificação no Mac).
- **Números:** taxa de resposta e de fechamento por mercado, canal e tipo de cliente.

## Instalar (macOS / Linux)

```bash
curl -fsSL https://raw.githubusercontent.com/gabrielxreis/amariana/main/install.sh | bash
```

Depois, no Claude Code: `/amariana onboard`. A skill se atualiza sozinha a cada uso. Seus dados (`data/`, `.env`, `harvey.local.yaml`) ficam só na sua máquina e nunca são tocados pela atualização.

Pré-requisitos: Python 3.11 ou mais novo (o instalador resolve pelo Homebrew no Mac), git e o Claude Code logado (`claude login`) com assinatura Pro ou Max.

## Comandos

```bash
mariana onboard                   # primeiro uso: a Mariana aprende sobre você
mariana signature                 # gera e mostra a assinatura (--install-gmail instala no Gmail)
mariana gmail auth                # conecta o Gmail e o Google Agenda (uma vez)
mariana email-check --send-test   # confere DNS, conexão e manda um teste
mariana whatsapp-check            # confere o WhatsApp
mariana signals --confirm free    # confirma os sinais grátis
mariana discover                  # encontra empresas (--providers / --estimate)
mariana eventos                   # radar de eventos (--estimate)
mariana profile                   # lê os sites encontrados (grátis)
mariana dashboard                 # painel em http://localhost:5555
mariana run                       # o ciclo: a cada 15 min decide, faz e dorme
mariana proposta --email x@y.com  # proposta em PDF a partir da conversa
mariana amostras                  # briefing de amostras para o /ogab
mariana amostra-pronta --prospect ID --link URL
mariana agenda-check              # próximos horários livres
mariana aviso-teste               # testa o aviso no celular
mariana status                    # resumo do funil
mariana usage                     # uso da assinatura
mariana outbox                    # revisar emails pela linha de comando
mariana export                    # leads com email válido em CSV
mariana sending pause|resume      # botão de pânico: para todos os envios
mariana microsoft auth|test       # Microsoft 365 (docs/microsoft365.md)
mariana train <url>               # aprende um produto a partir de um site
```

Ou abra a pasta no Claude Code e diga "configurar a Mariana": o `CLAUDE.md` guia tudo, passo a passo.

---

## Como ela trabalha

A Mariana roda em ciclos: acorda, confere o orçamento da assinatura, decide o que mais precisa ser feito, faz, registra e dorme. A cada 15 minutos, por padrão.

```
Acorda → Horário de silêncio? → Orçamento ok? → Decide → Faz → Registra → Dorme
```

A decisão é por regra, não por pergunta ao modelo (seria gastar uma chamada com algo que dá pra saber contando):

```
responder > enviar campanhas > escrever campanhas > prospectar > analisar
```

A leitura de sites, as mensagens de WhatsApp/LinkedIn/Instagram, os lembretes de produção e o pós-venda rodam em todo ciclo, porque custam pouco e precisam acontecer na hora.

### Os agentes

| Agente | O que faz |
|---|---|
| **Scout** | Pontua os leads contra o seu perfil de cliente e escreve o ângulo de cada um. O Python faz a busca; o modelo só entra onde precisa de julgamento. |
| **Writer** | Escreve as sequências de email (1º email com menos de 75 palavras, 2º com menos de 75, 3º com menos de 40) no idioma do mercado. Lista rígida de frases proibidas que soam como IA. |
| **Channels** | Escreve a mensagem de WhatsApp (Brasil), LinkedIn (exterior) ou Instagram de cada lead. |
| **Sender** | Monta cada email e agenda na Outbox. Envia os aprovados com ritmo humano, respeitando o limite diário e parando quando a pessoa responde. |
| **Handler** | Lê as respostas, classifica a intenção, avança a conversa e rascunha a resposta com horários livres e o portfólio certo. Detecta bounces e aciona o botão de pânico se passar do limite. |
| **PostJob** | Follow-up de proposta, lembrete de gravação, aviso de entrega, depoimento, indicação e retomada antes do próximo evento. |
| **Analyst** | Nos ciclos parados: estatísticas do funil e o que está funcionando. |

Estágios da conversa: `contato inicial → engajado → qualificando → apresentando → negociando → fechando → ganho / perdido`.

## Você confirma o que ela procura

A Mariana sabe coletar dezenas de sinais sobre uma empresa e não coleta nenhum até você confirmar. Na primeira vez ela *propõe* o catálogo; você confirma, pula ou recusa cada um no painel ou no terminal:

```bash
mariana signals                       # ver o catálogo
mariana signals --confirm free        # tudo o que é grátis
mariana signals --confirm SERP_RANK   # um pago, escolhido de propósito
```

| | Sinal | O que ele diz |
|---|---|---|
| **Audiovisual** | `NO_VIDEO_ON_SITE` | O site não tem nenhum vídeo. A lacuna mais clara pra quem vende vídeo. |
| | `HAS_YOUTUBE_CHANNEL` | Já acreditam em vídeo; o ângulo é qualidade, frequência ou volume de edição. |
| | `INSTAGRAM_PROFILE` / `LINKEDIN_COMPANY` | Onde estão os Reels e por onde falar quando não há email. |
| **Descoberta** | `SERP_RANK` | Posição na busca do próprio serviço. |
| | `NO_WEBSITE` | Tem cadastro e telefone, mas não tem site. |
| | `REVIEW_RATING` / `REVIEW_COUNT` | Bom mas invisível, ou visível mas com dificuldade. |
| **Perfil** | `RUNNING_GOOGLE_ADS` / `RUNNING_META_ADS` | Estão gastando com aquisição hoje: o sinal de orçamento mais forte que dá pra ver de graça. |
| | `INCUMBENT_AGENCY` | Quem cuida da conta hoje (crédito no rodapé do site). |
| | `BLOG_STALE`, `SITE_PAGE_COUNT`, `TECH_STACK`, `HIRING_ROLE` | Conteúdo abandonado, tamanho, plataforma e vagas abertas. |
| **Pessoas** | `CONTACT_FOUND`, `DECISION_MAKER_TITLE`, `LIKELY_OWNER` | Quem decide. |
| **Contato** | `EMAIL_PATTERN`, `EMAIL_STATUS`, `CONTACT_FORM_URL` | Se dá pra falar com eles de verdade. |

Com os sinais confirmados, o construtor de público do painel vira uma consulta: escolha o que o lead **precisa ter** e o que **desqualifica**, e ele conta na hora. Exemplo: "tem Instagram E não tem vídeo no site E NÃO é produtora → 23 empresas".

## O funil de prospecção

Quatro etapas independentes, que podem rodar de novo sem duplicar nada, e sempre mostram o custo.

**1. Descobrir: quem existe.** A única etapa que pode custar dinheiro, então ela sempre estima antes.

| Fonte | Custo | Grátis | Melhor para |
|---|---|---|---|
| **OpenStreetMap** *(padrão)* | grátis | ilimitado, sem conta | Testar tudo antes de pagar. Entende igreja, evento, casamento, academia, imobiliária, restaurante, hotel, clínica, escola, agência, teatro, esporte. |
| **DataForSEO Business Listings** | US$ 0,37 / 1.000 | US$ 1 de crédito | Negócios locais com telefone, site e avaliação. |
| **DataForSEO SERP** | US$ 0,0018 / busca | crédito + sandbox | Posição na busca como sinal. |
| **Serper** | ~US$ 0,30–1,00 / 1.000 | 2.500 grátis | O pago mais fácil de testar; também usado no radar de eventos. |

**2. Perfil: o que eles são.** Grátis. Algumas requisições HTTP por empresa, sem navegador e sem modelo: página inicial, `robots.txt`, `sitemap.xml`, equipe e vagas. Daí saem os sinais que deixam a mensagem específica.

**3. Enriquecer: quem decide.** Nome e cargo da página de equipe, conferidos em registros públicos quando existem.

**4. Verificar: dá pra chegar neles?** Ela aprende o padrão de email de cada empresa e verifica um candidato, em vez de chutar variações. Cada endereço é marcado com honestidade: `verified` / `risky` (aceita tudo) / `guess` / `invalid`. **Só os entregáveis recebem email.**

## Nada sai sem você

Por padrão, **todo email espera a sua aprovação** na Outbox, e toda mensagem de WhatsApp, LinkedIn e Instagram espera na aba Mensagens. Na Outbox, um email ocupa a tela e os outros esperam ao lado: `A` aprova, `R` recusa, `J`/`K` navega.

Antes de qualquer envio, um **filtro automático** (sem modelo) recusa: variáveis não preenchidas, frases proibidas, email longo demais, links demais, HTML no corpo, endereço não entregável e destinatário diferente do cadastro. A assinatura entra depois desse filtro, então os links dela não contam.

Quando confiar, `channels.email.require_approval: false` liga o piloto automático do email. As mensagens dos outros canais continuam sempre manuais.

## O painel

```bash
mariana dashboard     # http://localhost:5555
```

- **Hoje**: o que espera por você, o funil e a atividade
- **Sinais**: a confirmação e o construtor de público
- **Descobrir**: as fontes com preço lado a lado, estimativa e execução
- **Empresas / Contatos**: tudo o que foi encontrado, com exportação CSV
- **Outbox**: os emails para aprovar
- **Mensagens**: WhatsApp, LinkedIn e Instagram, com "Abrir no WhatsApp", "Copiar e abrir perfil" e "Respondeu"
- **Jobs**: propostas, fechados e entregues, com produção, revisões e próximo evento
- **Números**: taxa de resposta e fechamento por mercado, canal e segmento
- **Conversas**: cada resposta, com "Gerar proposta" e "Fechou"
- **Uso**: cota da assinatura e tokens por agente

## Onde ficam os dados

Tudo local, em SQLite (`data/harvey.db`). Cada fato é uma linha, nunca uma coluna: um sinal novo não precisa de migração, o histórico vem de graça, e a confiança e a origem de cada fato ficam guardadas junto com ele.

Tabelas principais: `companies`, `prospects`, `observations`, `campaigns`, `conversations`, `outbox`, `channel_outbox` (WhatsApp/LinkedIn/Instagram), `jobs`, `actions`, `runs`, `usage_events`, `settings`.

Propostas em `data/propostas/`, amostras em `data/amostras/`, assinatura em `data/signature.*`, dossiê em `skills/product_knowledge.md`. As pastas de cliente vão para a pasta de clientes do /ogab (`pasta_saida`) ou para `~/Documents/Mariana/clientes`.

## Configuração

Dois arquivos de texto:

**`.env`**: credenciais e chaves (Gmail, WhatsApp Cloud API, ntfy/Telegram, Serper...). Cada variável explica onde conseguir.

**`harvey.yaml`**: o modelo da configuração. O `mariana onboard` gera o **`harvey.local.yaml`** (fora do git) com os seus dados, e ele tem prioridade:

```yaml
persona:     { name, company, role, email, tone, language, signature }
product:     { name, description, pricing, key_benefits, offer }
icp:         { industries, titles, company_size, geography, geo_coordinates }
channels:
  email:     { provider: gmail | microsoft | smtp, max_daily_sends, require_approval }
  whatsapp:  { enabled, mode: link | cloud_api, countries }
  linkedin:  { enabled }
  instagram: { enabled }
calendar:    { working_hours, working_days, meeting_minutes, slots_to_offer }
notify:      { intents }
production:  { clients_dir, proposal_followup_days, shoot_reminder }
postjob:     { testimonial_after_days, reengage_days_before_event }
usage:       { max_daily_claude_percent, heartbeat_interval_minutes, quiet_hours }
brain:       { provider: claude | codex, model }
```

## Base de conhecimento

O conhecimento de vendas mora em `skills/`, em Markdown que você pode editar. Antes de cada agente rodar, os arquivos que ele usa entram direto no prompt. Mudou o arquivo, o próximo ciclo já se comporta diferente.

- **`audiovisual_offer.md`**: quem compra vídeo, o gancho de cada segmento, objeções e o briefing para orçar
- **`channel_messages.md`**: regras de WhatsApp, LinkedIn e Instagram por mercado
- **`email_frameworks.md`**: como escrever email que parece de gente, frameworks e frases proibidas
- **`signal_playbook.md`**: como transformar um sinal na primeira linha da mensagem
- **`objection_handling.md`**: o ciclo ouvir, reconhecer, avaliar, responder e confirmar
- **`lead_qualification.md`**, **`sales_methodology.md`**, **`offer_strategy.md`**, **`prospecting_tactics.md`**, **`account_navigation.md`**, **`linkedin_outreach.md`**
- **`product_knowledge.md`**: gerado pelo onboarding, com você, seus serviços, preços e portfólio (fora do git)

Os prompts de cada agente ficam em `prompts/`, também editáveis.

## Usar o ChatGPT no lugar do Claude (Codex)

O Claude é o padrão. Se preferir usar um plano do ChatGPT, a Mariana pensa pelo [Codex CLI](https://developers.openai.com/codex), também por assinatura:

```bash
npm install -g @openai/codex@0.159.3
codex login     # escolha "Sign in with ChatGPT"
```

E no config:

```yaml
brain:
  provider: codex
  model: gpt-5.5
```

É um ou outro: se o Codex falhar, a chamada falha com uma mensagem clara, sem trocar para o Claude sozinha. Cada chamada roda isolada, sem ferramentas, sem mexer na sua configuração do Codex, e o seu login só vai para a OpenAI. Só macOS e Linux, na versão 0.159.3 do Codex.

## Lei e entregabilidade

A Mariana automatiza o contato, mas **quem envia é você**.

- **Brasil (LGPD):** contato B2B precisa de interesse legítimo: a mensagem tem que ser relevante para o trabalho da pessoa, você precisa saber de onde veio o contato, e sair tem que ser fácil. Pedido de "não quero" vale para sempre, em todos os canais.
- **EUA (CAN-SPAM):** assunto verdadeiro, remetente real, opt-out que funciona e endereço físico no rodapé.
- **Europa e Reino Unido (GDPR/PECR):** interesse legítimo defensável. Opcionalmente, a verificação por destinatário do [Precleared](https://precleared.dev) (`compliance.precleared.enabled: true`).
- **WhatsApp:** a política da Meta proíbe mensagem comercial pela API para quem não deu opt-in; por isso as mensagens frias saem do seu WhatsApp, enviadas por você.
- **LinkedIn:** automatizar o navegador viola os termos e pode restringir a conta. Fica desligado; as mensagens são enviadas por você.
- **Se perguntarem se é IA,** a resposta é sempre a verdade.

**Aqueça o domínio ou queime o domínio.** Use um domínio só para prospecção, configure SPF, DKIM e DMARC, comece com 10 a 20 emails por dia e suba devagar. Bounce acima de 3%: pare e limpe a lista.

*Nada disso é aconselhamento jurídico.*

## Problemas comuns

**`command not found: mariana`**: rode `source .venv/bin/activate` antes, ou use `.venv/bin/mariana`.

**`SyntaxError` ou `ImportError` estranho logo depois de instalar (Mac)**: o ambiente foi criado com o Python 3.9 do sistema. Refaça: `rm -rf .venv && python3.12 -m venv .venv && .venv/bin/pip install -e .`

**O Claude não responde em modo automático**: `claude login` e confirme que a assinatura está ativa. Teste com `claude -p "oi"`.

**A descoberta não acha nada**: confirme os sinais primeiro (`mariana signals --confirm free`). O OpenStreetMap só cobre categorias mapeadas; `mariana discover --providers` mostra as alternativas.

**Email caindo no spam**: quase sempre é o domínio, não o texto. Confira SPF/DKIM/DMARC com `mariana email-check`, aqueça e reduza o volume.

**A Mariana não faz nada durante o dia**: confira o `quiet_hours` e se bateu o `max_daily_claude_percent`. `mariana status` mostra o estado.

**Parar agora**: `Ctrl+C`, ou `mariana sending pause` para parar os envios e manter o resto rodando.

## Estrutura do projeto

```
harvey/                  # código (o nome da pasta é interno)
├── main.py              # o ciclo
├── brain.py             # Claude/Codex, base de conhecimento e uso
├── onboard.py           # onboarding
├── signature.py         # assinatura de email
├── market.py            # Brasil x exterior, idioma e canal
├── proposal.py          # proposta em PDF
├── pricing.py           # sugestão de preço pelo histórico
├── production.py        # pasta do cliente e produção
├── samples.py           # amostras para o /ogab
├── metrics.py           # números
├── notify.py            # avisos
├── state.py             # banco de dados
├── signals.py           # catálogo de sinais
├── gate.py              # filtro antes do envio
├── dashboard.py         # API do painel
├── collectors/          # descoberta, perfil e radar de eventos
├── agents/              # scout, writer, channels, sender, handler, postjob, analyst
├── integrations/        # Gmail, Microsoft, SMTP, WhatsApp, Google Agenda
└── web/                 # o painel (HTML/CSS/JS, sem build)

skills/                  # base de conhecimento editável
prompts/                 # prompts dos agentes
tests/                   # testes automatizados
```

## Mudanças

Veja o [CHANGELOG.md](CHANGELOG.md).

## Licença

MIT. Veja [LICENSE](LICENSE).
