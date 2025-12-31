"""
GUIA DE INTEGRAÇÃO - Sistema Completo
Como integrar todos os módulos avançados
"""

import asyncio
from typing import Dict, List
from datetime import datetime

# Imports dos módulos
from auth.session_manager import SessionManager
from monitor.lance_monitor import MonitorLances
from monitor.heartbeat import HeartbeatMonitor, NotificadorHeartbeat
from monitor.realtime_logger import LoggerRealtime, LogContexto
from engine.lance_engine import EngineDecisao, ExecutorLances
from engine.gerenciador_itens import GerenciadorItens
from engine.pos_lance import OrquestradorPosLance


class RoboLancesAvancado:
    """
    Sistema completo de automação de lances com:
    - Autenticação persistente
    - Monitoramento em tempo real
    - Múltiplos itens simultâneos
    - Logs em tempo real via WebSocket
    - Heartbeat e alertas
    - Pós-lance com inteligência comercial
    """
    
    def __init__(self):
        # Componentes principais
        self.session_manager = None
        self.gerenciador_itens = None
        self.heartbeat = None
        self.logger = LoggerRealtime()
        self.notificador = NotificadorHeartbeat()
        self.orquestrador_pos_lance = OrquestradorPosLance()
        
        # Estado
        self.rodando = False
        self.panico_ativado = False
    
    async def inicializar(self):
        """Inicializa todos os componentes"""
        
        print("🚀 Inicializando Robô Avançado...")
        
        # 1. Carrega sessão
        self.session_manager = SessionManager("compras_session.json")
        context = await self.session_manager.load_existing_session(
            "https://www.gov.br/compras/pt-br"
        )
        
        if not context:
            await self.logger.error("Sessão não carregada. Execute o login manual.")
            return False
        
        # 2. Inicializa gerenciador de itens
        self.gerenciador_itens = GerenciadorItens(max_itens_simultaneos=5)
        
        # 3. Inicializa heartbeat
        self.heartbeat = HeartbeatMonitor(intervalo_segundos=30)
        self.heartbeat.registrar_callback(self._callback_heartbeat)
        
        # 4. Registra callbacks de mudanças
        self.gerenciador_itens.registrar_callback_mudanca(self._ao_mudar_status_item)
        
        # 5. Configura notificador (opcional)
        # self.notificador.configurar_discord("https://discordapp.com/api/webhooks/...")
        
        await self.logger.info("✅ Robô inicializado com sucesso")
        
        return True
    
    async def _callback_heartbeat(self, status: Dict):
        """Callback do heartbeat"""
        await self.logger.debug(
            "❤️  Heartbeat enviado",
            {
                'itens_ativos': status['itens_ativos'],
                'lances_executados': status['lances_executados'],
                'uptime': status['uptime_segundos']
            }
        )
        
        # Notifica via canais configurados
        await self.notificador.notificar(status)
    
    async def _ao_mudar_status_item(self, item_id: str, novo_status: str):
        """Callback quando item muda de status"""
        await self.logger.info(
            f"Item {item_id} → {novo_status}"
        )
    
    async def adicionar_e_monitorar_item(
        self,
        numero_item: str,
        descricao: str,
        valor_minimo: float,
        estrategia: str = 'sniper'
    ):
        """
        Adiciona item e inicia monitoramento
        
        Args:
            numero_item: ID do item
            descricao: Descrição
            valor_minimo: Valor mínimo (hard stop)
            estrategia: 'sniper' ou 'escada'
        """
        
        # Cria configuração
        item_config = {
            'id': numero_item,
            'numero_item': numero_item,
            'descricao': descricao,
            'valor_minimo': valor_minimo,
            'estrategia': estrategia,
            'intervalo_lance': 1.0,
            'tempo_gatilho': 60
        }
        
        # Adiciona ao gerenciador
        self.gerenciador_itens.adicionar_item(numero_item)
        
        # Função de monitoramento para este item
        async def monitora_item(item_id):
            async with LogContexto(self.logger, f"Monitorar item {item_id}"):
                monitor = MonitorLances(self.session_manager.page, item_config)
                engine = EngineDecisao(item_config)
                executor = ExecutorLances(self.session_manager.page, self.logger)
                
                # Registra callbacks
                async def ao_lance_mudar(dados):
                    await self._processar_lance_mudou(
                        dados, engine, executor, monitor
                    )
                
                monitor.registrar_callback('lance_mudou', ao_lance_mudar)
                
                # Inicia monitoramento
                await monitor.iniciar(intervalo_polling=2.0)
        
        # Inicia monitoramento
        await self.gerenciador_itens.iniciar_item(numero_item, monitora_item)
        
        await self.logger.info(f"▶️  Item {numero_item} iniciado")
    
    async def _processar_lance_mudou(self, dados, engine, executor, monitor):
        """Processa mudança de lance"""
        lance_atual = dados['lance_atual']
        estado = monitor.obter_estado_atual()
        
        # Avalia com engine
        decisao = engine.avaliar_lance(
            lance_atual,
            estado['tempo_restante'],
            estado['intervalo_minimo']
        )
        
        await self.logger.info(f"Lance: {decisao['motivo']}")
        
        # Executa se necessário
        if decisao['deve_dar_lance']:
            resultado = await executor.executar_lance(
                decisao['valor_proposto'],
                monitor.item_config['numero_item']
            )
            
            if resultado['sucesso']:
                self.heartbeat.registrar_lance()
                await self.logger.info(
                    f"✅ Lance enviado: R$ {decisao['valor_proposto']:.2f}"
                )
    
    async def ativar_panico(self):
        """Ativa modo pânico - para tudo imediatamente"""
        self.panico_ativado = True
        
        # Para todos os itens
        await self.gerenciador_itens.pausar_todos()
        
        await self.logger.critical("🚨 PÂNICO ATIVADO - TODOS OS ITENS PARADOS")
    
    async def cancelar_panico(self):
        """Cancela modo pânico"""
        self.panico_ativado = False
        
        await self.logger.info("✅ Pânico cancelado - Sistema pronto para retomar")
    
    async def iniciar_heartbeat(self):
        """Inicia monitoramento de saúde do sistema"""
        asyncio.create_task(self.heartbeat.iniciar())
    
    async def parar_tudo(self):
        """Para completamente o robô"""
        await self.logger.info("🛑 Parando robô...")
        
        await self.gerenciador_itens.pausar_todos()
        await self.heartbeat.parar()
        
        if self.session_manager:
            await self.session_manager.close()
        
        await self.logger.info("✅ Robô finalizado")


# ============================================================================
# EXEMPLO DE INTEGRAÇÃO COMPLETA
# ============================================================================

async def exemplo_integracao_completa():
    """
    Demonstração de como usar o sistema completo
    """
    
    print("=" * 70)
    print("🤖 EXEMPLO DE INTEGRAÇÃO COMPLETA - ROBÔ AVANÇADO")
    print("=" * 70)
    print()
    
    # Cria robô
    robo = RoboLancesAvancado()
    
    # Inicializa
    sucesso = await robo.inicializar()
    if not sucesso:
        return
    
    # Inicia heartbeat
    await robo.iniciar_heartbeat()
    
    # Adiciona itens para monitoramento
    itens_exemplo = [
        {
            'numero_item': 'ITEM_001',
            'descricao': 'Notebook Dell Latitude',
            'valor_minimo': 3000.00,
            'estrategia': 'sniper'
        },
        {
            'numero_item': 'ITEM_002',
            'descricao': 'Monitor 27 polegadas',
            'valor_minimo': 1200.00,
            'estrategia': 'escada'
        }
    ]
    
    # Adiciona itens
    for item in itens_exemplo:
        await robo.adicionar_e_monitorar_item(
            item['numero_item'],
            item['descricao'],
            item['valor_minimo'],
            item['estrategia']
        )
        await asyncio.sleep(1)
    
    # Simula operação por 120 segundos
    print("\n⏱️  Robô em operação por 120 segundos...")
    print("Imprensa Ctrl+C para parar\n")
    
    try:
        await asyncio.sleep(120)
    except KeyboardInterrupt:
        print("\n\n⏸️  Parando...")
    finally:
        await robo.parar_tudo()


# ============================================================================
# INTEGRAÇÃO COM FLASK
# ============================================================================

class RoboFlaskBridge:
    """
    Bridge para integrar RoboLancesAvancado com Flask/SocketIO
    """
    
    def __init__(self, socketio_instance):
        self.socketio = socketio_instance
        self.robo = None
    
    async def inicializar(self):
        """Inicializa o robô"""
        self.robo = RoboLancesAvancado()
        
        # Redireciona logs para WebSocket
        async def callback_log(mensagem):
            self.socketio.emit('novo_log', {
                'mensagem': mensagem,
                'timestamp': datetime.now().isoformat()
            })
        
        self.robo.logger.adicionar_conexao_websocket(callback_log)
        
        return await self.robo.inicializar()
    
    async def adicionar_item(self, numero_item, descricao, valor_minimo):
        """Adiciona item via Flask"""
        await self.robo.adicionar_e_monitorar_item(
            numero_item,
            descricao,
            valor_minimo
        )
    
    async def ativar_panico(self):
        """Ativa pânico via Flask"""
        await self.robo.ativar_panico()
    
    async def cancelar_panico(self):
        """Cancela pânico via Flask"""
        await self.robo.cancelar_panico()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("""
    Este é um exemplo de integração completa.
    
    Para usar com Flask:
    
    1. Na aplicação Flask, importe:
       from integracao_completa import RoboFlaskBridge
    
    2. Crie uma instância:
       bridge = RoboFlaskBridge(socketio_instance)
    
    3. Inicialize:
       await bridge.inicializar()
    
    4. Use nas rotas:
       await bridge.adicionar_item(...)
       await bridge.ativar_panico()
    
    Para testar este exemplo:
       python3 integracao_completa.py
    """)
    
    # asyncio.run(exemplo_integracao_completa())
