"""Reply rates by market, channel and segment: keep what works, cut the rest.

A prospect counts as "contacted" on a channel when something was actually
sent there (email outbox or channel outbox with status sent), and as
"replied" when their status moved to replied / meeting / closed, or a
conversation exists for them. Jobs count as "won" once status is won or
delivered.
"""

from __future__ import annotations

from collections import defaultdict

from harvey import market, portfolio


def _rate(replied: int, contacted: int) -> float:
    return round(100.0 * replied / contacted, 1) if contacted else 0.0


async def compute(state, default_language: str = "pt-BR") -> dict:
    import aiosqlite

    async with state._connect() as db:
        db.row_factory = aiosqlite.Row
        async def rows(sql, params=()):
            async with db.execute(sql, params) as cur:
                return [dict(r) for r in await cur.fetchall()]

        email_sent = await rows("SELECT DISTINCT prospect_id FROM outbox "
                                "WHERE status = 'sent' AND prospect_id != ''")
        chan_sent = await rows("SELECT DISTINCT prospect_id, channel FROM channel_outbox "
                               "WHERE status = 'sent' AND prospect_id != ''")
        convos = {r["prospect_id"] for r in await rows("SELECT prospect_id FROM conversations")}
        won = {r["prospect_id"] for r in await rows(
            "SELECT prospect_id FROM jobs WHERE status IN ('won', 'delivered')")}

    touches: dict[str, set[str]] = defaultdict(set)
    for r in email_sent:
        touches[r["prospect_id"]].add("email")
    for r in chan_sent:
        touches[r["prospect_id"]].add(r["channel"])

    by = {"market": defaultdict(lambda: [0, 0, 0]), "channel": defaultdict(lambda: [0, 0, 0]),
          "segment": defaultdict(lambda: [0, 0, 0])}
    total = [0, 0, 0]
    for pid, channels in touches.items():
        prospect = await state.get_prospect(pid)
        if not prospect:
            continue
        replied = (prospect.status in ("replied", "meeting", "closed", "won")
                   or pid in convos)
        is_won = pid in won
        mk = await market.for_prospect(state, prospect, default_language)
        company = await state.get_company(prospect.company_id) if prospect.company_id else None
        seg = portfolio.segment_of(prospect.industry, prospect.company,
                                   company.name if company else "",
                                   company.industry if company else "") or "outros"
        country = market.COUNTRY_NAMES.get(getattr(mk, "country", ""), "")
        place = country or ("Brasil" if mk == market.BR else "Exterior")
        keys = [("market", place), ("segment", seg)]
        keys += [("channel", ch) for ch in channels]
        for dim, key in keys:
            by[dim][key][0] += 1
            by[dim][key][1] += int(replied)
            by[dim][key][2] += int(is_won)
        total[0] += 1
        total[1] += int(replied)
        total[2] += int(is_won)

    def table(d):
        return sorted(
            ({"key": k, "contacted": v[0], "replied": v[1], "won": v[2],
              "reply_rate": _rate(v[1], v[0]), "win_rate": _rate(v[2], v[0])}
             for k, v in d.items()),
            key=lambda r: (-r["reply_rate"], -r["contacted"]))

    return {
        "total": {"contacted": total[0], "replied": total[1], "won": total[2],
                  "reply_rate": _rate(total[1], total[0]), "win_rate": _rate(total[2], total[0])},
        "by_market": table(by["market"]),
        "by_channel": table(by["channel"]),
        "by_segment": table(by["segment"]),
    }
