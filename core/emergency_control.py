"""
Sistema de Controle de Emergência (Panic Button)
Permite parar robô instantaneamente quando algo der errado
"""

import threading
from typing import Callable, Dict
from datetime import datetime
from enum import Enum


class ControlState(Enum):
    """Estados de controle do robô"""
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class EmergencyController:
    """
    Controlador de emergência que permite:
    - Pausar robô imediatamente
    - Parar robô completamente
    - Retomar operação
    - Modo de erro seguro
    """
    
    def __init__(self):
        self.estado = ControlState.STOPPED
        self.motivo_parada = None
        self.timestamp_parada = None
        
        self.lock = threading.Lock()
        
        # Callbacks
        self.callbacks_mudanca_estado = []
        
        # Histórico de ações
        self.historico = []
    
    def iniciar(self) -> bool:
        """Inicia robô"""
        with self.lock:
            if self.estado in [ControlState.RUNNING]:
                return False  # Já está rodando
            
            self.estado = ControlState.RUNNING
            self.motivo_parada = None
            self._registrar_acao('INICIAR', 'Robô iniciado')
            self._notificar_mudanca_estado()
        
        return True
    
    def pausar(self, motivo: str = None) -> bool:
        """
        Pausa robô (pode ser retomado)
        
        Args:
            motivo: Motivo da pausa
        """
        with self.lock:
            if self.estado == ControlState.PAUSED:
                return False  # Já está pausado
            
            self.estado = ControlState.PAUSED
            self.motivo_parada = motivo or "Pausa manual"
            self.timestamp_parada = datetime.now()
            
            self._registrar_acao('PAUSAR', motivo or "Pausa manual")
            self._notificar_mudanca_estado()
        
        print(f"⏸️  ROBÔ PAUSADO: {motivo or 'Pausa manual'}")
        return True
    
    def parar_emergencia(self, motivo: str = None) -> bool:
        """
        Para robô completamente (PANIC BUTTON)
        Deve ser acionada em caso de erro crítico
        
        Args:
            motivo: Motivo da parada
        """
        with self.lock:
            if self.estado == ControlState.STOPPED:
                return False
            
            self.estado = ControlState.STOPPED
            self.motivo_parada = motivo or "Parada de emergência"
            self.timestamp_parada = datetime.now()
            
            self._registrar_acao('PARADA_EMERGENCIA', motivo or "Parada de emergência")
            self._notificar_mudanca_estado()
        
        print(f"🚨 PARADA DE EMERGÊNCIA: {motivo or 'Sem motivo especificado'}")
        return True
    
    def marcar_erro(self, mensagem_erro: str) -> bool:
        """
        Marca estado como erro (robô falhou)
        
        Args:
            mensagem_erro: Descrição do erro
        """
        with self.lock:
            if self.estado == ControlState.ERROR:
                return False
            
            self.estado = ControlState.ERROR
            self.motivo_parada = mensagem_erro
            self.timestamp_parada = datetime.now()
            
            self._registrar_acao('ERRO', mensagem_erro)
            self._notificar_mudanca_estado()
        
        print(f"❌ ERRO DO ROBÔ: {mensagem_erro}")
        return True
    
    def retomar(self) -> bool:
        """
        Retoma operação (apenas se pausado)
        """
        with self.lock:
            if self.estado != ControlState.PAUSED:
                return False
            
            self.estado = ControlState.RUNNING
            self.motivo_parada = None
            
            self._registrar_acao('RETOMAR', 'Robô retomado')
            self._notificar_mudanca_estado()
        
        print("▶️  ROBÔ RETOMADO")
        return True
    
    def pode_executar(self) -> bool:
        """Verifica se robô pode executar ações"""
        return self.estado == ControlState.RUNNING
    
    def obter_estado(self) -> Dict:
        """Retorna estado atual"""
        with self.lock:
            return {
                'estado': self.estado.value,
                'pode_executar': self.pode_executar(),
                'motivo_parada': self.motivo_parada,
                'timestamp_parada': self.timestamp_parada.isoformat() if self.timestamp_parada else None
            }
    
    def registrar_callback(self, callback: Callable):
        """Registra callback chamado quando estado muda"""
        self.callbacks_mudanca_estado.append(callback)
    
    def _notificar_mudanca_estado(self):
        """Notifica callbacks de mudança de estado"""
        estado_dict = self.obter_estado()
        for callback in self.callbacks_mudanca_estado:
            try:
                callback(estado_dict)
            except Exception as e:
                print(f"❌ Erro em callback: {e}")
    
    def _registrar_acao(self, acao: str, detalhes: str):
        """Registra ação no histórico"""
        self.historico.append({
            'timestamp': datetime.now().isoformat(),
            'acao': acao,
            'detalhes': detalhes
        })
        
        # Limita histórico
        if len(self.historico) > 100:
            self.historico.pop(0)
    
    def obter_historico(self) -> list:
        """Retorna histórico de ações"""
        with self.lock:
            return self.historico.copy()


# ============================================================================
# EXEMPLO DE USO COM CONTEXTO MANAGER
# ============================================================================

class ControlledRobo:
    """Context manager para garantir parada segura do robô"""
    
    def __init__(self, controller: EmergencyController):
        self.controller = controller
    
    def __enter__(self):
        self.controller.iniciar()
        return self.controller
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Houve exceção
            self.controller.marcar_erro(str(exc_val))
        else:
            self.controller.parar_emergencia("Fim normal de execução")
        
        return False  # Re-raise exceptions


def exemplo_uso():
    """Exemplo de uso do controller"""
    
    controller = EmergencyController()
    
    # Callback para mudanças
    def quando_muda(estado):
        print(f"📡 Novo estado: {estado['estado']}")
    
    controller.registrar_callback(quando_muda)
    
    # Simula operação
    print("Iniciando...")
    controller.iniciar()
    
    print("Simulando operação por 5 segundos...")
    import time
    time.sleep(2)
    
    print("Pausando...")
    controller.pausar("Usuário clicou em pausar")
    
    time.sleep(1)
    
    print("Retomando...")
    controller.retomar()
    
    time.sleep(2)
    
    print("Parando emergência...")
    controller.parar_emergencia("Teste de parada de emergência")
    
    print("\n📜 Histórico:")
    for acao in controller.obter_historico():
        print(f"  {acao['timestamp']} | {acao['acao']}: {acao['detalhes']}")


if __name__ == "__main__":
    exemplo_uso()
