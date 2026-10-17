"""Which market a prospect is in, and so which language and channels to use.

Brazil  → Portuguese; email + WhatsApp.
Abroad  → English; email + LinkedIn (+ Instagram when the business has one).

Decided from the strongest evidence available, in order: the phone's
country code, a .br domain, then the location text. No evidence falls back
to the persona's language, so a Brazilian user prospecting locally and a
user prospecting the US both get a sensible default.
"""

from __future__ import annotations

import re

BR = "BR"
INTL = "INTL"

_BR_LOCATION = re.compile(
    r"\b(brasil|brazil|rio de janeiro|s[ãa]o paulo|belo horizonte|bras[ií]lia|"
    r"curitiba|porto alegre|salvador|recife|fortaleza|goi[âa]nia|niter[óo]i|"
    r"campinas|florian[óo]polis|vit[óo]ria|manaus|bel[ée]m|"
    r"\b(RJ|SP|MG|RS|PR|SC|BA|PE|CE|GO|DF|ES)\b)",
    re.IGNORECASE,
)


def detect(phone: str = "", domain: str = "", location: str = "",
           default_language: str = "pt-BR") -> str:
    digits = re.sub(r"\D", "", phone or "")
    pt_default = default_language.lower().startswith("pt")
    if digits:
        raw = (phone or "").strip()
        if raw.startswith("+") or digits.startswith("00"):
            return BR if digits.lstrip("0").startswith("55") else INTL
        if digits.startswith("55") and len(digits) >= 12:
            return BR
        # No country code: a local number in the user's own market.
        if len(digits) in (10, 11):
            return BR if pt_default else INTL
    host = (domain or "").lower().strip().rstrip("/")
    if host.endswith(".br"):
        return BR
    if location:
        return BR if _BR_LOCATION.search(location) else INTL
    return BR if default_language.lower().startswith("pt") else INTL


def language(market: str) -> str:
    return "pt-BR" if market == BR else "en"


def language_name(market: str) -> str:
    return ("Brazilian Portuguese (português do Brasil)" if market == BR
            else "American English")


async def for_prospect(state, prospect, default_language: str = "pt-BR") -> str:
    """Market for a prospect, looking at its company when it has one."""
    phone, domain, location = prospect.phone, "", ""
    if prospect.company_id:
        try:
            company = await state.get_company(prospect.company_id)
        except Exception:
            company = None
        if company:
            phone = phone or company.phone
            domain = company.domain
            location = company.location
    if not domain and prospect.email and "@" in prospect.email:
        domain = prospect.email.split("@", 1)[1]
    return detect(phone, domain, location, default_language)
