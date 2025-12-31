"""
Sistema de Logging em Tempo Real via WebSocket
Permite que o operador acompanhe tudo que o robô está fazendo
"""

import asyncio
import logging
from datetime import datetime
from typing import Set, Callable
from enum import Enum


class LogLevel(Enum):
    """Níveis de log"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LoggerRealtime:
    """
    Logger com suporte a WebSocket para logs em tempo real
    """
    
    def __init__(self, max_logs_buffer: int = 500):
        """
        Args:
            max_logs_buffer: Máximo de logs mantidos em memória
        """
        self.logs: list = []
        self.max_logs = max_logs_buffer
        self.conexoes_websocket: Set[Callable] = set()
        self.logger = logging.getLogger('robo-lances')
    
    def adicionar_conexao_websocket(self, send_callback: Callable):
        """
        Registra nova conexão WebSocket
        
        Args:
            send_callback: Função para enviar dados ao cliente
        """
        self.conexoes_websocket.add(send_callback)
    
    def remover_conexao_websocket(self, send_callback: Callable):
        """Remove conexão WebSocket"""
        self.conexoes_websocket.discard(send_callback)
    
    async def _broadcast(self, mensagem: dict):
        """Envia mensagem para todas as conexões WebSocket"""
        if not self.conexoes_websocket:
            return
        
        tasks = []
        for callback in list(self.conexoes_websocket):
            try:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(mensagem))
            except Exception as e:
                self.logger.error(f"Erro ao enviar WebSocket: {e}")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _registrar_log(
        self,
        mensagem: str,
        nivel: LogLevel,
        dados_extras: dict = None
    ):
        """Registra e transmite log"""
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'nivel': nivel.value,
            'mensagem': mensagem,
            'dados': dados_extras or {}
        }
        
        # Adiciona ao buffer
        self.logs.append(log_entry)
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)
        
        # Transmite via WebSocket
        await self._broadcast(log_entry)
        
        # Log local também
        self.logger.log(
            getattr(logging, nivel.name),
            mensagem
        )
    
    # Métodos de conveniência
    async def debug(self, msg: str, dados: dict = None):
        await self._registrar_log(msg, LogLevel.DEBUG, dados)
    
    async def info(self, msg: str, dados: dict = None):
        await self._registrar_log(msg, LogLevel.INFO, dados)
    
    async def warning(self, msg: str, dados: dict = None):
        await self._registrar_log(msg, LogLevel.WARNING, dados)
    
    async def error(self, msg: str, dados: dict = None):
        await self._registrar_log(msg, LogLevel.ERROR, dados)
    
    async def critical(self, msg: str, dados: dict = None):
        await self._registrar_log(msg, LogLevel.CRITICAL, dados)
    
    def obter_ultimos_logs(self, quantidade: int = 100) -> list:
        """Retorna os últimos N logs"""
        return self.logs[-quantidade:]
    
    def limpar_logs(self):
        """Limpa o buffer de logs"""
        self.logs.clear()


class LogContexto:
    """
    Context manager para logar operações com contexto
    """
    
    def __init__(self, logger: LoggerRealtime, titulo: str):
        self.logger = logger
        self.titulo = titulo
        self.tempo_inicio = None
    
    async def __aenter__(self):
        self.tempo_inicio = datetime.now()
        await self.logger.info(f"🔵 INICIANDO: {self.titulo}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        tempo_decorrido = (datetime.now() - self.tempo_inicio).total_seconds()
        
        if exc_type:
            await self.logger.error(
                f"🔴 ERRO em {self.titulo}: {exc_val}",
                {'tempo_segundos': tempo_decorrido}
            )
        else:
            await self.logger.info(
                f"🟢 CONCLUÍDO: {self.titulo}",
                {'tempo_segundos': f"{tempo_decorrido:.2f}"}
            )


# ============================================================================
# INTEGRAÇÃO COM MONITOR DE LANCES
# ============================================================================

class MonitorComLogs:
    """
    Extende MonitorLances com logging em tempo real
    """
    
    def __init__(self, monitor, logger_realtime: LoggerRealtime):
        self.monitor = monitor
        self.logger = logger_realtime
    
    async def monitorar_com_logs(self, intervalo_polling: float = 2.0):
        """Inicia monitoramento com logs em tempo real"""
        
        self.monitor.esta_monitorando = True
        await self.logger.info(
            f"👁️  Monitor iniciado para item {self.monitor.item_config['numero_item']}"
        )
        
        while self.monitor.esta_monitorando:
            try:
                # Verifica página
                await self.monitor._verificar_pagina()
                
                # Registra estado
                estado = self.monitor.obter_estado_atual()
                
                await self.logger.debug(
                    f"Lance monitorado: {self.monitor.item_config['numero_item']}",
                    {
                        'lance_atual': estado['ultimo_lance'],
                        'tempo_restante': estado['tempo_restante'],
                        'intervalo_minimo': estado['intervalo_minimo']
                    }
                )
                
                # Aguarda
                import random
                tempo_espera = intervalo_polling + random.uniform(-0.5, 0.5)
                await asyncio.sleep(max(1.0, tempo_espera))
            
            except Exception as e:
                await self.logger.error(
                    f"Erro no monitoramento do item {self.monitor.item_config['numero_item']}",
                    {'erro': str(e)}
                )
                await asyncio.sleep(5)


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def exemplo_logs():
    """Exemplo de uso do logger em tempo real"""
    
    logger = LoggerRealtime()
    
    # Simula WebSocket (em produção seria com Flask-SocketIO)
    async def enviar_para_cliente(msg):
        print(f"📤 [WebSocket] {msg}")
    
    logger.adicionar_conexao_websocket(enviar_para_cliente)
    
    # Simula operações
    async with LogContexto(logger, "Conectar ao portal"):
        await asyncio.sleep(1)
        await logger.info("Navegando para URL...")
        await asyncio.sleep(0.5)
    
    async with LogContexto(logger, "Monitorar item 00001"):
        await logger.info("Lance atual: R$ 45.000", {'lance': 45000})
        await asyncio.sleep(0.5)
        await logger.info("Lance mudou!", {'novo_lance': 44500})
    
    # Retorna últimos logs
    print("\n📋 Últimos logs:")
    for log in logger.obter_ultimos_logs(5):
        print(f"  [{log['nivel'].upper()}] {log['mensagem']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(exemplo_logs())
