#!/usr/bin/env bash
# Script para reiniciar ambiente de desenvolvimento limpo

set -euo pipefail

echo "🔄 Reiniciando ambiente de desenvolvimento..."

# Matar processos nas portas
echo "Liberando portas..."
lsof -ti :5000 | xargs kill -9 2>/dev/null || true
lsof -ti :8001 | xargs kill -9 2>/dev/null || true
lsof -ti :5173 | xargs kill -9 2>/dev/null || true

echo "✅ Portas liberadas"
echo ""
echo "Agora execute em terminais separados:"
echo ""
echo "# Terminal 1 - Simulador"
echo "python3 scripts/mtconnect_simulator.py --port 5000"
echo ""
echo "# Terminal 2 - Backend"
echo "cd backend && source .venv/bin/activate && uvicorn main:app --port 8001 --reload"
echo ""
echo "# Terminal 3 - Frontend"
echo "cd frontend && npm run dev"
