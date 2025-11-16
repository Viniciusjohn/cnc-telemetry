#!/usr/bin/env bash
# Script de instalação PostgreSQL 15 + TimescaleDB
# Ubuntu/Debian

set -euo pipefail

echo "🚀 Instalando PostgreSQL 15 + TimescaleDB..."

# Atualizar repositórios
echo "📦 Atualizando apt..."
sudo apt update

# Instalar PostgreSQL 15
echo "📦 Instalando PostgreSQL 15..."
sudo apt install -y postgresql-15 postgresql-contrib-15

# Adicionar repositório TimescaleDB
echo "📦 Adicionando repositório TimescaleDB..."
sudo sh -c "echo 'deb [signed-by=/usr/share/keyrings/timescale.keyring] https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"

# Adicionar chave GPG
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | \
  gpg --dearmor | \
  sudo tee /usr/share/keyrings/timescale.keyring >/dev/null

# Atualizar e instalar TimescaleDB
echo "📦 Instalando TimescaleDB..."
sudo apt update
sudo apt install -y timescaledb-2-postgresql-15

# Configurar TimescaleDB (auto-tune)
echo "⚙️  Configurando TimescaleDB..."
sudo timescaledb-tune --quiet --yes

# Restart PostgreSQL
echo "🔄 Reiniciando PostgreSQL..."
sudo systemctl restart postgresql

# Verificar status
echo "✅ Verificando status..."
sudo systemctl status postgresql --no-pager

# Criar database e user
echo "🗄️  Criando database e usuário..."
sudo -u postgres psql -c "CREATE DATABASE cnc_telemetry;" 2>/dev/null || echo "Database já existe"
sudo -u postgres psql -d cnc_telemetry -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
sudo -u postgres psql -c "CREATE USER cnc_user WITH PASSWORD 'cnc_telemetry_2025';" 2>/dev/null || echo "User já existe"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cnc_telemetry TO cnc_user;"
sudo -u postgres psql -d cnc_telemetry -c "GRANT ALL ON SCHEMA public TO cnc_user;"

echo ""
echo "✅ PostgreSQL 15 + TimescaleDB instalado com sucesso!"
echo ""
echo "📊 Próximos passos:"
echo "  1. Executar schemas:"
echo "     psql -U cnc_user -d cnc_telemetry -f backend/db/schema.sql"
echo "     psql -U cnc_user -d cnc_telemetry -f backend/db/aggregates.sql"
echo "     psql -U cnc_user -d cnc_telemetry -f backend/db/oee_schema.sql"
echo ""
echo "  2. Configurar .env com DATABASE_URL:"
echo "     DATABASE_URL=postgresql://cnc_user:cnc_telemetry_2025@localhost/cnc_telemetry"
echo ""
echo "  3. Testar conexão:"
echo "     psql -U cnc_user -d cnc_telemetry -c 'SELECT version();'"
echo ""
