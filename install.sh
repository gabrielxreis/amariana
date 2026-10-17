#!/usr/bin/env bash
# Instalador da Mariana (/amariana), a secretária de IA para audiovisual.
# Uso:  curl -fsSL https://raw.githubusercontent.com/gabrielxreis/amariana/main/install.sh | bash
# Pode rodar de novo quando quiser: atualiza a skill e só instala o que faltar.
# Seus dados (data/, .env, harvey.local.yaml) nunca são tocados.
set -euo pipefail

REPO="https://github.com/gabrielxreis/amariana"
DEST="$HOME/.claude/skills/amariana"

ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
info() { printf "\n\033[1m%s\033[0m\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }

info "1/5 Python 3.11+ e git"
PY=""
for c in python3.13 python3.12 python3.11 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
    PY="$(command -v "$c")"; break
  fi
done
if [ -z "$PY" ]; then
  if [ "$(uname)" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
    echo "  Instalando Python 3.12 pelo Homebrew..."
    brew install python@3.12 git >/dev/null
    PY="$(brew --prefix)/bin/python3.12"
  else
    echo "  Preciso do Python 3.11 ou mais novo. No Mac: instale o Homebrew (https://brew.sh)"
    echo "  e rode: brew install python@3.12   Depois rode este instalador de novo."
    exit 1
  fi
fi
command -v git >/dev/null 2>&1 || { echo "  Instale o git e rode de novo."; exit 1; }
ok "$("$PY" --version)"

info "2/5 Baixando / atualizando a Mariana"
mkdir -p "$HOME/.claude/skills"
if [ -d "$DEST/.git" ] || [ -L "$DEST" ]; then
  git -C "$DEST" pull --ff-only --quiet && ok "atualizada em $DEST"
else
  git clone --quiet "$REPO" "$DEST" && ok "instalada em $DEST"
fi

info "3/5 Ambiente Python"
cd "$DEST"
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/pip install -q --upgrade pip >/dev/null
.venv/bin/pip install -q -e . && ok "dependências instaladas"

info "4/5 Arquivos locais"
[ -f .env ] || { cp .env.example .env && ok ".env criado (fica só na sua máquina)"; }
[ -f .env ] && ok ".env presente"
mkdir -p data

info "5/5 PDF das propostas"
if [ -d "/Applications/Google Chrome.app" ] || command -v google-chrome >/dev/null 2>&1; then
  ok "Google Chrome encontrado (as propostas saem em PDF)"
else
  warn "Sem Google Chrome: instalando o Chromium do Playwright para gerar PDF..."
  .venv/bin/python -m playwright install chromium >/dev/null 2>&1 && ok "Chromium instalado" \
    || warn "não deu; as propostas saem em HTML (dá pra salvar como PDF no navegador)"
fi

printf "\n\033[1mPronto.\033[0m Abra o Claude Code e digite:\n\n    /amariana onboard\n\n"
printf "A Mariana vai te conhecer (pode mandar um .md sobre você), criar sua assinatura,\n"
printf "preparar o email e o WhatsApp. Nada é enviado sem a sua aprovação.\n\n"
