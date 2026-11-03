---
name: amariana
description: "DESATIVADO: a Mariana (/amariana) agora é o Gab. Prospecção de clientes de vídeo, mensagens de email, WhatsApp, LinkedIn e Instagram, proposta, follow-up, produção do job e arrumar o LinkedIn e o Instagram do usuário são feitos pelo /ogab (/ogab comercial). Use só quando o usuário digitar /amariana ou /mariana, para avisar e passar o pedido ao /ogab."
---

# /amariana foi desativado: a Mariana agora é o Gab (/ogab)

Desde 03/11/2026 a Mariana mora dentro do Gab. Este comando NÃO roda mais sozinho: não rode `mariana`, não abra painel,
não escreva mensagem nem proposta daqui.

1. Avise o usuário em UMA linha: "O /amariana foi desativado: a Mariana agora é o Gab. Prospecção, propostas, LinkedIn
   e Instagram ficam no /ogab (`/ogab comercial <pedido>`)."
2. Se o /ogab estiver instalado (`~/.claude/skills/ogab/SKILL.md`), chame a skill `ogab` pela ferramenta Skill com
   `comercial <o pedido do usuário>` e siga por lá (o passo zero do Gab cuida de licença e atualização).
3. Sem o /ogab: diga que o comercial agora vem com o Gab e passe o link **https://ogab.io**. Não faça o trabalho por aqui.

Quem já usava a Mariana: copie `data/`, `.env`, `harvey.local.yaml` e `skills/product_knowledge.md` desta pasta para
`~/.claude/skills/ogab/comercial/` e rode `bash ~/.claude/skills/ogab/comercial/install.sh`. Depois esta pasta pode
ser apagada.
