"""Video samples for the hottest leads, made by Gab (/ogab).

`mariana amostras` picks the top leads that have public video material
(YouTube channel or Instagram linked from their site), writes a brief for
/ogab per lead (what to cut, format, where the material is), and saves it
to data/amostras/<date>.md.

When the sample is ready (`mariana amostra-pronta --prospect ID --link URL`)
Mariana drafts the message that carries it, on the lead's channel: WhatsApp
in Brazil, LinkedIn or Instagram abroad, email otherwise. Approval as always.

The sample uses the lead's own public material and is sent only to them,
privately, as a spec piece. It is never published.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone

from harvey import market, portfolio
from harvey.paths import PROJECT_ROOT

logger = logging.getLogger("harvey.samples")

OUT_DIR = PROJECT_ROOT / "data" / "amostras"

CUTS = {
    "igreja": "Reel 9:16 de 15 s com o trecho mais forte da pregação ou do louvor, legenda animada e chamada para o próximo culto",
    "evento": "teaser 9:16 de 15 s da edição anterior, cortes no ritmo da música, data da próxima edição no fim",
    "casamento": "15 s de highlight com os momentos mais emocionantes, música suave, sem texto",
    "esporte": "15 s de melhores momentos com cortes na batida e placar/nome do time no fim",
    "marca": "anúncio 9:16 de 15 s com o produto em uso, gancho nos 2 primeiros segundos e CTA",
    "imobiliaria": "tour de 15 s do imóvel com movimentos suaves e preço/bairro na tela",
    "institucional": "15 s apresentando o espaço e as pessoas, com uma frase de posicionamento",
    "musica": "15 s do refrão em 9:16 com legenda da letra",
}
DEFAULT_CUT = "Reel 9:16 de 15 s com o melhor trecho do material público, legenda e gancho nos 2 primeiros segundos"


async def _links(state, company_id: str) -> dict[str, str]:
    links = {}
    if not company_id:
        return links
    for row in await state.get_observations(company_id=company_id, latest_only=True):
        if row["signal_code"] in ("HAS_YOUTUBE_CHANNEL", "INSTAGRAM_PROFILE") and row.get("value_text"):
            links[row["signal_code"]] = row["value_text"]
    return links


async def pick_leads(state, top: int = 5) -> list[dict]:
    """Highest-scored leads with public video material, not sampled before."""
    sampled = set()
    for item in await state.get_channel_items(limit=1000):
        if item.get("kind") == "sample":
            sampled.add(item["prospect_id"])
    done = (await state.get_setting("samples_done")) or ""
    sampled |= set(filter(None, done.split(",")))
    candidates = []
    for status in ("queued", "contacted", "replied", "new"):
        candidates += await state.get_prospects_by_status(status)
    candidates.sort(key=lambda p: p.score or 0, reverse=True)
    picked = []
    for p in candidates:
        if p.id in sampled:
            continue
        links = await _links(state, p.company_id)
        if not links:
            continue
        company = await state.get_company(p.company_id) if p.company_id else None
        picked.append({"prospect": p, "company": company, "links": links})
        if len(picked) >= top:
            break
    return picked


async def write_briefs(state, top: int = 5) -> tuple[str, list[dict]]:
    leads = await pick_leads(state, top)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{date.today().isoformat()}.md"
    out = [f"# Amostras da semana ({date.today().strftime('%d/%m/%Y')})", "",
           "Para o Gab (/ogab): um corte curto por lead, com o material público deles.",
           "Enviado só para o próprio lead, em particular. Nunca publicar.", ""]
    for n, lead in enumerate(leads, 1):
        p, c = lead["prospect"], lead["company"]
        name = c.name if c else p.company
        seg = portfolio.segment_of(p.industry, name, c.description if c else "")
        out += [f"## {n}. {name}", "",
                f"- **Contato:** {p.full_name()} ({p.title}), id `{p.id}`",
                f"- **Segmento:** {seg or 'geral'}  |  **Score:** {p.score}",
                f"- **Material:** " + " | ".join(lead["links"].values()),
                f"- **Site:** {c.website or c.domain if c else ''}",
                f"- **Corte sugerido:** {CUTS.get(seg, DEFAULT_CUT)}",
                f"- **Quando pronto:** `mariana amostra-pronta --prospect {p.id} --link <link>`",
                ""]
    if not leads:
        out.append("Nenhum lead com YouTube ou Instagram no site ainda. Rode `mariana profile` "
                   "com os sinais HAS_YOUTUBE_CHANNEL e INSTAGRAM_PROFILE confirmados.")
    path.write_text("\n".join(out), encoding="utf-8")
    return str(path), leads


async def sample_ready(state, brain, config, prospect_id: str, link: str) -> str:
    """Draft the message carrying the finished sample. Returns where it went."""
    from harvey.agents.channels import ChannelsAgent
    prospect = await state.get_prospect(prospect_id)
    if not prospect:
        raise ValueError("prospect not found")
    mk = await market.for_prospect(state, prospect, getattr(config.persona, "language", "pt-BR"))
    lang = market.language_name(mk)
    choice = await ChannelsAgent(brain, state, config).choose(prospect)
    channel = choice[0] if choice else "email"
    prompt = f"""Write a short {channel} message, first person, in {lang}, from an
audiovisual professional who made a 15-second sample for this lead using their
own public material, to show what they could do together. Under 60 words, warm,
no pressure, one question at the end. Include this link exactly once: {link}
No em dashes, no exclamation marks, no signature.

Lead: {prospect.full_name()} ({prospect.title}) at {prospect.company}
Notes: {prospect.personalization_notes}

Return ONLY the message."""
    body = (await brain.think(prompt, agent="samples", task="sample_message") or "").strip().strip('"')
    body = body.replace("—", ",").replace("–", ",")
    if link not in body:
        body = f"{body}\n\n{link}"
    if choice:
        await state.add_channel_item(
            channel=choice[0], target=choice[1], body=body, kind="sample",
            prospect_id=prospect.id, company_id=prospect.company_id,
            contact_name=prospect.full_name(), company_name=choice[3],
            language=market.language(mk), mode="manual",
        )
    elif prospect.email:
        await state.add_outbox_item(
            prospect_id=prospect.id, to_email=prospect.email,
            subject=market.pick(mk, pt="fiz uma coisa pra vocês", es="hice algo para ustedes", fr="j'ai fait quelque chose pour vous", en="made something for you"),
            body=body, kind="sample", status="pending_review",
            send_at=datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        )
    else:
        raise ValueError("lead has no channel to receive the sample")
    done = (await state.get_setting("samples_done")) or ""
    await state.set_setting("samples_done", ",".join(filter(None, [done, prospect.id])))
    return channel
