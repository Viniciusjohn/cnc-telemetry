#!/usr/bin/env bash
set -euo pipefail

# CNC Telemetry — Deploy Beta VM helper script
# Objetivo: padronizar passos manuais em uma VM Ubuntu/CentOS pequena.
# Este script pode ser executado trecho a trecho (copy/paste) para agilizar o setup.

REPO_DIR="/opt/cnc-telemetry-main"
FRONTEND_DIR="$REPO_DIR/frontend"
BACKEND_DIR="$REPO_DIR/backend"
FRONTEND_DIST="/var/www/cnc-telemetry"
PYTHON_BIN="python3.11"
VENV_DIR="$BACKEND_DIR/.venv"

log() {
  echo "[deploy-beta] $1"
}

log "Atualizando pacotes básicos (comente se já fez)"
# sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip git nodejs npm nginx

log "Clonando/atualizando repositório"
if [ ! -d "$REPO_DIR/.git" ]; then
  sudo mkdir -p "$REPO_DIR"
  sudo chown "$USER":"$USER" "$REPO_DIR"
  git clone https://example.com/cnc-telemetry-main.git "$REPO_DIR"
else
  cd "$REPO_DIR"
  git pull
fi

log "Configurando backend (FastAPI + SQLite)"
cd "$BACKEND_DIR"
if [ ! -d "$VENV_DIR" ]; then
  $PYTHON_BIN -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

log "Definindo variáveis de ambiente do backend"
cat <<'EOF' > "$BACKEND_DIR/.env.beta"
TELEMETRY_DATABASE_URL=sqlite:///./telemetry_beta.db
TELEMETRY_API_HOST=0.0.0.0
TELEMETRY_API_PORT=8000
EOF

log "Executando seed opcional"
python -m scripts.seed_beta_demo || true

deactivate

log "Build do frontend"
cd "$FRONTEND_DIR"
npm install
npm run build

log "Publicando build estático em $FRONTEND_DIST"
sudo mkdir -p "$FRONTEND_DIST"
sudo cp -r "$FRONTEND_DIR/dist/." "$FRONTEND_DIST/"
sudo chown -R www-data:www-data "$FRONTEND_DIST"

log "Lembrete: configure o arquivo deploy/cnc-telemetry.service.example em /etc/systemd/system/cnc-telemetry.service"
log "Depois: sudo systemctl daemon-reload && sudo systemctl enable --now cnc-telemetry"
log "Deploy beta finalizado"
