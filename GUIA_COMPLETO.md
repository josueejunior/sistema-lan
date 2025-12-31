# Robô de Lances Automáticos - Guia Completo de Implementação

## 📋 Índice
1. Visão Geral da Arquitetura
2. Estrutura de Pastas
3. Módulos Implementados
4. Fluxo de Execução
5. Como Usar
6. Integração com Flask
7. Segurança e Contingência
8. Próximos Passos

---

## 🏗️ 1. Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────┐
│        Flask Web UI + WebSocket (Dashboard)          │
├─────────────────────────────────────────────────────┤
│  RoboLancesAvancado (Orquestrador Principal)         │
├──────────┬──────────┬──────────┬────────────────────┤
│ Session  │ Monitor  │ Engine   │ GerenciadorItens   │
│ Manager  │ + Logger │ + Lance  │                    │
├──────────┼──────────┼──────────┼────────────────────┤
│ Heartbeat│ Pos-Lance│ Humaniz. │ Playwright         │
└──────────┴──────────┴──────────┴────────────────────┘
```

---

## 📁 2. Estrutura de Pastas

```
comprasnet-bot/
├── auth/
│   └── session_manager.py          # Login persistente com gov.br
│
├── monitor/
│   ├── lance_monitor.py            # Monitoramento em tempo real
│   ├── heartbeat.py                # Health check do sistema
│   └── realtime_logger.py           # Logs via WebSocket
│
├── engine/
│   ├── lance_engine.py             # Decisão e execução (humanizadas)
│   ├── gerenciador_itens.py        # Multi-threading de itens
│   └── pos_lance.py                # Captura de resultados e IA
│
├── app/
│   ├── main.py                     # Flask básico
│   └── main_avancado.py            # Flask com WebSocket
│
├── templates/
│   ├── dashboard.html              # Dashboard básico
│   └── dashboard_avancado.html     # Dashboard com WebSocket
│
├── static/                         # CSS, JS extras
│
├── integracao_completa.py          # Exemplo completo de uso
├── robo_main.py                    # Script standalone
├── requirements.txt                # Dependências
├── .env.example                    # Variáveis de ambiente
├── .gitignore
└── README.md
```

---

## 🔧 3. Módulos Implementados

### 3.1 Autenticação Persistente (`auth/session_manager.py`)
**Funcionalidade**: Login manual na primeira vez, reutilização de cookies
```python
# Primeira execução
manager = SessionManager()
await manager.create_new_session("https://www.gov.br/compras")

# Execuções posteriores
context = await manager.load_existing_session(url)
```

### 3.2 Monitoramento em Tempo Real (`monitor/lance_monitor.py`)
**Funcionalidade**: Observa mudanças de lance, tempo restante, intervalo mínimo
```python
monitor = MonitorLances(page, item_config)
monitor.registrar_callback('lance_mudou', callback)
await monitor.iniciar(intervalo_polling=2.0)
```

### 3.3 Heartbeat Monitor (`monitor/heartbeat.py`)
**Funcionalidade**: Envia sinais a cada 30s confirmando que está vivo
```python
heartbeat = HeartbeatMonitor(intervalo_segundos=30)
notificador = NotificadorHeartbeat()
notificador.configurar_discord("webhook_url")
heartbeat.registrar_callback(notificador.notificar)
```

### 3.4 Logger em Tempo Real (`monitor/realtime_logger.py`)
**Funcionalidade**: Transmite logs via WebSocket para o dashboard
```python
logger = LoggerRealtime()
logger.adicionar_conexao_websocket(websocket_callback)
await logger.info("Mensagem", {'dados': 'extras'})
```

### 3.5 Engine de Decisão e Execução (`engine/lance_engine.py`)
**Funcionalidade**: 
- Calcula valores de lance (Sniper ou Escada)
- Simula movimento de mouse
- Digita como humano
- Hard stop (nunca vai abaixo do mínimo)
```python
engine = EngineDecisao(item_config)
decisao = engine.avaliar_lance(lance_atual, tempo_restante, intervalo_minimo)

executor = ExecutorLances(page, logger)
resultado = await executor.executar_lance(valor, item_id)
```

### 3.6 Gerenciador de Múltiplos Itens (`engine/gerenciador_itens.py`)
**Funcionalidade**: Coordena monitoramento de 5+ itens simultâneos
```python
gerenciador = GerenciadorItens(max_itens_simultaneos=5)
gerenciador.adicionar_item("ITEM_001")
await gerenciador.iniciar_item("ITEM_001", funcao_monitoramento)
```

### 3.7 Pós-Lance e Inteligência Comercial (`engine/pos_lance.py`)
**Funcionalidade**: 
- Download automático de atas
- Análise de concorrentes
- Banco de dados de preços
```python
capturador = CapturadorResultados()
await capturador.baixar_ata(page, item_id, numero_disputa)

analisador = AnalisadorConcorrentes()
await analisador.registrar_concorrentes(numero_disputa, item_id, concorrentes)
```

---

## 🔄 4. Fluxo de Execução

### Primeira Execução (Setup)
```
1. Usuário executa: python3 auth/session_manager.py
2. Navegador abre (modo headful)
3. Usuário faz login manual no gov.br
4. Resolve CAPTCHA e MFA
5. Sistema salva cookies em compras_session.json
```

### Execuções Normais
```
1. python3 app/main_avancado.py (ou integração_completa.py)
2. Carrega sessão salva
3. Inicializa Heartbeat (sinais a cada 30s)
4. Adiciona itens para monitoramento
5. Loop contínuo:
   a. Monitor verifica lance atual
   b. Engine avalia se deve dar lance
   c. Se sim, Executor envia lance
   d. Logger transmite tudo via WebSocket
6. Botão Pânico para no caso de emergência
7. Pós-Lance captura ata e analisa concorrentes
```

---

## 🚀 5. Como Usar

### 5.1 Setup Inicial
```bash
cd /home/josue/lance

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
playwright install chromium

# Copiar configuração
cp .env.example .env
```

### 5.2 Primeiro Login
```bash
python3 auth/session_manager.py
# Navegador abre
# Você faz login manualmente
# Pressione ENTER para salvar
```

### 5.3 Iniciar o Sistema

**Opção 1: Dashboard Web**
```bash
python3 app/main_avancado.py
# Acesse http://localhost:5000
# Configure itens pelo dashboard
# Clique em ativar
```

**Opção 2: Script Standalone**
```bash
python3 integracao_completa.py
# Ou personalizar robo_main.py
```

### 5.4 Monitorar em Tempo Real
- Abra o dashboard em http://localhost:5000
- Acompanhe logs em tempo real via WebSocket
- Botão 🚨 PÂNICO para parar tudo
- Heartbeat indicator mostra que está vivo

---

## 🔌 6. Integração com Flask

### No seu `main_avancado.py`:

```python
from integracao_completa import RoboFlaskBridge

# Na inicialização da app
bridge = None

@socketio.on('connect')
def ao_conectar():
    global bridge
    if not bridge:
        bridge = RoboFlaskBridge(socketio)
        asyncio.create_task(bridge.inicializar())

@app.route('/api/add-item', methods=['POST'])
async def add_item():
    data = request.get_json()
    await bridge.adicionar_item(
        data['numero_item'],
        data['descricao'],
        data['valor_minimo']
    )
    return jsonify({'success': True})

@app.route('/api/panico', methods=['POST'])
async def panico():
    await bridge.ativar_panico()
    return jsonify({'success': True})
```

---

## 🛡️ 7. Segurança e Contingência

### Heartbeat Monitor (Cada 30 segundos)
```
✅ Vivo - continua
❌ Morto por 2 minutos - alerta via:
   • Discord (webhook)
   • Slack (webhook)
   • Email (configurável)
```

### Botão Pânico
- Para TODO robô imediatamente
- Desativa novos lances
- Logs indicam parada
- Requer clique confirmado para retomar

### Logs em Tempo Real
- WebSocket transmite TUDO que o robô vê
- Operador acompanha decisões em tempo real
- Debug facilitado

### Tratamento de Erros
```python
try:
    # operação
except Exception as e:
    await logger.error(f"Erro: {e}")
    heartbeat.registrar_erro(str(e))
    # continua operando
```

---

## 📊 8. Próximos Passos

### Implementação Imediata
- [ ] Ajustar seletores CSS conforme portal real
- [ ] Testar em homologação (valores baixos)
- [ ] Calibrar delays humanizados
- [ ] Treinar operador no dashboard

### Curto Prazo (1-2 semanas)
- [ ] Testes em licitações reais
- [ ] Integração com base de dados (MySQL/PostgreSQL)
- [ ] Backup automático de sessões
- [ ] Notificações por SMS/Telegram

### Médio Prazo (1 mês)
- [ ] Dashboard com gráficos de concorrência
- [ ] Análise preditiva de preços
- [ ] Integração com histórico fiscal
- [ ] Modo "rehearsal" com dados simulados

### Longo Prazo (3+ meses)
- [ ] Machine learning para otimizar estratégias
- [ ] Integração com múltiplos pregões simultâneos
- [ ] API para integração com sistemas ERP
- [ ] Interface mobile (React Native)

---

## 📞 Suporte e Referências

### Documentação
- [Playwright Python Docs](https://playwright.dev/python/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/)
- [Compras.gov.br API](https://www.gov.br/compras/pt-br)

### Problemas Comuns

**P: "Seletor não encontrado"**
R: Use F12 (DevTools) no navegador para inspecionar o HTML real

**P: "Sessão expirada"**
R: Execute novamente `session_manager.py` para novo login

**P: "Lances rejeitados"**
R: Verifique intervalo mínimo e ajuste `delay_humanizado`

**P: "Conta bloqueada"**
R: Reduza frequência de lances, aumente delays

---

## ⚖️ AVISO LEGAL FINAL

Este projeto é **exclusivamente educacional**. O uso em ambiente de produção para participar de licitações reais requer:

✅ Aprovação legal expressa
✅ Conformidade com edital
✅ Consulta a IN nº 03/2011
✅ Auditoria de segurança
✅ Termo de responsabilidade assinado

**Uso inadequado pode resultar em penalidades administrativas e legais.**

---

**Desenvolvido em Dezembro de 2025** | **Versão 2.0 (Avançada)**
