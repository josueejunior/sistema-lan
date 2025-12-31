"""
Heartbeat Monitor - Mantém sistema vivo e alerta sobre falhas
Envia sinais a cada 30s confirmando que o robô está operacional
"""

import asyncio
import threading
from datetime import datetime, timedelta
from typing import Callable, Dict, Optional
from enum import Enum


class HealthStatus(Enum):
    """Status de saúde do sistema"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class HeartbeatMonitor:
    """
    Monitor de saúde que emite sinais periódicos (heartbeat)
    
    Características:
    - Verifica saúde a cada intervalo
    - Detecta falhas/timeouts
    - Notifica callbacks quando status muda
    - Pode enviar alertas (email, SMS, Telegram)
    """
    
    def __init__(self, intervalo_segundos: int = 30, timeout_segundos: int = 90):
        """
        Args:
            intervalo_segundos: Intervalo entre heartbeats
            timeout_segundos: Tempo até considerar offline
        """
        self.intervalo = intervalo_segundos
        self.timeout = timeout_segundos
        
        self.ultimo_heartbeat = None
        self.status = HealthStatus.OFFLINE
        self.esta_monitorando = False
        
        self.callbacks_mudanca_status = []
        self.callbacks_heartbeat = []
        
        self.metricas = {
            'lances_enviados': 0,
            'lances_aceitos': 0,
            'lances_rejeitados': 0,
            'erros': 0,
            'cpu_percent': 0,
            'memoria_mb': 0
        }
        
        self.thread_monitor = None
    
    async def iniciar(self):
        """Inicia monitoramento de heartbeat"""
        self.esta_monitorando = True
        print("💓 Heartbeat Monitor iniciado")
        
        while self.esta_monitorando:
            await self._emitir_heartbeat()
            await asyncio.sleep(self.intervalo)
    
    def parar(self):
        """Para o monitoramento"""
        self.esta_monitorando = False
        print("🛑 Heartbeat Monitor parado")
    
    async def _emitir_heartbeat(self):
        """Emite sinal de heartbeat e verifica saúde"""
        self.ultimo_heartbeat = datetime.now()
        
        # Notifica subscribers
        await self._notificar_heartbeat({
            'timestamp': self.ultimo_heartbeat.isoformat(),
            'status': self.status.value,
            'metricas': self.metricas
        })
        
        # Verifica saúde
        novo_status = await self._verificar_saude()
        
        if novo_status != self.status:
            self.status = novo_status
            await self._notificar_mudanca_status(novo_status)
    
    async def _verificar_saude(self) -> HealthStatus:
        """
        Verifica saúde do sistema
        
        Critérios:
        - Último heartbeat < timeout: HEALTHY
        - Última resposta > timeout: OFFLINE
        - Taxa de erro alta: DEGRADED
        """
        if self.ultimo_heartbeat is None:
            return HealthStatus.OFFLINE
        
        tempo_sem_resposta = (datetime.now() - self.ultimo_heartbeat).total_seconds()
        
        if tempo_sem_resposta > self.timeout:
            return HealthStatus.OFFLINE
        
        # Verifica taxa de erro (> 30% = DEGRADED)
        total = self.metricas['lances_aceitos'] + self.metricas['lances_rejeitados']
        if total > 0:
            taxa_rejeicao = self.metricas['lances_rejeitados'] / total
            if taxa_rejeicao > 0.3:
                return HealthStatus.DEGRADED
        
        # Verifica uso de memória (> 500MB = DEGRADED)
        if self.metricas['memoria_mb'] > 500:
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY
    
    def registrar_evento(self, tipo: str, dados: Dict = None):
        """
        Registra evento (lance aceito, rejeitado, erro)
        
        Args:
            tipo: 'lance_aceito', 'lance_rejeitado', 'erro'
            dados: Dados adicionais
        """
        if tipo == 'lance_aceito':
            self.metricas['lances_aceitos'] += 1
            self.metricas['lances_enviados'] += 1
        elif tipo == 'lance_rejeitado':
            self.metricas['lances_rejeitados'] += 1
            self.metricas['lances_enviados'] += 1
        elif tipo == 'erro':
            self.metricas['erros'] += 1
    
    def atualizar_metricas(self, metricas: Dict):
        """Atualiza métricas de sistema (CPU, memória)"""
        self.metricas.update(metricas)
    
    def registrar_callback_heartbeat(self, callback: Callable):
        """Registra callback chamado a cada heartbeat"""
        self.callbacks_heartbeat.append(callback)
    
    def registrar_callback_mudanca_status(self, callback: Callable):
        """Registra callback chamado quando status muda"""
        self.callbacks_mudanca_status.append(callback)
    
    async def _notificar_heartbeat(self, dados: Dict):
        """Notifica callbacks de heartbeat"""
        for callback in self.callbacks_heartbeat:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(dados)
                else:
                    callback(dados)
            except Exception as e:
                print(f"❌ Erro em callback heartbeat: {e}")
    
    async def _notificar_mudanca_status(self, novo_status: HealthStatus):
        """Notifica callbacks de mudança de status"""
        print(f"🚨 Status mudou para: {novo_status.value}")
        
        for callback in self.callbacks_mudanca_status:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback({
                        'novo_status': novo_status.value,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    callback({
                        'novo_status': novo_status.value,
                        'timestamp': datetime.now().isoformat()
                    })
            except Exception as e:
                print(f"❌ Erro em callback de status: {e}")
    
    def obter_status_atual(self) -> Dict:
        """Retorna status atual do sistema"""
        return {
            'status': self.status.value,
            'ultimo_heartbeat': self.ultimo_heartbeat.isoformat() if self.ultimo_heartbeat else None,
            'metricas': self.metricas
        }


class AlertaManager:
    """
    Gerencia envio de alertas (SMS, Email, Telegram)
    Notifica operador quando algo der errado
    """
    
    def __init__(self):
        self.alertas_enviados = []
        self.configuracoes = {
            'telegram_token': None,
            'telegram_chat_id': None,
            'email': None,
            'telefone': None
        }
    
    async def enviar_alerta(self, titulo: str, mensagem: str, severity: str = "warning"):
        """
        Envia alerta por múltiplos canais
        
        Args:
            titulo: Título do alerta
            mensagem: Mensagem do alerta
            severity: 'info', 'warning', 'error', 'critical'
        """
        print(f"\n🚨 ALERTA [{severity.upper()}]")
        print(f"   Título: {titulo}")
        print(f"   Mensagem: {mensagem}")
        
        # TODO: Implementar envio via Telegram, Email, SMS
        # Por enquanto apenas loga
        
        self.alertas_enviados.append({
            'timestamp': datetime.now().isoformat(),
            'titulo': titulo,
            'mensagem': mensagem,
            'severity': severity
        })
    
    async def enviar_telegram(self, mensagem: str):
        """Envia mensagem via Telegram"""
        if not self.configuracoes['telegram_token']:
            print("⚠️  Telegram não configurado")
            return
        
        # import requests
        # url = f"https://api.telegram.org/bot{token}/sendMessage"
        # requests.post(url, json={
        #     'chat_id': self.configuracoes['telegram_chat_id'],
        #     'text': mensagem
        # })
        pass
    
    async def enviar_email(self, assunto: str, corpo: str):
        """Envia email para operador"""
        if not self.configuracoes['email']:
            print("⚠️  Email não configurado")
            return
        
        # import smtplib
        # msg = f"Subject: {assunto}\n\n{corpo}"
        # smtplib.SMTP(...).sendmail(...)
        pass


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def exemplo_heartbeat():
    """Exemplo de uso do heartbeat monitor"""
    
    monitor = HeartbeatMonitor(intervalo_segundos=10, timeout_segundos=30)
    alertas = AlertaManager()
    
    # Registra callbacks
    def on_heartbeat(dados):
        print(f"💓 Heartbeat: {dados['status']} | Lances: {dados['metricas']['lances_enviados']}")
    
    async def on_status_change(dados):
        status = dados['novo_status']
        if status == 'offline':
            await alertas.enviar_alerta(
                "Robô Offline",
                "O robô parou de responder!",
                severity="critical"
            )
    
    monitor.registrar_callback_heartbeat(on_heartbeat)
    monitor.registrar_callback_mudanca_status(on_status_change)
    
    # Simula operação
    async def simular_operacao():
        for i in range(5):
            monitor.registrar_evento('lance_aceito')
            await asyncio.sleep(5)
    
    # Inicia ambos
    await asyncio.gather(
        monitor.iniciar(),
        simular_operacao()
    )


if __name__ == "__main__":
    asyncio.run(exemplo_heartbeat())
