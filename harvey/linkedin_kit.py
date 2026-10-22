"""LinkedIn kit: the user's profile, posts of their work and the send queue.

Nothing here logs into LinkedIn or clicks for the user (that breaks LinkedIn's
terms and gets accounts restricted). Mariana writes, the user pastes or sends:

  perfil  data/linkedin/perfil.md   every profile field ready to paste, in
                                    Portuguese and English: headline options,
                                    About, experience, featured, skills,
                                    custom URL, banner brief for /oyoshi
  posts   data/linkedin/posts.md    one post per portfolio piece, approved by
                                    the user and posted from their account (or
                                    scheduled with a connected official tool)
  fila    the approved LinkedIn drafts of the Mensagens tab, one at a time:
          copy the text, open the profile, the user sends, Mariana marks it
          sent; stops at channels.linkedin.max_daily_messages
"""

from __future__ import annotations

import json
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

from harvey import portfolio
from harvey.dossie import SOBRE_FILE, copy_to_clipboard
from harvey.onboard import KNOWLEDGE_FILE
from harvey.paths import PROJECT_ROOT

OUT_DIR = PROJECT_ROOT / "data" / "linkedin"

RULES = """Rules:
- Use ONLY facts from the material. Never invent clients, numbers, dates or awards.
  When something is missing, write [FALTA: what is missing] so the user fills it.
- Never use em dashes or en dashes. Use colons, commas or parentheses.
- No hype words (apaixonado, guru, ninja, rockstar, passionate, visionary).
- Concrete beats adjectives: who you film for, what changed for them."""


def _material() -> str:
    parts = []
    for f in (KNOWLEDGE_FILE, SOBRE_FILE):
        if f.exists():
            parts.append(f.read_text(encoding="utf-8")[:30000])
    return "\n\n".join(parts)


def _clean(value):
    if isinstance(value, str):
        return value.replace("—", ",").replace("–", ",").strip()
    if isinstance(value, list):
        return [_clean(v) for v in value]
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    return value


def _pt_en(d, key) -> tuple[str, str]:
    v = d.get(key) or {}
    if isinstance(v, str):
        return v, ""
    return v.get("pt", ""), v.get("en", "")


async def build_profile(brain) -> Path:
    material = _material()
    if not material:
        raise ValueError("sem material: rode o onboarding ou 'mariana dossie' antes")
    items = portfolio.load_items()
    prompt = f"""You are a LinkedIn profile strategist for audiovisual professionals
(filmmakers, video editors, producers). Build this person's complete profile,
optimized to be found by and convince the clients in their dossier, in
Portuguese (pt) and English (en).

{RULES}

Material about the person:
{material}

Portfolio pieces:
{portfolio.describe(items) or "(none listed)"}

Return JSON:
{{
  "headlines": [{{"pt": "", "en": "", "why": ""}}],        // 3 options, max 220 chars, keywords clients search
  "about": {{"pt": "", "en": ""}},                          // 1500-2200 chars, hook in the first 2 lines, ends with a clear call to action
  "experience": [{{"title": "", "company": "", "period": "", "location": "",
                   "description": {{"pt": "", "en": ""}}}}],  // newest first, bullet results
  "featured": [{{"title": "", "url": "", "why": ""}}],      // 3-5, strongest first
  "skills": [""],                                           // top 15, ordered; first 3 are the pinned ones
  "services": [""],                                         // for the Services section
  "custom_url": "",                                         // suggested linkedin.com/in/<slug>
  "banner_brief": "",                                       // what the cover image says and shows (for a designer)
  "photo_tips": "",
  "open_to": "",                                            // what to set in Open to work / providing services
  "missing": [""]                                           // what the person still needs to send
}}"""
    data = await brain.think_json(prompt, agent="linkedin", task="profile")
    if not isinstance(data, dict):
        raise RuntimeError("o cérebro não devolveu o perfil; tente de novo")
    data = _clean(data)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "perfil.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))
    path = OUT_DIR / "perfil.md"
    path.write_text(render_profile(data), encoding="utf-8")
    return path


def render_profile(d: dict) -> str:
    out = ["# Perfil do LinkedIn (pronto para colar)", "",
           "Cada bloco vai num campo do perfil. Troque o que estiver em [FALTA: ...] antes de colar.",
           "Ordem sugerida: foto e capa, título, Sobre, Experiência, Destaques, Competências, Serviços, URL.", ""]
    out += ["## Título (headline): escolha um", ""]
    for n, h in enumerate(d.get("headlines") or [], 1):
        out += [f"**Opção {n}** ({h.get('why', '')})", "", f"PT: {h.get('pt', '')}", "",
                f"EN: {h.get('en', '')}", ""]
    pt, en = _pt_en(d, "about")
    out += ["## Sobre", "", "### Português", "", pt, "", "### English", "", en, ""]
    out += ["## Experiência", ""]
    for e in d.get("experience") or []:
        dpt, den = _pt_en(e, "description")
        out += [f"### {e.get('title', '')} | {e.get('company', '')}",
                f"{e.get('period', '')} | {e.get('location', '')}", "", dpt, "", den, ""]
    out += ["## Destaques (Featured)", ""]
    for f in d.get("featured") or []:
        out.append(f"- **{f.get('title', '')}**: {f.get('url', '')} ({f.get('why', '')})")
    out += ["", "## Competências (as 3 primeiras ficam fixadas)", "",
            ", ".join(d.get("skills") or []), "",
            "## Serviços", "", ", ".join(d.get("services") or []), "",
            "## URL personalizada", "", f"linkedin.com/in/{d.get('custom_url', '')}", "",
            "## Capa (para o /oyoshi fazer)", "", d.get("banner_brief", ""), "",
            "## Foto", "", d.get("photo_tips", ""), "",
            "## Aberto a", "", d.get("open_to", ""), ""]
    if d.get("missing"):
        out += ["## Falta você mandar", ""] + [f"- {m}" for m in d["missing"]] + [""]
    return "\n".join(out)


async def build_posts(brain, count: int = 5) -> Path:
    items = portfolio.load_items()
    if not items:
        raise ValueError("nenhum trabalho no portfólio do onboarding (data/onboarding.json)")
    prompt = f"""Write {min(count, len(items))} LinkedIn posts, one per portfolio piece
below (best pieces first), for an audiovisual professional. Each post tells
the story of the job: the client's problem, what was filmed or edited, the
result. Hook in the first line, short paragraphs, 120-220 words, at most 3
hashtags, ends with a soft question or call to action. Portuguese (pt) and
English (en) versions.

{RULES}

Material about the person:
{_material()[:15000]}

Portfolio pieces:
{portfolio.describe(items)}

Return JSON: {{"posts": [{{"piece": "", "url": "", "pt": "", "en": "",
"media": "what to attach (video, frames, before/after)", "best_time": ""}}]}}"""
    data = await brain.think_json(prompt, agent="linkedin", task="posts")
    posts = _clean((data or {}).get("posts") if isinstance(data, dict) else None) or []
    if not posts:
        raise RuntimeError("o cérebro não devolveu os posts; tente de novo")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = ["# Posts dos trabalhos (rascunhos para aprovar)", "",
           "Nada é publicado sozinho. Aprove, ajuste e publique da sua conta "
           "(ou agende numa ferramenta oficial conectada).", ""]
    for n, p in enumerate(posts, 1):
        out += [f"## {n}. {p.get('piece', '')}", "", f"Link: {p.get('url', '')}",
                f"Mídia: {p.get('media', '')}  |  Melhor horário: {p.get('best_time', '')}", "",
                "### PT", "", p.get("pt", ""), "", "### EN", "", p.get("en", ""), ""]
    path = OUT_DIR / "posts.md"
    path.write_text("\n".join(out), encoding="utf-8")
    return path


async def approve_pending(state) -> int:
    """Approve every LinkedIn draft waiting for review (the user saw the list)."""
    n = 0
    for item in await state.get_channel_items("linkedin", "pending_review", limit=1000):
        await state.update_channel_item(item["id"], status="approved")
        n += 1
    return n


async def queue(state, config, ask=input, out=print) -> int:
    """Walk the approved LinkedIn messages: copy, open, the user sends."""
    cap = config.channels.linkedin.max_daily_messages
    left = cap - await state.count_channel_sent_today("linkedin")
    items = await state.get_channel_items("linkedin", "approved")
    if left <= 0:
        out(f"  Limite de hoje atingido ({cap} mensagens). Volte amanhã.")
        return 0
    if not items:
        out("  Nenhuma mensagem do LinkedIn aprovada. Aprove no painel (aba Mensagens).")
        return 0
    out(f"  {len(items)} aprovada(s), {left} cabem hoje. Enter = enviei, p = pular, s = sair.\n")
    sent = 0
    for item in items[:left]:
        text = item["body"]
        if item.get("note"):
            text = f"{item['note']}\n\n(depois que aceitar o convite:)\n{item['body']}"
        out(f"  {item.get('contact_name') or ''} | {item.get('company_name') or ''}")
        out(f"  {item['target']}\n")
        out("    " + text.replace("\n", "\n    ") + "\n")
        copy_to_clipboard(item.get("note") or item["body"])
        if item["target"].startswith("http"):
            webbrowser.open(item["target"])
        answer = (ask("  Texto copiado e perfil aberto. Enviou? ") or "").strip().lower()
        if answer == "s":
            break
        if answer == "p":
            continue
        now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        await state.update_channel_item(item["id"], status="sent", sent_at=now)
        sent += 1
    return sent
