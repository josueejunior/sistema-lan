#!/bin/bash
# Script de Deploy Automático

set -e  # Para em caso de erro

echo "🚀 Iniciando deploy do Sistema de Lances..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker não encontrado. Instalando...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker Compose não encontrado. Instalando...${NC}"
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
fi

# Criar diretórios necessários
echo -e "${YELLOW}📁 Criando diretórios...${NC}"
mkdir -p data sessions logs

# Verificar arquivo .env
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Arquivo .env não encontrado. Criando...${NC}"
    cp .env.example .env
    echo -e "${RED}❗ IMPORTANTE: Edite o arquivo .env antes de continuar!${NC}"
    echo -e "${RED}   Execute: nano .env${NC}"
    read -p "Pressione ENTER após editar o .env..."
fi

# Parar containers antigos
echo -e "${YELLOW}🛑 Parando containers antigos...${NC}"
docker-compose down 2>/dev/null || true

# Build da imagem
echo -e "${YELLOW}🔨 Building imagem Docker...${NC}"
docker-compose build --no-cache

# Iniciar serviços
echo -e "${YELLOW}🚀 Iniciando serviços...${NC}"
docker-compose up -d

# Aguardar inicialização
echo -e "${YELLOW}⏳ Aguardando inicialização...${NC}"
sleep 10

# Verificar saúde
echo -e "${YELLOW}🏥 Verificando saúde dos containers...${NC}"
docker-compose ps

# Testar aplicação
echo -e "${YELLOW}🧪 Testando aplicação...${NC}"
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Aplicação está rodando!${NC}"
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ DEPLOY CONCLUÍDO COM SUCESSO!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo ""
    echo "🌐 Acesse: http://localhost:5000"
    echo "📊 Ver logs: docker-compose logs -f app"
    echo "🛑 Parar: docker-compose down"
    echo ""
else
    echo -e "${RED}❌ Aplicação não está respondendo${NC}"
    echo "Ver logs: docker-compose logs app"
    exit 1
fi

# Mostrar logs iniciais
echo -e "${YELLOW}📋 Últimas linhas do log:${NC}"
docker-compose logs --tail=20 app
