"""
Guia de Implementação - Roteiro Prático
Como implementar cada funcionalidade no seu projeto
"""

# ============================================================================
# 1. INTEGRAR LOGGER COM MONITOR DE LANCES
# ============================================================================

# No seu monitor/lance_monitor.py:

from core.logger import logger

async def _verificar_pagina(self):
    try:
        lance_atual = await self._extrair_lance_atual()
        tempo_restante = await self._extrair_tempo_restante()
        
        # LOG: Situação atual
        logger.debug(
            f"Verificação realizada",
            user_id=str(self.item_config.get('user_id')),
            dados={
                'lance': lance_atual,
                'tempo': tempo_restante,
                'item': self.item_config['numero_item']
            }
        )
        
        # LOG: Se lance mudou
        if lance_atual != self.ultimo_lance:
            logger.info(
                f"Lance mudou! {self.ultimo_lance} → {lance_atual}",
                user_id=str(self.item_config.get('user_id'))
            )
            self.ultimo_lance = lance_atual

# ============================================================================
# 2. INTEGRAR EMERGENCY CONTROLLER COM ENGINE
# ============================================================================

# No seu engine/lance_engine.py:

from core.emergency_control import EmergencyController

class ExecutorLances:
    def __init__(self, page, emergency_controller):
        self.page = page
        self.emergency_controller = emergency_controller
    
    async def executar_lance(self, valor: float, item_id: str):
        # Verificar se pode executar
        if not self.emergency_controller.pode_executar():
            logger.warning(
                f"Robô não pode executar: {self.emergency_controller.obter_estado()['motivo_parada']}"
            )
            return {'sucesso': False, 'mensagem': 'Robô pausado'}
        
        # Continua execução normal...

# ============================================================================
# 3. INTEGRAR HUMANIZER COM EXECUTOR
# ============================================================================

# No seu engine/lance_engine.py:

from core.humanizer import HumanSimulator

class ExecutorLances:
    def __init__(self, page):
        self.page = page
        self.human = HumanSimulator(page)
    
    async def executar_lance(self, valor: float, item_id: str):
        try:
            # Move mouse naturalmente
            await self.human.clicar_naturalista("#btn-enviar-lance")
            
            # Digita com delays
            await self.human.digitar_naturalista(str(valor), "input#valor-lance")
            
            # Clica em enviar com hesitação
            await self.human.delay_humano(0.5, 1.0)
            await self.human.clicar_naturalista("button[type='submit']")
            
            return {'sucesso': True, 'mensagem': 'Lance enviado'}

# ============================================================================
# 4. INICIAR HEARTBEAT NA APLICAÇÃO FLASK
# ============================================================================

# No seu app/main.py:

from core.heartbeat import HeartbeatMonitor, AlertaManager
import asyncio

# Instância global
monitor_saude = HeartbeatMonitor(intervalo_segundos=30)
alertas = AlertaManager()

@app.route('/api/robos/<int:robo_id>/iniciar', methods=['POST'])
def iniciar_robo(robo_id):
    user_id = session.get('user_id')
    robo = DatabaseManager.obter_robo(robo_id)
    
    if not robo or robo.usuario_id != user_id:
        return jsonify({'success': False}), 404
    
    # Inicia heartbeat em thread separada
    async def rodar_heartbeat():
        async def on_heartbeat(dados):
            socketio.emit('heartbeat', dados, room=str(user_id))
        
        async def on_status_change(dados):
            if dados['novo_status'] == 'offline':
                await alertas.enviar_alerta(
                    "Robô Offline",
                    f"Robô {robo.numero_item} perdeu conexão!",
                    severity="critical"
                )
        
        monitor_saude.registrar_callback_heartbeat(on_heartbeat)
        monitor_saude.registrar_callback_mudanca_status(on_status_change)
        
        await monitor_saude.iniciar()
    
    thread = Thread(target=lambda: asyncio.run(rodar_heartbeat()))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True})

# ============================================================================
# 5. USAR BANCO DE DADOS NO DASHBOARD
# ============================================================================

# No seu templates/dashboard.html:

<!-- Adicionar após conectar WebSocket -->
<script>
socket.on('log_evento', function(evento) {
    // Novo log em tempo real
    const linha = `
        [${evento.timestamp}] 
        <span class="badge badge-${evento.level.toLowerCase()}">
            ${evento.level}
        </span>
        ${evento.mensagem}
    `;
    document.getElementById('console-logs').innerHTML += linha + '<br>';
});

socket.on('heartbeat', function(dados) {
    // Atualizar status
    document.getElementById('status-saude').textContent = dados.status;
    document.getElementById('metricas-lances').textContent = 
        dados.metricas.lances_enviados;
});
</script>

# ============================================================================
# 6. MÚLTIPLOS USUÁRIOS - ISOLAMENTO
# ============================================================================

# No seu app/main.py:

@app.before_request
def validar_autenticacao():
    """Validar usuário antes de cada request"""
    # Implement seu sistema de autenticação
    # Por exemplo, JWT tokens:
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token and request.path not in ['/login', '/health']:
        return jsonify({'error': 'Não autenticado'}), 401
    
    # Decodificar token e salvar em session
    # user_id = decode_jwt(token)
    # session['user_id'] = user_id

# ============================================================================
# 7. RODAR MÚLTIPLOS ROBÔS SIMULTANEAMENTE
# ============================================================================

# Criar arquivo: workers.py

import asyncio
from robo_main import RoboLances

async def rodar_multiplos_robos():
    robos = DatabaseManager.listar_robos_ativos(usuario_id=1)
    
    # Inicia todos os robôs em paralelo
    tarefas = [
        RoboLances(robo.to_dict()).inicializar(robo.url_item)
        for robo in robos
    ]
    
    resultados = await asyncio.gather(*tarefas)
    return resultados

# ============================================================================
# 8. TESTES DE INTEGRAÇÃO
# ============================================================================

# Criar arquivo: tests/test_integracao.py

import pytest
from app.main import app, db
from core.database import DatabaseManager, Usuario

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def test_criar_usuario(client):
    """Testa criação de usuário"""
    usuario = DatabaseManager.criar_usuario(
        "Test User",
        "test@example.com",
        "hash123"
    )
    assert usuario.id is not None
    assert usuario.email == "test@example.com"

def test_criar_robo(client):
    """Testa criação de robô"""
    usuario = DatabaseManager.criar_usuario(
        "Test",
        "test@test.com",
        "hash"
    )
    
    robo = DatabaseManager.criar_robo(usuario.id, {
        'numero_item': '001',
        'descricao': 'Test',
        'valor_minimo': 1000.00
    })
    
    assert robo.usuario_id == usuario.id
    assert robo.numero_item == '001'

# ============================================================================
# 9. CONFIGURAR ALERTAS VIA TELEGRAM (OPCIONAL)
# ============================================================================

# No seu .env:

TELEGRAM_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui

# No seu core/heartbeat.py:

import requests

async def enviar_telegram(self, mensagem: str):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    requests.post(url, json={
        'chat_id': chat_id,
        'text': mensagem,
        'parse_mode': 'HTML'
    })

# ============================================================================
# 10. DEPLOY EM PRODUÇÃO
# ============================================================================

# Criar arquivo: docker-compose.yml

version: '3.8'

services:
  flask:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/compras_bot
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=compras_bot
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
  
  redis:
    image: redis:7
  
  celery:
    build: .
    command: celery -A tasks worker --loglevel=info
    depends_on:
      - redis

# Criar arquivo: Dockerfile

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

COPY . .

CMD ["python3", "run.py"]

# ============================================================================
# PRÓXIMOS PASSOS
# ============================================================================

"""
1. ✅ Implementar autenticação JWT (login/logout)
2. ✅ Ajustar seletores CSS do portal real
3. ✅ Testar com dados simulados
4. ✅ Configurar banco de dados produção (PostgreSQL)
5. ✅ Configurar alertas (Telegram/Email)
6. ✅ Deploy em servidor Linux
7. ✅ SSL/TLS para HTTPS
8. ✅ Monitoramento com Prometheus/Grafana
9. ✅ Backup automático de dados
10. ✅ Rate limiting e proteção contra abuse
"""
