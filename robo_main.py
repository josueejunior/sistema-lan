"""
Orquestrador Principal - Integração de todos os módulos
Gerencia todo o ciclo de vida do robô de lances
"""

import asyncio
from pathlib import Path
import sys

# Adiciona diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

from auth.session_manager import SessionManager
from monitor.lance_monitor import MonitorLances
from engine.lance_engine import EngineDecisao, ExecutorLances


class RoboLances:
    """
    Orquestrador principal que integra todos os componentes
    """
    
    def __init__(self, item_config: dict):
        """
        Args:
            item_config: Configuração do item a ser monitorado
        """
        self.item_config = item_config
        self.session_manager = None
        self.monitor = None
        self.engine = None
        self.executor = None
        self.esta_rodando = False
    
    async def inicializar(self, url_disputa: str):
        """
        Inicializa todos os componentes do robô
        
        Args:
            url_disputa: URL da página de disputa do item
        """
        print("🚀 Inicializando Robô de Lances...")
        
        # 1. Gerenciador de Sessão
        self.session_manager = SessionManager("compras_session.json")
        
        # 2. Tenta carregar sessão existente
        context = await self.session_manager.load_existing_session(
            url_disputa,
            headless=True
        )
        
        if context is None:
            print("❌ Sessão inválida. Execute primeiro o login manual.")
            print("   python3 auth/session_manager.py")
            return False
        
        # 3. Inicializa componentes
        self.monitor = MonitorLances(
            self.session_manager.page,
            self.item_config
        )
        
        self.engine = EngineDecisao(self.item_config)
        
        self.executor = ExecutorLances(self.session_manager.page)
        
        # 4. Registra callbacks
        self.monitor.registrar_callback('lance_mudou', self._on_lance_mudou)
        self.monitor.registrar_callback('tempo_critico', self._on_tempo_critico)
        
        print("✅ Robô inicializado com sucesso!")
        return True
    
    async def _on_lance_mudou(self, dados: dict):
        """Callback quando o lance muda"""
        print(f"\n💰 Lance mudou: R$ {dados['lance_anterior']} → R$ {dados['lance_atual']}")
        
        # Avalia se deve dar lance
        await self._avaliar_e_executar(dados['lance_atual'])
    
    async def _on_tempo_critico(self, dados: dict):
        """Callback quando entra em tempo crítico"""
        print(f"\n⏰ TEMPO CRÍTICO! {dados['tempo_restante']}s restantes")
        print(f"   Lance atual: R$ {dados['lance_atual']}")
        
        # Avalia se deve dar lance
        await self._avaliar_e_executar(dados['lance_atual'])
    
    async def _avaliar_e_executar(self, lance_atual: float):
        """
        Avalia situação e executa lance se necessário
        """
        # Pega estado do monitor
        estado = self.monitor.obter_estado_atual()
        
        # Avalia com a engine
        decisao = self.engine.avaliar_lance(
            lance_atual,
            estado['tempo_restante'],
            estado['intervalo_minimo']
        )
        
        print(f"   📊 Decisão: {decisao['motivo']}")
        
        # Se deve dar lance, executa
        if decisao['deve_dar_lance']:
            print(f"   💸 Preparando lance de R$ {decisao['valor_proposto']:.2f}...")
            
            resultado = await self.executor.executar_lance(
                decisao['valor_proposto'],
                self.item_config['numero_item']
            )
            
            if resultado['sucesso']:
                print(f"   ✅ {resultado['mensagem']}")
            else:
                print(f"   ❌ {resultado['mensagem']}")
            
            # Registra decisão
            self.engine.registrar_decisao(decisao)
    
    async def iniciar_monitoramento(self):
        """Inicia o monitoramento contínuo"""
        self.esta_rodando = True
        print("\n👁️  Monitoramento iniciado. Pressione Ctrl+C para parar.\n")
        
        try:
            await self.monitor.iniciar(intervalo_polling=2.0)
        except KeyboardInterrupt:
            print("\n\n🛑 Parando robô...")
            await self.parar()
    
    async def parar(self):
        """Para o robô e libera recursos"""
        self.esta_rodando = False
        
        if self.monitor:
            await self.monitor.parar()
        
        if self.session_manager:
            await self.session_manager.close()
        
        print("👋 Robô finalizado")


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def main():
    """
    Exemplo de uso do robô completo
    """
    # Configuração do item
    item_config = {
        'id': 1,
        'numero_item': '00001',
        'descricao': 'Notebook Dell Latitude 5420',
        'valor_minimo': 3000.00,
        'estrategia': 'sniper',  # ou 'escada'
        'intervalo_lance': 1.0,  # 1%
        'tempo_gatilho': 60  # 60 segundos
    }
    
    # URL da disputa (AJUSTAR conforme portal real)
    url_disputa = "https://www.gov.br/compras/pt-br/acesso-restrito/disputa/item/00001"
    
    # Cria e inicializa robô
    robo = RoboLances(item_config)
    
    sucesso = await robo.inicializar(url_disputa)
    
    if not sucesso:
        return
    
    # Inicia monitoramento
    await robo.iniciar_monitoramento()


if __name__ == "__main__":
    print("="*60)
    print("🤖 ROBÔ DE LANCES AUTOMÁTICOS - COMPRAS.GOV.BR")
    print("="*60)
    print("⚠️  USO RESPONSÁVEL:")
    print("   • Certifique-se de estar em conformidade com o edital")
    print("   • Consulte a IN nº 03/2011 do MPOG")
    print("   • Verifique os Termos de Uso do portal")
    print("="*60)
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Até logo!")
