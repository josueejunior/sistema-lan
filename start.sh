#!/bin/bash
# Quick Start - Script de inicialização rápida

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  🤖 ROBÔ DE LANCES - COMPRAS.GOV.BR (Quick Start)            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar Python
echo -e "${YELLOW}[1/5]${NC} Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 não encontrado!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python encontrado${NC}"

# Criar venv
echo ""
echo -e "${YELLOW}[2/5]${NC} Criando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
echo -e "${GREEN}✅ Ambiente ativado${NC}"

# Instalar dependências
echo ""
echo -e "${YELLOW}[3/5]${NC} Instalando dependências..."
pip install -q -r requirements.txt
playwright install chromium > /dev/null 2>&1
echo -e "${GREEN}✅ Dependências instaladas${NC}"

# Configurar .env
echo ""
echo -e "${YELLOW}[4/5]${NC} Configurando ambiente..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ Arquivo .env criado${NC}"
else
    echo -e "${GREEN}✅ Arquivo .env já existe${NC}"
fi

# Iniciar
echo ""
echo -e "${YELLOW}[5/5]${NC} Iniciando sistema..."
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Sistema pronto!${NC}"
echo ""
echo "🌐 Acesse: http://localhost:5000"
echo ""
echo "⚠️  LEMBRE-SE:"
echo "   • Consulte advogado antes de usar em produção"
echo "   • Confirme conformidade com o edital"
echo "   • Verifique Termos de Uso do Compras.gov.br"
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

python3 run.py
