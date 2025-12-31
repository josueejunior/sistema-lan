"""
Monitor de Lances - Playwright
Monitora página de lances em tempo real e captura informações
"""

import asyncio
from datetime import datetime
from typing import Dict, Optional, Callable
from playwright.async_api import Page, Browser
import random


class MonitorLances:
    """
    Monitora página de lances do Compras.gov.br em tempo real
    
    Responsabilidades:
    - Detectar mudanças no lance atual
    - Capturar tempo restante da disputa
    - Ler intervalo mínimo entre lances
    - Notificar callbacks quando houver mudanças
    """
    
    def __init__(self, page: Page, item_config: Dict):
        """
        Inicializa o monitor
        
        Args:
            page: Página do Playwright já autenticada
            item_config: Configurações do item (id, valor_minimo, estrategia, etc)
        """
        self.page = page
        self.item_config = item_config
        self.esta_monitorando = False
        self.callbacks = {
            'lance_mudou': [],
            'tempo_critico': [],
            'erro': []
        }
        
        # Cache de estado
        self.ultimo_lance = None
        self.tempo_restante = None
        self.intervalo_minimo = None
        
    def registrar_callback(self, evento: str, funcao: Callable):
        """
        Registra função callback para eventos
        
        Eventos disponíveis:
        - lance_mudou: Quando o lance atual muda
        - tempo_critico: Quando entra no tempo de gatilho
        - erro: Quando ocorre erro no monitoramento
        """
        if evento in self.callbacks:
            self.callbacks[evento].append(funcao)
    
    async def iniciar(self, intervalo_polling: float = 2.0):
        """
        Inicia o monitoramento contínuo
        
        Args:
            intervalo_polling: Tempo em segundos entre cada verificação
        """
        self.esta_monitorando = True
        print(f"👁️  Monitor iniciado para item {self.item_config['numero_item']}")
        
        while self.esta_monitorando:
            try:
                await self._verificar_pagina()
                
                # Intervalo com randomização para parecer humano
                tempo_espera = intervalo_polling + random.uniform(-0.5, 0.5)
                await asyncio.sleep(max(1.0, tempo_espera))
                
            except Exception as e:
                print(f"❌ Erro no monitoramento: {e}")
                await self._notificar('erro', {'erro': str(e)})
                await asyncio.sleep(5)  # Espera maior em caso de erro
    
    async def parar(self):
        """Para o monitoramento"""
        self.esta_monitorando = False
        print("🛑 Monitor parado")
    
    async def _verificar_pagina(self):
        """
        Verifica estado atual da página e extrai informações
        
        IMPORTANTE: Seletores CSS/XPath devem ser ajustados conforme
        a estrutura real do portal Compras.gov.br
        """
        try:
            # ============================================================
            # ATENÇÃO: AJUSTAR SELETORES CONFORME PORTAL REAL
            # ============================================================
            
            # Exemplo 1: Capturar lance atual
            lance_atual = await self._extrair_lance_atual()
            
            # Exemplo 2: Capturar tempo restante
            tempo_restante = await self._extrair_tempo_restante()
            
            # Exemplo 3: Capturar intervalo mínimo (conforme solicitado)
            intervalo_minimo = await self._extrair_intervalo_minimo()
            
            # Verifica se lance mudou
            if lance_atual != self.ultimo_lance:
                await self._notificar('lance_mudou', {
                    'lance_anterior': self.ultimo_lance,
                    'lance_atual': lance_atual,
                    'timestamp': datetime.now().isoformat()
                })
                self.ultimo_lance = lance_atual
            
            # Verifica se está em tempo crítico
            if tempo_restante and tempo_restante <= self.item_config.get('tempo_gatilho', 60):
                await self._notificar('tempo_critico', {
                    'tempo_restante': tempo_restante,
                    'lance_atual': lance_atual
                })
            
            # Atualiza cache
            self.tempo_restante = tempo_restante
            self.intervalo_minimo = intervalo_minimo
            
        except Exception as e:
            raise Exception(f"Erro ao verificar página: {e}")
    
    async def _extrair_lance_atual(self) -> Optional[float]:
        """
        Extrai valor do lance atual da página
        
        AJUSTAR SELETORES conforme HTML real
        """
        try:
            # Opção 1: Por ID/classe específica
            # elemento = await self.page.query_selector('#lance-atual')
            
            # Opção 2: Por texto próximo
            # elemento = await self.page.query_selector('span:has-text("Menor Lance")')
            
            # Opção 3: Por atributo data
            # elemento = await self.page.query_selector('[data-lance-atual]')
            
            # EXEMPLO GENÉRICO (ajustar):
            elemento = await self.page.query_selector('.lance-valor, #valor-lance, [data-lance]')
            
            if elemento:
                texto = await elemento.inner_text()
                # Remove formatação (R$, pontos, etc)
                valor_limpo = texto.replace('R$', '').replace('.', '').replace(',', '.').strip()
                return float(valor_limpo)
            
            return None
            
        except Exception as e:
            print(f"⚠️  Erro ao extrair lance: {e}")
            return None
    
    async def _extrair_tempo_restante(self) -> Optional[int]:
        """
        Extrai tempo restante em segundos
        
        AJUSTAR conforme formato do timer do portal
        """
        try:
            # Busca elemento do cronômetro
            # elemento = await self.page.query_selector('.cronometro, #tempo-restante')
            
            # EXEMPLO: Se o formato for "MM:SS" ou "HH:MM:SS"
            # texto = await elemento.inner_text()  # Ex: "05:30"
            # partes = texto.split(':')
            # if len(partes) == 2:
            #     return int(partes[0]) * 60 + int(partes[1])
            
            return None  # Implementar conforme portal real
            
        except Exception as e:
            return None
    
    async def _extrair_intervalo_minimo(self) -> Optional[float]:
        """
        Extrai o intervalo mínimo entre lances definido pelo sistema
        Conforme solicitado pelo Rômulo
        
        Pode ser um valor fixo ou percentual
        """
        try:
            # Busca informação na página
            # elemento = await self.page.query_selector('.intervalo-minimo, #info-disputa')
            
            # EXEMPLO: Se estiver escrito "Intervalo mínimo: R$ 10,00" ou "1%"
            # texto = await elemento.inner_text()
            
            return None  # Implementar conforme portal
            
        except Exception as e:
            return None
    
    async def _notificar(self, evento: str, dados: Dict):
        """Executa callbacks registrados para um evento"""
        if evento in self.callbacks:
            for callback in self.callbacks[evento]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(dados)
                    else:
                        callback(dados)
                except Exception as e:
                    print(f"❌ Erro ao executar callback {evento}: {e}")
    
    def obter_estado_atual(self) -> Dict:
        """Retorna estado atual do monitoramento"""
        return {
            'monitorando': self.esta_monitorando,
            'ultimo_lance': self.ultimo_lance,
            'tempo_restante': self.tempo_restante,
            'intervalo_minimo': self.intervalo_minimo,
            'item': self.item_config['numero_item']
        }


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def exemplo_monitor():
    """Exemplo de como usar o monitor"""
    from playwright.async_api import async_playwright
    
    # Configuração do item
    item_config = {
        'id': 1,
        'numero_item': '00001',
        'descricao': 'Notebook Dell',
        'valor_minimo': 3000.00,
        'estrategia': 'sniper',
        'tempo_gatilho': 60
    }
    
    # Inicializa Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Carrega sessão salva (exemplo)
        context = await browser.new_context(
            storage_state='compras_session.json'
        )
        
        page = await context.new_page()
        await page.goto('https://www.gov.br/compras/pt-br/disputa/item/00001')
        
        # Cria monitor
        monitor = MonitorLances(page, item_config)
        
        # Registra callbacks
        def quando_lance_mudar(dados):
            print(f"💰 Lance mudou! {dados['lance_anterior']} → {dados['lance_atual']}")
        
        def quando_tempo_critico(dados):
            print(f"⏰ TEMPO CRÍTICO! {dados['tempo_restante']}s restantes")
            print(f"   Lance atual: R$ {dados['lance_atual']}")
        
        monitor.registrar_callback('lance_mudou', quando_lance_mudar)
        monitor.registrar_callback('tempo_critico', quando_tempo_critico)
        
        # Inicia monitoramento (vai rodar por 60 segundos neste exemplo)
        try:
            await asyncio.wait_for(
                monitor.iniciar(intervalo_polling=2.0),
                timeout=60
            )
        except asyncio.TimeoutError:
            print("⏱️  Timeout atingido, parando monitor...")
            await monitor.parar()
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(exemplo_monitor())
