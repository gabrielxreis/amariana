"""Post-job: the cheapest next job is the client you already have.

Two moments, both drafted for approval, never sent on their own:
  * N days after delivery: thank them, ask for a short testimonial and for
    one person who might need video too.
  * Before the client's next event (next_event_date): offer to cover it,
    referencing the work already done together.

Brazilian clients get it on WhatsApp when there is a number (they're
clients now, so the Cloud API may send it); everyone else by email.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

from harvey import market
from harvey.integrations.whatsapp import normalize_phone

logger = logging.getLogger("harvey.postjob")


def _parse(d: str) -> date | None:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime((d or "")[:10], fmt).date()
        except ValueError:
            continue
    return None


class PostJobAgent:
    def __init__(self, brain, state, config, env=None):
        self.brain = brain
        self.state = state
        self.config = config
        self.env = env

    @property
    def cfg(self):
        return self.config.postjob

    def due(self, job: dict, today: date) -> str:
        """'testimonial', 'reengage' or '' for one job."""
        delivered = _parse(job.get("delivered_at", ""))
        if (job.get("status") == "delivered" and delivered
                and not job.get("testimonial_requested_at")
                and today >= delivered + timedelta(days=self.cfg.testimonial_after_days)):
            return "testimonial"
        nxt = _parse(job.get("next_event_date", ""))
        if (job.get("status") in ("won", "delivered") and nxt and today < nxt
                and today >= nxt - timedelta(days=self.cfg.reengage_days_before_event)):
            last = _parse(job.get("reengaged_at", ""))
            if not last or last < nxt - timedelta(days=self.cfg.reengage_days_before_event):
                return "reengage"
        return ""

    async def _write(self, moment: str, job: dict, language: str, channel: str) -> str:
        goal = ("thank them for the project, ask for a short testimonial (2-3 lines they "
                "can reply with) and ask if they know one person or company that could "
                "use video too" if moment == "testimonial" else
                f"their next event is on {job.get('next_event_date')}: offer to cover it, "
                "reference the previous project in one line, ask if they want to talk")
        prompt = f"""Write a short {channel} message from an audiovisual professional to a
past client, in {"Brazilian Portuguese" if language.startswith("pt") else "American English"},
first person, warm and direct, under 70 words, one question at the end. No em
dashes, no exclamation marks, no signature, no links.

Client: {job.get('contact_name')} at {job.get('company_name')}
Previous project: {job.get('service')} ({job.get('segment')})
Goal: {goal}

Return ONLY the message text."""
        text = await self.brain.think(prompt, agent="postjob", task=moment)
        return (text or "").strip().strip('"').replace("—", ",").replace("–", ",")

    async def run(self) -> int:
        if not self.cfg.enabled:
            return 0
        today = date.today()
        drafted = 0
        for job in await self.state.get_jobs():
            moment = self.due(job, today)
            if not moment or not job.get("prospect_id"):
                continue
            prospect = await self.state.get_prospect(job["prospect_id"])
            if not prospect or prospect.status == "opted_out":
                continue
            mk = await market.for_prospect(self.state, prospect,
                                           getattr(self.config.persona, "language", "pt-BR"))
            language = market.language(mk)
            phone = ""
            if mk == market.BR:
                last = await self.state.channel_target_for_prospect(prospect.id, "whatsapp")
                phone = (last or {}).get("target") or normalize_phone(
                    prospect.phone, self.config.channels.whatsapp.default_country_code)
            channel = "whatsapp" if phone else "email"
            if channel == "email" and not prospect.email:
                continue
            body = await self._write(moment, job, language, channel)
            if not body:
                continue
            if channel == "whatsapp":
                await self.state.add_channel_item(
                    channel="whatsapp", target=phone, body=body, kind="postjob",
                    prospect_id=prospect.id, company_id=prospect.company_id,
                    contact_name=job.get("contact_name", ""),
                    company_name=job.get("company_name", ""), language=language,
                    opted_in=True, mode=self.config.channels.whatsapp.mode,
                )
            else:
                subject = ("obrigado pelo projeto" if moment == "testimonial" and language.startswith("pt")
                           else "thank you for the project" if moment == "testimonial"
                           else "próximo evento" if language.startswith("pt") else "your next event")
                await self.state.add_outbox_item(
                    prospect_id=prospect.id, to_email=prospect.email, subject=subject,
                    body=body, kind="postjob", status="pending_review",
                    send_at=datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                )
            stamp = today.isoformat()
            await self.state.update_job(
                job["id"], **({"testimonial_requested_at": stamp} if moment == "testimonial"
                              else {"reengaged_at": stamp}))
            drafted += 1
            logger.info(f"PostJob: {moment} draft for {job.get('company_name')} ({channel}).")
        return drafted
