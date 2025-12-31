"""
Sistema de Logging em Tempo Real com WebSockets
Transmite eventos do robô para o dashboard em tempo real
"""

import asyncio
import json
from datetime import datetime
from typing import Callable, Dict, List
from enum import Enum
import threading


class LogLevel(Enum):
    """Níveis de log"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEvent:
    """Representa um evento de log"""
    
    def __init__(self, level: LogLevel, mensagem: str, dados: Dict = None):
        self.timestamp = datetime.now().isoformat()
        self.level = level
        self.mensagem = mensagem
        self.dados = dados or {}
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'level': self.level.value,
            'mensagem': self.mensagem,
            'dados': self.dados
        }
    
    def to_json(self):
        return json.dumps(self.to_dict())


class LogManager:
    """
    Gerenciador centralizado de logs com suporte a WebSockets
    
    Permite:
    - Registrar eventos com diferentes níveis
    - Notificar clientes conectados em tempo real
    - Armazenar histórico de logs
    - Filtrar por nível e usuário
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Args:
            max_history: Número máximo de logs a manter em memória
        """
        self.max_history = max_history
        self.historico = []
        self.subscribers: Dict[str, List[Callable]] = {}  # user_id -> callbacks
        self.lock = threading.Lock()
    
    def registrar_evento(
        self,
        level: LogLevel,
        mensagem: str,
        user_id: str = "global",
        dados: Dict = None
    ):
        """
        Registra um evento de log e notifica subscribers
        
        Args:
            level: Nível do log
            mensagem: Mensagem do log
            user_id: ID do usuário (para filtrar subscribers)
            dados: Dados adicionais
        """
        evento = LogEvent(level, mensagem, dados)
        
        with self.lock:
            # Adiciona ao histórico
            self.historico.append(evento.to_dict())
            
            # Limita histórico
            if len(self.historico) > self.max_history:
                self.historico.pop(0)
        
        # Notifica subscribers
        self._notificar(user_id, evento)
        
        # Log console
        self._print_console(evento)
    
    def debug(self, msg: str, user_id: str = "global", dados: Dict = None):
        self.registrar_evento(LogLevel.DEBUG, msg, user_id, dados)
    
    def info(self, msg: str, user_id: str = "global", dados: Dict = None):
        self.registrar_evento(LogLevel.INFO, msg, user_id, dados)
    
    def warning(self, msg: str, user_id: str = "global", dados: Dict = None):
        self.registrar_evento(LogLevel.WARNING, msg, user_id, dados)
    
    def error(self, msg: str, user_id: str = "global", dados: Dict = None):
        self.registrar_evento(LogLevel.ERROR, msg, user_id, dados)
    
    def critical(self, msg: str, user_id: str = "global", dados: Dict = None):
        self.registrar_evento(LogLevel.CRITICAL, msg, user_id, dados)
    
    def subscribe(self, user_id: str, callback: Callable):
        """
        Registra callback para receber eventos em tempo real
        
        Args:
            user_id: ID do usuário
            callback: Função que será chamada com o LogEvent
        """
        if user_id not in self.subscribers:
            self.subscribers[user_id] = []
        
        self.subscribers[user_id].append(callback)
    
    def unsubscribe(self, user_id: str, callback: Callable):
        """Remove callback"""
        if user_id in self.subscribers:
            self.subscribers[user_id].remove(callback)
    
    def _notificar(self, user_id: str, evento: LogEvent):
        """Notifica todos os subscribers"""
        # Notifica usuário específico
        if user_id in self.subscribers:
            for callback in self.subscribers[user_id]:
                try:
                    callback(evento)
                except Exception as e:
                    print(f"❌ Erro ao notificar subscriber: {e}")
        
        # Notifica 'global' também (se não for global)
        if user_id != "global" and "global" in self.subscribers:
            for callback in self.subscribers["global"]:
                try:
                    callback(evento)
                except Exception as e:
                    print(f"❌ Erro ao notificar global subscriber: {e}")
    
    def _print_console(self, evento: LogEvent):
        """Imprime log no console com cores"""
        cores = {
            LogLevel.DEBUG: '\033[36m',      # Ciano
            LogLevel.INFO: '\033[32m',       # Verde
            LogLevel.WARNING: '\033[33m',    # Amarelo
            LogLevel.ERROR: '\033[31m',      # Vermelho
            LogLevel.CRITICAL: '\033[41m'    # Fundo vermelho
        }
        reset = '\033[0m'
        
        cor = cores.get(evento.level, '')
        print(f"{cor}[{evento.timestamp}] {evento.level.value}: {evento.mensagem}{reset}")
    
    def obter_historico(self, user_id: str = None, nivel_minimo: LogLevel = None) -> List[Dict]:
        """
        Retorna histórico filtrado
        
        Args:
            user_id: Filtrar por usuário (não implementado aqui)
            nivel_minimo: Filtrar por nível mínimo
        """
        with self.lock:
            historico = self.historico.copy()
        
        if nivel_minimo:
            niveis_incluir = [
                LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING,
                LogLevel.ERROR, LogLevel.CRITICAL
            ]
            indice_minimo = niveis_incluir.index(nivel_minimo)
            historico = [
                log for log in historico
                if niveis_incluir.index(LogLevel[log['level']]) >= indice_minimo
            ]
        
        return historico
    
    def limpar_historico(self):
        """Limpa o histórico"""
        with self.lock:
            self.historico.clear()


# Instância global (singleton)
logger = LogManager()


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

def exemplo_uso():
    """Exemplo de uso do logger"""
    
    # Registra eventos
    logger.info("Iniciando sistema", user_id="usuario_1")
    logger.debug("Debug: Conectando ao navegador", user_id="usuario_1", dados={
        'url': 'https://www.gov.br/compras'
    })
    logger.warning("Aviso: Próximo ao tempo crítico", user_id="usuario_1", dados={
        'tempo_restante': 30,
        'lance_atual': 5000.00
    })
    logger.error("Erro ao enviar lance", user_id="usuario_1", dados={
        'motivo': 'Lance rejeitado',
        'erro': 'Intervalo mínimo não respeitado'
    })
    
    # Subscriber que recebe eventos em tempo real
    def my_callback(evento: LogEvent):
        print(f"📥 Evento recebido: {evento.mensagem}")
    
    logger.subscribe("usuario_1", my_callback)
    logger.info("Evento que será capturado", user_id="usuario_1")
    
    # Histórico
    print("\n📜 Histórico de logs:")
    for log in logger.obter_historico(nivel_minimo=LogLevel.DEBUG):
        print(f"  {log['timestamp']} [{log['level']}] {log['mensagem']}")


if __name__ == "__main__":
    exemplo_uso()
