# 🤖 Sistema Avançado de Automação de Lances - Compras.gov.br

Sistema completo de automação de lances para licitações públicas no portal Compras.gov.br, desenvolvido com Playwright, Flask, SQLAlchemy e WebSockets.

## ⚠️ AVISO LEGAL CRÍTICO

**Este sistema é fornecido exclusivamente para fins educacionais e de desenvolvimento.**

Antes de qualquer uso em produção, você DEVE:

1. ✅ **Consultar legal**: Advogado especializado em licitações
2. ✅ **Verificar Edital**: Se permite automação/APIs
3. ✅ **Conformidade**: IN nº 03/2011 do MPOG (Sistema de Compras)
4. ✅ **Termos de Uso**: Compras.gov.br (proíbe bots?)
5. ✅ **Autorização**: Assinada por responsável legal

**Riscos legais:**
- ❌ Desclassificação da licitação
- ❌ Bloqueio permanente do portal
- ❌ Multas administrativas
- ❌ Consequências penais

**USE POR SUA CONTA E RISCO**

---

## 📋 Arquitetura do Sistema

```
compras-bot/
├── app/
│   ├── main.py                 # Flask + SocketIO principal
│   ├── templates/
│   │   └── dashboard.html      # Interface web em tempo real
│   └── __init__.py
│
├── auth/
│   └── session_manager.py      # Login gov.br persistente
│
├── monitor/
│   └── lance_monitor.py        # Monitoramento em tempo real
│
├── engine/
│   └── lance_engine.py         # Lógica de decisão + execução
│
├── core/                       # ⭐ NOVO
│   ├── logger.py               # Logs em tempo real via WebSockets
│   ├── heartbeat.py            # Monitor de saúde + alertas
│   ├── emergency_control.py    # Botão de pânico + parada
│   ├── humanizer.py            # Simulação de comportamento humano
│   └── database.py             # Multi-tenancy com SQLAlchemy
│
├── run.py                      # ⭐ NOVO - Inicialização principal
├── requirements.txt
├── .env.example
├── README.md
└── .gitignore
```

---

## 🆕 Recursos Avançados

### 1. 🔐 **Multi-Tenancy (Múltiplos Usuários)**
- Banco de dados SQLite/PostgreSQL
- Isolamento completo de dados por usuário
- Suporte a múltiplos robôs simultâneos por usuário

**Tabelas:**
- `usuarios`: Login, email, perfil
- `sessoes`: Cookies/localStorage persistentes
- `robo_config`: Configurações de cada robô
- `historico_lance`: Auditoria completa

### 2. 📊 **Logs em Tempo Real**
- WebSockets para transmissão imediata
- Histórico de eventos com timestamps
- Filtro por nível (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Visualização no dashboard

```python
logger.info("Novo lance detectado", user_id="usuario_1", dados={
    'valor': 5000.00,
    'tempo_restante': 30
})
```

### 3. 💓 **Heartbeat Monitor**
- Sinal de vida a cada 30 segundos
- Detecção de timeout
- Métricas em tempo real:
  - Lances aceitos/rejeitados
  - Taxa de erro
  - Uso de CPU/Memória
- Alertas automáticos

### 4. 🚨 **Emergency Controller (Botão de Pânico)**
- Para robô instantaneamente
- Estados: RUNNING, PAUSED, STOPPED, ERROR
- Histórico de ações
- Context manager para segurança

```python
controller = EmergencyController()
controller.iniciar()
# ... operação ...
if erro:
    controller.parar_emergencia("Erro crítico detectado")
```

### 5. 🖱️ **Humanização Avançada**
- Movimento de mouse com trajetória Bézier
- Delays randômicos com distribuição beta
- Digitação humanizada (com pausas)
- Scroll natural
- Variação de padrões de clique

```python
simulator = HumanSimulator(page)
await simulator.clicar_naturalista("button#enviar-lance")
await simulator.digitar_naturalista("1500.00", "input#valor")
```

### 6. 📈 **Monitoramento Administrativo**
- Dashboard mostra:
  - Todos os robôs ativos
  - Status de saúde
  - Lances em tempo real
  - Taxa de sucesso
  - Alertas críticos

---

## 🚀 Instalação Rápida

### 1. Clone/Prepare o Projeto
```bash
cd /home/josue/lance
```

### 2. Ambiente Virtual
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale Dependências
```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Configure Variáveis
```bash
cp .env.example .env
# Edite .env conforme necessário
```

### 5. Inicialize o Sistema
```bash
python3 run.py
```

Acesse: **http://localhost:5000**

---

## 📖 Uso do Sistema

### Primeira Vez: Login Manual

1. No dashboard, clique em **"🔓 Fazer Login Manual"**
2. Navegador abrirá mostrando gov.br
3. Faça login normalmente
4. Resolva CAPTCHA e MFA (se houver)
5. Aguarde até estar autenticado
6. Cookies serão salvos automaticamente no banco de dados

### Adicionar Item para Monitoramento

1. Clique em **"➕ Configurar Novo Item"**
2. Preencha:
   - **Número do Item**: Ex: `00001`
   - **Descrição**: Ex: `Notebook Dell Latitude`
   - **Valor Mínimo**: R$ (hard stop - nunca ultrapassa)
   - **Estratégia**: 
     - 🎯 **Sniper**: Aguarda últimos segundos
     - 📉 **Escada**: Lances gradua is contínuos
   - **Intervalo de Lance**: % de redução (ex: 1%)
   - **Tempo de Gatilho**: Segundos antes do fim (ex: 60s)

### Iniciar Monitoramento

1. No quadro "Itens Monitorados", clique em **"▶️ Ativar"**
2. Monitor começará a observar mudanças
3. Logs aparecerão em tempo real no painel
4. Heartbeat confirmará que robô está vivo

### Em Caso de Erro

1. **Botão Emergência** (vermelho): Para imediatamente
2. **Logs**: Mostram exatamente o que aconteceu
3. **Status**: Verde = saudável, Amarelo = degradado, Vermelho = offline

---

## 🔧 Configuração Avançada

### Ajustar Seletores CSS

Os seletores precisam ser customizados conforme estrutura real do portal:

**[monitor/lance_monitor.py](monitor/lance_monitor.py#L120)**
```python
async def _extrair_lance_atual(self) -> Optional[float]:
    # AJUSTAR SELETOR AQUI
    elemento = await self.page.query_selector('.seu-seletor-aqui')
```

**[engine/lance_engine.py](engine/lance_engine.py#L250)**
```python
async def executar_lance(self, valor: float, item_id: str):
    # AJUSTAR SELETORES
    input_valor = await self.page.query_selector('seu-seletor')
    btn_enviar = await self.page.query_selector('seu-botao')
```

### Adicionar Estratégia Customizada

**[engine/lance_engine.py](engine/lance_engine.py#L85)**
```python
def _avaliar_estrategia_custom(self, lance_atual, tempo_restante):
    # Sua lógica aqui
    if condicao_especial:
        return {
            'deve_dar_lance': True,
            'valor_proposto': novo_valor,
            'motivo': 'Estratégia customizada'
        }
```

### Configurar Alertas

**[core/heartbeat.py](core/heartbeat.py#L150)**
```python
alertas = AlertaManager()
alertas.configuracoes['telegram_token'] = 'seu_token'
alertas.configuracoes['telegram_chat_id'] = 'seu_chat_id'

await alertas.enviar_telegram("Robô parou!")
```

---

## 🗄️ Banco de Dados

### Estrutura

**Tabela `usuarios`**
```sql
id | nome | email | senha_hash | criado_em | ativo
```

**Tabela `sessoes`**
```sql
id | usuario_id | cookies_json | localstorage_json | expira_em | ativo
```

**Tabela `robo_config`**
```sql
id | usuario_id | numero_item | descricao | valor_minimo | 
estrategia | intervalo_lance | ativo | rodando | total_lances
```

**Tabela `historico_lance`**
```sql
id | robo_id | valor_proposto | sucesso | motivo | 
tempo_restante | timestamp | tipo
```

### Operações Comuns

```python
from core.database import DatabaseManager

# Criar usuário
usuario = DatabaseManager.criar_usuario("João", "joao@email.com", hash_senha)

# Obter robôs do usuário
robos = DatabaseManager.listar_robos(usuario_id=1)

# Registrar lance no histórico
lance = DatabaseManager.registrar_lance(
    robo_id=1,
    valor_proposto=5000.00,
    sucesso=True,
    tempo_restante=30,
    tipo='sniper'
)

# Histórico de lances
historico = DatabaseManager.obter_historico_robo(robo_id=1, limite=100)
```

---

## 🧪 Testes

### Testar Logger
```bash
python3 core/logger.py
```

### Testar Heartbeat
```bash
python3 core/heartbeat.py
```

### Testar Emergency Control
```bash
python3 core/emergency_control.py
```

### Testar Humanizer
```bash
python3 core/humanizer.py
```

---

## 📊 Dashboard em Tempo Real

### Componentes

1. **Header**
   - Status da sessão (Ativo/Inativo)
   - Botão de login

2. **Estatísticas**
   - Itens ativos
   - Total de lances enviados
   - Taxa de sucesso

3. **Console de Logs**
   - Eventos em tempo real
   - Filtro por nível
   - Scroll automático

4. **Tabela de Itens**
   - Status de cada robô
   - Botões de controle (Ativar/Pausar)
   - Últimas ações

5. **Alertas**
   - Notificações de erros
   - Heartbeat perdido
   - Lances críticos

---

## 🚀 Escalabilidade Futura

### Celery para Múltiplos Robôs

```python
# tasks.py
from celery import Celery

celery = Celery(__name__)

@celery.task
def executar_robo(robo_id):
    # Cada robô em processo separado
    robo = DatabaseManager.obter_robo(robo_id)
    asyncio.run(robo.iniciar_monitoramento())
```

### Redis para Cache

```python
from redis import Redis

redis = Redis(host='localhost', port=6379)

# Cache de preços atuais
redis.set(f'item:{item_id}', json.dumps(preco_atual))
```

---

## 🐛 Solução de Problemas

| Problema | Solução |
|----------|---------|
| "Sessão expirada" | Execute login manual novamente |
| "Seletor não encontrado" | Inspecione DOM (F12) e ajuste em `monitor/` |
| "Lance rejeitado" | Verifique intervalo mínimo do sistema |
| "Navegador não abre" | `playwright install chromium` |
| "Port 5000 em uso" | `lsof -i :5000` e mude em `run.py` |
| "Banco de dados bloqueado" | Feche outras conexões |

---

## 📞 Referências

- [Playwright Python](https://playwright.dev/python/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Socket.IO Flask](https://flask-socketio.readthedocs.io/)
- [IN nº 03/2011 MPOG](http://www.comprasgovernamentais.gov.br/)

---

## 📄 Licença

Fornecido "como está", sem garantias de qualquer tipo.

**Uso por sua conta e risco.**

---

**Desenvolvido para fins educacionais** | v2.0 | Dezembro 2025
