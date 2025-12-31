"""
Gerenciador de Múltiplos Itens
Coordena monitoramento e lances de vários itens simultaneamente
"""

import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ItemTaskStatus:
    """Status de uma tarefa de item"""
    item_id: str
    ativa: bool = False
    em_execucao: bool = False
    task: Optional[asyncio.Task] = None
    ultima_atualizacao: Optional[str] = None
    erros: List[str] = field(default_factory=list)


class GerenciadorItens:
    """
    Gerencia monitoramento e execução de múltiplos itens simultâneos
    
    Permite:
    - Adicionar/remover itens dinamicamente
    - Iniciar/pausar monitoramento por item
    - Coordenar lances entre itens (prioridades)
    - Gerenciar recursos (browsers, conexões)
    """
    
    def __init__(self, max_itens_simultaneos: int = 5):
        """
        Args:
            max_itens_simultaneos: Máximo de itens monitorados ao mesmo tempo
        """
        self.itens: Dict[str, ItemTaskStatus] = {}
        self.tarefas: Dict[str, asyncio.Task] = {}
        self.max_itens = max_itens_simultaneos
        self.callbacks_mudanca = []
        self.parado = False
    
    def adicionar_item(self, item_id: str) -> bool:
        """
        Adiciona um item para monitoramento
        
        Args:
            item_id: Identificador único do item
            
        Returns:
            True se adicionado com sucesso, False se limite atingido
        """
        if item_id in self.itens:
            logger.warning(f"Item {item_id} já está sendo monitorado")
            return False
        
        if len(self.itens) >= self.max_itens:
            logger.error(
                f"Limite de {self.max_itens} itens simultaneamente atingido"
            )
            return False
        
        self.itens[item_id] = ItemTaskStatus(item_id=item_id)
        logger.info(f"✅ Item {item_id} adicionado ao gerenciador")
        return True
    
    def remover_item(self, item_id: str) -> bool:
        """
        Remove item do monitoramento
        
        Args:
            item_id: Identificador do item
            
        Returns:
            True se removido com sucesso
        """
        if item_id not in self.itens:
            return False
        
        # Para a tarefa se estiver rodando
        if self.itens[item_id].task and not self.itens[item_id].task.done():
            self.itens[item_id].task.cancel()
        
        del self.itens[item_id]
        logger.info(f"❌ Item {item_id} removido do gerenciador")
        return True
    
    async def iniciar_item(
        self,
        item_id: str,
        funcao_monitora: callable
    ) -> bool:
        """
        Inicia monitoramento de um item
        
        Args:
            item_id: Identificador do item
            funcao_monitora: Função async para monitorar (deve aceitar item_id)
            
        Returns:
            True se iniciado com sucesso
        """
        if item_id not in self.itens:
            logger.error(f"Item {item_id} não existe")
            return False
        
        if self.itens[item_id].ativa:
            logger.warning(f"Item {item_id} já está ativo")
            return False
        
        # Cria tarefa
        self.itens[item_id].ativa = True
        self.itens[item_id].em_execucao = True
        
        async def monitor_com_tratamento():
            try:
                await funcao_monitora(item_id)
            except asyncio.CancelledError:
                logger.info(f"Monitoramento de {item_id} cancelado")
            except Exception as e:
                logger.error(f"Erro no item {item_id}: {e}")
                self.itens[item_id].erros.append(str(e))
                self.itens[item_id].ativa = False
            finally:
                self.itens[item_id].em_execucao = False
        
        self.itens[item_id].task = asyncio.create_task(
            monitor_com_tratamento()
        )
        
        logger.info(f"▶️  Item {item_id} iniciado")
        return True
    
    async def pausar_item(self, item_id: str) -> bool:
        """
        Pausa monitoramento de um item
        
        Args:
            item_id: Identificador do item
            
        Returns:
            True se pausado com sucesso
        """
        if item_id not in self.itens:
            return False
        
        if not self.itens[item_id].ativa:
            return False
        
        self.itens[item_id].ativa = False
        
        if self.itens[item_id].task and not self.itens[item_id].task.done():
            self.itens[item_id].task.cancel()
            try:
                await self.itens[item_id].task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"⏸️  Item {item_id} pausado")
        return True
    
    async def pausar_todos(self):
        """Para todos os itens"""
        for item_id in list(self.itens.keys()):
            await self.pausar_item(item_id)
    
    def obter_status_todos(self) -> Dict:
        """Retorna status de todos os itens"""
        return {
            item_id: {
                'ativa': status.ativa,
                'em_execucao': status.em_execucao,
                'ultima_atualizacao': status.ultima_atualizacao,
                'total_erros': len(status.erros)
            }
            for item_id, status in self.itens.items()
        }
    
    def registrar_callback_mudanca(self, callback: callable):
        """
        Registra callback para quando o status de um item mudar
        
        Args:
            callback: async def callback(item_id, novo_status)
        """
        self.callbacks_mudanca.append(callback)
    
    async def _notificar_mudanca(self, item_id: str, novo_status: str):
        """Notifica mudanças de status"""
        for callback in self.callbacks_mudanca:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(item_id, novo_status)
            except Exception as e:
                logger.error(f"Erro ao executar callback: {e}")


class GerenciadorContextoBrowser:
    """
    Gerencia contextos do navegador para múltiplos itens
    
    Pode usar:
    - Uma aba por item
    - Um navegador por item
    - Um pool de navegadores compartilhados
    """
    
    def __init__(self, max_browsers: int = 3):
        """
        Args:
            max_browsers: Máximo de instâncias do navegador simultâneas
        """
        self.max_browsers = max_browsers
        self.browsers_ativos: Dict[str, object] = {}
        self.paginas_por_item: Dict[str, object] = {}
    
    async def obter_pagina(self, item_id: str):
        """
        Obtém uma página/contexto para um item
        
        Implementação real precisaria de Playwright
        """
        # TODO: Implementar com Playwright real
        pass
    
    async def liberar_pagina(self, item_id: str):
        """Libera página de um item"""
        # TODO: Implementar
        pass


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def exemplo_gerenciador():
    """Exemplo de como usar o gerenciador de múltiplos itens"""
    
    gerenciador = GerenciadorItens(max_itens_simultaneos=3)
    
    # Função de monitoramento simulada
    async def monitora_item(item_id: str):
        """Função que seria implementada para cada item"""
        print(f"🔍 Monitorando item {item_id}")
        
        contador = 0
        while True:
            contador += 1
            print(f"  Item {item_id}: tick #{contador}")
            
            if contador > 10:
                break
            
            await asyncio.sleep(1)
    
    # Registra callback
    async def ao_mudar_status(item_id: str, novo_status: str):
        print(f"  📊 Item {item_id} → {novo_status}")
    
    gerenciador.registrar_callback_mudanca(ao_mudar_status)
    
    # Adiciona itens
    gerenciador.adicionar_item("item_001")
    gerenciador.adicionar_item("item_002")
    gerenciador.adicionar_item("item_003")
    
    # Inicia monitoramento
    await gerenciador.iniciar_item("item_001", monitora_item)
    await gerenciador.iniciar_item("item_002", monitora_item)
    
    # Aguarda um pouco
    await asyncio.sleep(5)
    
    # Pausa um item
    await gerenciador.pausar_item("item_001")
    
    # Inicia outro
    await gerenciador.iniciar_item("item_003", monitora_item)
    
    # Aguarda conclusão
    await asyncio.sleep(10)
    
    # Para tudo
    await gerenciador.pausar_todos()
    
    # Exibe status final
    print("\n📋 Status final:")
    for item_id, status in gerenciador.obter_status_todos().items():
        print(f"  {item_id}: {status}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(exemplo_gerenciador())
