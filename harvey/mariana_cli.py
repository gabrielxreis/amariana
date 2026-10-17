"""Mariana's own commands: onboarding, signature, email and WhatsApp checks.

Kept apart from cli.py so the upstream Harvey commands stay untouched.
"""

from __future__ import annotations

import asyncio
import webbrowser

DKIM_SELECTORS = ("google", "selector1", "selector2", "default", "k1", "s1",
                  "dkim", "mail", "zoho", "mxvault")


def cmd_onboard(args):
    from harvey.onboard import run_onboarding
    asyncio.run(run_onboarding(
        files=args.file or [], site=args.site or "",
        answers_file=args.answers or "", assume_yes=args.yes,
    ))


def cmd_signature(args):
    from harvey.config import load_config
    from harvey.signature import render_text, write_files

    config = load_config()
    paths = write_files(config)
    print("\n  Assinatura (texto, vai em todo email):\n")
    for line in render_text(config).splitlines():
        print(f"    {line}")
    print(f"\n  HTML pra colar em qualquer cliente de email: {paths['html']}")
    print(f"  Prévia no navegador: {paths['preview']}")
    if not args.no_open:
        webbrowser.open(paths["preview"].as_uri())

    if args.install_gmail:
        from harvey.config import load_env
        from harvey.integrations.gmail import GmailProvider
        provider = GmailProvider(config, load_env())
        if not provider.is_configured():
            print("\n  Gmail ainda não está conectado: rode 'mariana gmail auth'.")
            return
        ok, detail = asyncio.run(provider.install_signature(paths["html"].read_text()))
        print(f"\n  {'✓' if ok else '✗'} {detail}")
    print()


def _txt(name: str) -> list[str]:
    import dns.resolver
    try:
        answers = dns.resolver.resolve(name, "TXT", lifetime=8)
    except Exception:
        return []
    return [b"".join(r.strings).decode(errors="replace") for r in answers]


def _mx(domain: str) -> list[str]:
    import dns.resolver
    try:
        return sorted(str(r.exchange).rstrip(".").lower()
                      for r in dns.resolver.resolve(domain, "MX", lifetime=8))
    except Exception:
        return []


def check_domain(domain: str) -> list[tuple[bool, str, str]]:
    """(ok, item, advice) for MX / SPF / DKIM / DMARC of a sending domain."""
    results = []
    mx = _mx(domain)
    google = any("google" in m for m in mx)
    microsoft = any("outlook" in m or "microsoft" in m for m in mx)
    results.append((bool(mx), "MX", ", ".join(mx[:3]) if mx else
                    "Sem MX: esse domínio não recebe email. Respostas vão se perder."))

    spf = [t for t in _txt(domain) if t.lower().startswith("v=spf1")]
    if not spf:
        include = ("include:_spf.google.com" if google else
                   "include:spf.protection.outlook.com" if microsoft else "include:<seu provedor>")
        results.append((False, "SPF", f'Crie um TXT em {domain}: "v=spf1 {include} ~all"'))
    elif len(spf) > 1:
        results.append((False, "SPF", "Há mais de um registro SPF; junte num só."))
    else:
        results.append((True, "SPF", spf[0]))

    found = ""
    for sel in DKIM_SELECTORS:
        if any("v=dkim1" in t.lower() or "k=rsa" in t.lower()
               for t in _txt(f"{sel}._domainkey.{domain}")):
            found = sel
            break
    advice = ("Ative o DKIM: Google Admin > Apps > Gmail > Autenticar email"
              if google else "Ative o DKIM no painel do seu provedor de email")
    results.append((bool(found), "DKIM", f"seletor '{found}'" if found else advice))

    dmarc = [t for t in _txt(f"_dmarc.{domain}") if t.lower().startswith("v=dmarc1")]
    results.append((bool(dmarc), "DMARC", dmarc[0] if dmarc else
                    f'Crie um TXT em _dmarc.{domain}: "v=DMARC1; p=none; rua=mailto:dmarc@{domain}"'))
    return results


def cmd_email_check(args):
    from harvey.config import load_config, load_env
    from harvey.integrations.mail_provider import get_mail_provider
    from harvey.signature import compose

    config = load_config()
    env = load_env()
    email = config.persona.email
    print(f"\n  Email de envio: {email or '(vazio: preencha persona.email)'}")
    if not email or "@" not in email:
        return
    domain = email.split("@", 1)[1].lower()
    if domain in ("gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "icloud.com"):
        print(f"  ! {domain} é um email pessoal. Funciona pra começar, mas o ideal é um")
        print("    domínio próprio (ex.: contato@suamarca.com.br) e, pra volume, um")
        print("    domínio secundário só de prospecção.")
    else:
        print(f"\n  DNS de {domain}:")
        for ok, item, detail in check_domain(domain):
            print(f"    {'✓' if ok else '✗'} {item:6} {detail}")

    provider = get_mail_provider(config, env)
    if provider is None:
        print(f"\n  Provedor '{config.channels.email.provider}' não é nativo. Use gmail,")
        print("  microsoft ou smtp em channels.email.provider.")
        return
    ok, detail = asyncio.run(provider.test_connection())
    print(f"\n  {'✓' if ok else '✗'} Conexão ({provider.name}): {detail}")
    if ok and args.send_test:
        body = ("Teste da Mariana: se este email chegou, o envio e a assinatura "
                "estão funcionando.")
        result = asyncio.run(provider.send_email(email, "teste da mariana", body))
        print(f"  {'✓' if result.ok else '✗'} Email de teste para {email}"
              + ("" if result.ok else f": {result.error}"))
        print("\n  Como vai sair:\n")
        for line in compose(config, body)[0].splitlines():
            print(f"    {line}")
    print()


def cmd_whatsapp_check(args):
    from harvey.config import load_config, load_env
    from harvey.integrations.whatsapp import CloudAPIClient, normalize_phone, wa_link

    config = load_config()
    env = load_env()
    wa = config.channels.whatsapp
    mine = normalize_phone(config.persona.signature.whatsapp, wa.default_country_code)
    print(f"\n  WhatsApp {'ligado' if wa.enabled else 'desligado'}, modo: {wa.mode}")
    print(f"  Países: {', '.join('+' + c for c in wa.countries) or 'todos'}")
    print(f"  Seu número (assinatura): {('+' + mine) if mine else '(vazio)'}")
    if wa.mode == "link":
        print("\n  Modo link: a Mariana escreve, o painel abre o seu WhatsApp com o")
        print("  texto pronto e você aperta enviar. Nada a configurar.")
        if mine:
            print(f"  Teste: {wa_link(mine, 'Teste da Mariana')}")
    else:
        client = CloudAPIClient(env.whatsapp_token, env.whatsapp_phone_number_id)
        ok, detail = asyncio.run(client.test_connection())
        print(f"\n  {'✓' if ok else '✗'} Cloud API: {detail}")
        print("  Lembrete: pela API só vão mensagens para quem respondeu ou pediu")
        print("  contato (marcado como opt-in no painel). Frio continua manual.")
    print()


def register(subparsers):
    sub = subparsers.add_parser(
        "onboard", help="Primeiro uso: a Mariana aprende tudo sobre você/empresa")
    sub.add_argument("--file", action="append",
                     help="Arquivo .md/.txt/.pdf sobre você (pode repetir)")
    sub.add_argument("--site", default="", help="Site ou portfólio para ler")
    sub.add_argument("--answers", default="", help="JSON com respostas (modo automático)")
    sub.add_argument("--yes", action="store_true", help="Não perguntar nada no terminal")
    sub.set_defaults(func=cmd_onboard)

    sub = subparsers.add_parser("signature", help="Gerar e instalar a assinatura de email")
    sub.add_argument("--install-gmail", action="store_true",
                     help="Definir como assinatura do Gmail conectado")
    sub.add_argument("--no-open", action="store_true", help="Não abrir a prévia")
    sub.set_defaults(func=cmd_signature)

    sub = subparsers.add_parser(
        "email-check", help="Checar DNS (SPF/DKIM/DMARC), conexão e envio de teste")
    sub.add_argument("--send-test", action="store_true",
                     help="Mandar um email de teste para você mesmo")
    sub.set_defaults(func=cmd_email_check)

    sub = subparsers.add_parser("whatsapp-check", help="Checar a configuração do WhatsApp")
    sub.set_defaults(func=cmd_whatsapp_check)
