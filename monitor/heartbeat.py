"""
Heartbeat Monitor - Sistema de Monitoramento de Disponibilidade
Envia sinais periódicos confirmando que o robô está vivo e operacional
"""

import asyncio
import aiohttp
from datetime import datetime
from typing import Optional, Callable, List
import logging

logger = logging.getLogger(__name__)


class HeartbeatMonitor:
    """
    Monitora saúde do sistema e envia notificações periódicas
    
    Suporta múltiplos canais:
    - Webhook (Discord, Slack, etc)
    - Email
    - SMS (via serviço externo)
    - Arquivo de log local
    """
    
    def __init__(self, intervalo_segundos: int = 30):
        """
        Args:
            intervalo_segundos: Intervalo entre heartbeats (padrão 30s)
        """
        self.intervalo = intervalo_segundos
        self.esta_monitorando = False
        self.callbacks: List[Callable] = []
        self.ultima_verificacao = None
        self.status_atual = {
            'vivo': True,
            'itens_ativos': 0,
            'lances_executados': 0,
            'ultimos_erros': [],
            'uptime_segundos': 0
        }
        self.tempo_inicio = datetime.now()
    
    def registrar_callback(self, callback: Callable):
        """
        Registra função a ser chamada em cada heartbeat
        
        Args:
            callback: async def callback(status_dict)
        """
        self.callbacks.append(callback)
    
    async def iniciar(self):
        """Inicia o monitor de heartbeat"""
        self.esta_monitorando = True
        print("❤️  Heartbeat Monitor iniciado")
        
        while self.esta_monitorando:
            try:
                # Atualiza status
                self._atualizar_status()
                
                # Notifica callbacks
                await self._notificar_callbacks()
                
                # Log local
                self._log_heartbeat()
                
                # Aguarda intervalo
                await asyncio.sleep(self.intervalo)
                
            except Exception as e:
                logger.error(f"❌ Erro no heartbeat: {e}")
                self.status_atual['ultimos_erros'].append(str(e))
                await asyncio.sleep(5)  # Aguarda antes de tentar novamente
    
    async def parar(self):
        """Para o monitor"""
        self.esta_monitorando = False
        print("🛑 Heartbeat Monitor parado")
    
    def _atualizar_status(self):
        """Atualiza informações de status do sistema"""
        tempo_decorrido = (datetime.now() - self.tempo_inicio).total_seconds()
        self.status_atual['uptime_segundos'] = int(tempo_decorrido)
        self.ultima_verificacao = datetime.now().isoformat()
        
        # Mantém apenas os 5 últimos erros
        if len(self.status_atual['ultimos_erros']) > 5:
            self.status_atual['ultimos_erros'].pop(0)
    
    async def _notificar_callbacks(self):
        """Executa todos os callbacks registrados"""
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self.status_atual)
                else:
                    callback(self.status_atual)
            except Exception as e:
                logger.error(f"❌ Erro ao executar callback: {e}")
    
    def _log_heartbeat(self):
        """Log local do heartbeat"""
        logger.info(
            f"❤️  Heartbeat | Itens: {self.status_atual['itens_ativos']} | "
            f"Lances: {self.status_atual['lances_executados']} | "
            f"Uptime: {self._formatar_uptime()} | "
            f"Erros: {len(self.status_atual['ultimos_erros'])}"
        )
    
    @staticmethod
    def _formatar_uptime() -> str:
        """Formata uptime em formato legível"""
        uptime = int((datetime.now() - datetime.now()).total_seconds())
        horas = uptime // 3600
        minutos = (uptime % 3600) // 60
        segundos = uptime % 60
        return f"{horas}h {minutos}m {segundos}s"
    
    def atualizar_itens_ativos(self, quantidade: int):
        """Atualiza quantidade de itens monitorados"""
        self.status_atual['itens_ativos'] = quantidade
    
    def registrar_lance(self):
        """Registra que um lance foi executado"""
        self.status_atual['lances_executados'] += 1
    
    def registrar_erro(self, mensagem_erro: str):
        """Registra um erro"""
        self.status_atual['ultimos_erros'].append(mensagem_erro)
        logger.error(f"❌ Erro registrado: {mensagem_erro}")
    
    def obter_status(self) -> dict:
        """Retorna status atual"""
        return {
            **self.status_atual,
            'timestamp': self.ultima_verificacao
        }


class NotificadorHeartbeat:
    """
    Envia notificações de heartbeat via múltiplos canais
    """
    
    def __init__(self):
        self.webhook_discord = None
        self.webhook_slack = None
        self.email_destinatarios = []
    
    def configurar_discord(self, webhook_url: str):
        """
        Configura notificação via Discord Webhook
        
        Args:
            webhook_url: URL do webhook do Discord
        """
        self.webhook_discord = webhook_url
    
    def configurar_slack(self, webhook_url: str):
        """
        Configura notificação via Slack Webhook
        
        Args:
            webhook_url: URL do webhook do Slack
        """
        self.webhook_slack = webhook_url
    
    def configurar_email(self, destinatarios: list):
        """
        Configura notificação via Email
        
        Args:
            destinatarios: Lista de emails
        """
        self.email_destinatarios = destinatarios
    
    async def notificar(self, status: dict):
        """
        Envia notificação via canais configurados
        
        Args:
            status: Dicionário com status do sistema
        """
        # Discord
        if self.webhook_discord:
            await self._notificar_discord(status)
        
        # Slack
        if self.webhook_slack:
            await self._notificar_slack(status)
        
        # Email (apenas em caso de erro crítico)
        if self.email_destinatarios and status['ultimos_erros']:
            await self._notificar_email(status)
    
    async def _notificar_discord(self, status: dict):
        """Envia notificação para Discord"""
        try:
            embed = {
                "title": "❤️ Heartbeat - Robô de Lances",
                "color": 3066993,  # Verde
                "fields": [
                    {"name": "Status", "value": "✅ Vivo", "inline": True},
                    {"name": "Itens Ativos", "value": str(status['itens_ativos']), "inline": True},
                    {"name": "Lances Executados", "value": str(status['lances_executados']), "inline": True},
                    {"name": "Uptime", "value": self._format_uptime(status['uptime_segundos']), "inline": True},
                    {
                        "name": "Últimos Erros",
                        "value": "\n".join(status['ultimos_erros'][-3:]) if status['ultimos_erros'] else "Nenhum",
                        "inline": False
                    }
                ],
                "timestamp": status['timestamp']
            }
            
            async with aiohttp.ClientSession() as session:
                await session.post(
                    self.webhook_discord,
                    json={"embeds": [embed]}
                )
                logger.info("✅ Notificação Discord enviada")
        
        except Exception as e:
            logger.error(f"❌ Erro ao notificar Discord: {e}")
    
    async def _notificar_slack(self, status: dict):
        """Envia notificação para Slack"""
        try:
            mensagem = f"""
🤖 *Robô de Lances - Heartbeat*
✅ Status: Vivo
📊 Itens Ativos: {status['itens_ativos']}
💰 Lances Executados: {status['lances_executados']}
⏱️ Uptime: {self._format_uptime(status['uptime_segundos'])}
⚠️ Erros Recentes: {len(status['ultimos_erros'])}
            """
            
            async with aiohttp.ClientSession() as session:
                await session.post(
                    self.webhook_slack,
                    json={"text": mensagem}
                )
                logger.info("✅ Notificação Slack enviada")
        
        except Exception as e:
            logger.error(f"❌ Erro ao notificar Slack: {e}")
    
    async def _notificar_email(self, status: dict):
        """Envia notificação por Email (apenas em caso de erro)"""
        # TODO: Integrar com serviço de email (SendGrid, AWS SES, etc)
        logger.info("📧 Notificação de email configurada (implementar integração)")
    
    @staticmethod
    def _format_uptime(segundos: int) -> str:
        """Formata uptime em formato legível"""
        horas = segundos // 3600
        minutos = (segundos % 3600) // 60
        segs = segundos % 60
        return f"{horas}h {minutos}m {segs}s"


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def exemplo_heartbeat():
    """Exemplo de como usar o heartbeat"""
    
    # Cria monitor
    monitor = HeartbeatMonitor(intervalo_segundos=30)
    
    # Cria notificador
    notificador = NotificadorHeartbeat()
    
    # Configura Discord (obtenha webhook em Discord)
    # notificador.configurar_discord("https://discordapp.com/api/webhooks/...")
    
    # Registra callback
    async def callback_heartbeat(status):
        print(f"💓 Heartbeat enviado: {status}")
    
    monitor.registrar_callback(callback_heartbeat)
    monitor.registrar_callback(notificador.notificar)
    
    # Simula operação
    try:
        monitor.atualizar_itens_ativos(2)
        monitor.registrar_lance()
        
        # Roda heartbeat por 60 segundos
        await asyncio.wait_for(monitor.iniciar(), timeout=60)
    
    except asyncio.TimeoutError:
        print("\n⏱️ Tempo limite atingido")
    
    finally:
        await monitor.parar()


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    asyncio.run(exemplo_heartbeat())
