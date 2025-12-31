# Instruções Docker - Sistema de Lances

## 🐳 Início Rápido com Docker

### 1. Build da Imagem
```bash
docker build -t lance-bot:latest .
```

### 2. Executar Container
```bash
docker run -d \
  --name lance-bot \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/sessions:/app/sessions \
  -e SECRET_KEY="sua-chave-secreta-aqui" \
  lance-bot:latest
```

### 3. Ou usar Docker Compose (Recomendado)
```bash
# Iniciar todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f app

# Parar serviços
docker-compose down

# Parar e remover volumes
docker-compose down -v
```

## 🔧 Configuração

### Variáveis de Ambiente (.env)
Crie arquivo `.env` na raiz do projeto:

```env
SECRET_KEY=sua-chave-super-secreta-aqui-use-64-caracteres-aleatorios
DATABASE_URL=sqlite:////app/data/lance_system.db
FLASK_ENV=production
HEADLESS_MODE=true
LOG_LEVEL=INFO
```

### Usando PostgreSQL (Produção)
1. Descomente seção `db` no docker-compose.yml
2. Altere DATABASE_URL:
```env
DATABASE_URL=postgresql://lance_user:senha@db:5432/lance_system
```

## 📊 Comandos Úteis

### Ver logs em tempo real
```bash
docker-compose logs -f app
```

### Acessar shell do container
```bash
docker-compose exec app bash
```

### Reiniciar aplicação
```bash
docker-compose restart app
```

### Ver status dos containers
```bash
docker-compose ps
```

### Backup do banco de dados
```bash
docker-compose exec app sh -c "cp /app/data/lance_system.db /app/data/backup_$(date +%Y%m%d_%H%M%S).db"
```

## 🚀 Deploy em Produção

### 1. Servidor Linux (Ubuntu/Debian)
```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalar Docker Compose
sudo apt-get install docker-compose-plugin

# Clonar projeto
git clone seu-repo.git
cd lance

# Configurar variáveis
cp .env.example .env
nano .env  # Editar

# Iniciar
docker-compose up -d
```

### 2. Configurar Nginx (Proxy Reverso)
```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. SSL com Certbot
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com
```

## 🔒 Segurança

### Alterar permissões dos volumes
```bash
chmod 700 data/
chmod 700 sessions/
```

### Firewall
```bash
# Permitir apenas portas necessárias
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 📈 Monitoramento

### Ver uso de recursos
```bash
docker stats lance-bot
```

### Logs do sistema
```bash
docker-compose logs --tail=100 app
```

## 🐛 Troubleshooting

### Container não inicia
```bash
# Ver logs de erro
docker-compose logs app

# Verificar configuração
docker-compose config

# Rebuild forçado
docker-compose build --no-cache
```

### Navegador Chromium não funciona
```bash
# Entrar no container
docker-compose exec app bash

# Reinstalar Chromium
playwright install chromium
```

### Banco de dados corrompido
```bash
# Restaurar backup
docker-compose exec app sh -c "cp /app/data/backup_YYYYMMDD_HHMMSS.db /app/data/lance_system.db"
docker-compose restart app
```

## 🔄 Atualização

```bash
# Pull nova versão
git pull

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📦 Volumes Persistentes

- `./data` - Banco de dados SQLite
- `./sessions` - Cookies de sessão
- `./logs` - Logs da aplicação
- `redis-data` - Cache Redis

## 🌐 Acessar Aplicação

Após iniciar: http://localhost:5000

## ⚠️ IMPORTANTE

1. **Nunca** commit arquivo `.env` no Git
2. **Sempre** use HTTPS em produção
3. **Faça** backups regulares do banco de dados
4. **Monitore** logs em produção
5. **Teste** em ambiente de homologação primeiro
