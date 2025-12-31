"""
Engine de Decisão e Execução de Lances
Calcula valores e executa lances conforme estratégia configurada
"""

import asyncio
from datetime import datetime
from typing import Dict, Optional
from playwright.async_api import Page
import random


class EngineDecisao:
    """
    Motor de decisão para lances automatizados
    
    Estratégias implementadas:
    1. SNIPER: Aguarda até tempo crítico (últimos segundos) para dar lance
    2. ESCADA: Dá lances imediatos respeitando intervalo mínimo
    """
    
    def __init__(self, item_config: Dict):
        """
        Args:
            item_config: Configuração do item incluindo:
                - valor_minimo: Piso que não será ultrapassado
                - estrategia: 'sniper' ou 'escada'
                - intervalo_lance: Percentual ou valor fixo de redução
                - tempo_gatilho: Segundos antes do fim para ativar (sniper)
        """
        self.config = item_config
        self.historico_decisoes = []
        self.ultimo_lance_enviado = None
        self.ultima_tentativa = None
    
    def avaliar_lance(
        self,
        lance_atual: float,
        tempo_restante: Optional[int],
        intervalo_minimo: Optional[float]
    ) -> Dict:
        """
        Avalia se deve dar lance e calcula o valor
        
        Args:
            lance_atual: Valor do menor lance atual na disputa
            tempo_restante: Segundos restantes (None se desconhecido)
            intervalo_minimo: Intervalo mínimo do sistema (% ou valor)
        
        Returns:
            Dict com:
                - deve_dar_lance: bool
                - valor_proposto: float ou None
                - motivo: str explicando a decisão
        """
        decisao = {
            'deve_dar_lance': False,
            'valor_proposto': None,
            'motivo': '',
            'timestamp': datetime.now().isoformat()
        }
        
        # Validação 1: Lance atual é válido?
        if lance_atual is None or lance_atual <= 0:
            decisao['motivo'] = 'Lance atual inválido ou não detectado'
            return decisao
        
        # Validação 2: Já atingiu o valor mínimo?
        if lance_atual <= self.config['valor_minimo']:
            decisao['motivo'] = f'Lance atual (R$ {lance_atual:.2f}) já atingiu o valor mínimo (R$ {self.config["valor_minimo"]:.2f})'
            return decisao
        
        # Validação 3: Estratégia específica
        estrategia = self.config.get('estrategia', 'sniper')
        
        if estrategia == 'sniper':
            return self._avaliar_sniper(lance_atual, tempo_restante, intervalo_minimo, decisao)
        elif estrategia == 'escada':
            return self._avaliar_escada(lance_atual, tempo_restante, intervalo_minimo, decisao)
        else:
            decisao['motivo'] = f'Estratégia desconhecida: {estrategia}'
            return decisao
    
    def _avaliar_sniper(
        self,
        lance_atual: float,
        tempo_restante: Optional[int],
        intervalo_minimo: Optional[float],
        decisao: Dict
    ) -> Dict:
        """
        Estratégia SNIPER: Aguarda últimos segundos para dar lance
        """
        tempo_gatilho = self.config.get('tempo_gatilho', 60)
        
        # Verifica se está no tempo de gatilho
        if tempo_restante is None:
            decisao['motivo'] = 'Tempo restante desconhecido (aguardando)'
            return decisao
        
        if tempo_restante > tempo_gatilho:
            decisao['motivo'] = f'Aguardando tempo crítico ({tempo_restante}s > {tempo_gatilho}s)'
            return decisao
        
        # Está no tempo crítico! Calcular lance
        valor_proposto = self._calcular_valor_lance(lance_atual, intervalo_minimo)
        
        if valor_proposto is None:
            decisao['motivo'] = 'Não foi possível calcular valor do lance'
            return decisao
        
        # Verifica se não ultrapassa o mínimo
        if valor_proposto < self.config['valor_minimo']:
            valor_proposto = self.config['valor_minimo']
            decisao['motivo'] = f'⚠️  Valor ajustado para mínimo (R$ {valor_proposto:.2f})'
        else:
            decisao['motivo'] = f'🎯 SNIPER ATIVADO! Tempo: {tempo_restante}s'
        
        decisao['deve_dar_lance'] = True
        decisao['valor_proposto'] = valor_proposto
        
        return decisao
    
    def _avaliar_escada(
        self,
        lance_atual: float,
        tempo_restante: Optional[int],
        intervalo_minimo: Optional[float],
        decisao: Dict
    ) -> Dict:
        """
        Estratégia ESCADA: Dá lances imediatos sempre que possível
        """
        # Calcula valor do lance
        valor_proposto = self._calcular_valor_lance(lance_atual, intervalo_minimo)
        
        if valor_proposto is None:
            decisao['motivo'] = 'Não foi possível calcular valor do lance'
            return decisao
        
        # Verifica se não ultrapassa o mínimo
        if valor_proposto < self.config['valor_minimo']:
            valor_proposto = self.config['valor_minimo']
            decisao['motivo'] = f'⚠️  Valor ajustado para mínimo (R$ {valor_proposto:.2f})'
        else:
            decisao['motivo'] = f'📉 Lance escada (reduzindo gradualmente)'
        
        decisao['deve_dar_lance'] = True
        decisao['valor_proposto'] = valor_proposto
        
        return decisao
    
    def _calcular_valor_lance(
        self,
        lance_atual: float,
        intervalo_minimo: Optional[float]
    ) -> Optional[float]:
        """
        Calcula o valor do próximo lance
        
        Lógica:
        1. Se intervalo_minimo do sistema estiver disponível, usa ele
        2. Senão, usa o intervalo_lance configurado pelo usuário
        3. Aplica randomização pequena para parecer humano
        """
        # Prioriza intervalo do sistema
        if intervalo_minimo is not None:
            reducao = intervalo_minimo
        else:
            # Usa configuração do usuário (assume percentual)
            percentual = self.config.get('intervalo_lance', 1.0)
            reducao = lance_atual * (percentual / 100)
        
        # Calcula novo valor
        novo_valor = lance_atual - reducao
        
        # Adiciona pequena randomização (±0.5%) para parecer humano
        variacao = novo_valor * random.uniform(-0.005, 0.005)
        novo_valor += variacao
        
        # Arredonda para 2 casas decimais
        return round(novo_valor, 2)
    
    def registrar_decisao(self, decisao: Dict):
        """Registra decisão no histórico"""
        self.historico_decisoes.append(decisao)
        
        # Limita histórico a 100 últimas decisões
        if len(self.historico_decisoes) > 100:
            self.historico_decisoes.pop(0)


class ExecutorLances:
    """
    Executa lances na interface do portal
    com técnicas de humanização para evitar detecção
    """
    
    def __init__(self, page: Page, logger=None):
        """
        Args:
            page: Página do Playwright já autenticada
            logger: Logger para registrar operações (opcional)
        """
        self.page = page
        self.historico_execucoes = []
        self.logger = logger
    
    async def executar_lance(self, valor: float, item_id: str) -> Dict:
        """
        Executa o lance na interface do portal
        com simulação de comportamento humano
        
        IMPORTANTE: Seletores devem ser ajustados conforme o portal real
        
        Args:
            valor: Valor do lance a ser enviado
            item_id: Identificador do item
        
        Returns:
            Dict com resultado da execução:
                - sucesso: bool
                - mensagem: str
                - timestamp: str
        """
        resultado = {
            'sucesso': False,
            'mensagem': '',
            'valor': valor,
            'item_id': item_id,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            print(f"🤖 Executando lance de R$ {valor:.2f} no item {item_id}...")
            
            if self.logger:
                await self.logger.info(
                    f"Preparando lance no item {item_id}",
                    {'valor': valor}
                )
            
            # ============================================================
            # ATENÇÃO: AJUSTAR SELETORES CONFORME PORTAL REAL
            # ============================================================
            
            # Passo 1: Localizar campo de valor
            # input_valor = await self.page.query_selector('#valor-lance, input[name="valor"]')
            
            # if not input_valor:
            #     resultado['mensagem'] = 'Campo de valor não encontrado'
            #     return resultado
            
            # Passo 2: Mover mouse até o campo (humanização)
            await self._mover_mouse_humanizado(200, 200)
            
            # Passo 3: Delay humano antes de interagir
            await asyncio.sleep(random.uniform(0.8, 1.2))
            
            # Passo 4: Clicar no campo
            # await input_valor.click()
            
            # Passo 5: Delay antes de digitar
            await asyncio.sleep(random.uniform(0.3, 0.6))
            
            # Passo 6: Limpar campo e digitar valor (carácter por carácter)
            # await input_valor.fill('')
            # await self._digitar_como_humano(str(valor))
            
            # Passo 7: Delay antes de enviar
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # Passo 8: Mover mouse até botão de envio
            await self._mover_mouse_humanizado(300, 400)
            
            # Passo 9: Pequena pausa e então clique
            await asyncio.sleep(random.uniform(0.2, 0.4))
            
            # Passo 10: Clicar no botão de enviar
            # btn_enviar = await self.page.query_selector('#btn-enviar-lance, button[type="submit"]')
            
            # if not btn_enviar:
            #     resultado['mensagem'] = 'Botão de envio não encontrado'
            #     return resultado
            
            # await btn_enviar.click()
            
            # Passo 11: Aguardar processamento
            await asyncio.sleep(random.uniform(1.5, 2.5))
            
            # Passo 12: Verificar se lance foi aceito
            # sucesso = await self._verificar_sucesso_lance()
            
            # if sucesso:
            #     resultado['sucesso'] = True
            #     resultado['mensagem'] = 'Lance enviado com sucesso!'
            #     print(f"✅ Lance de R$ {valor:.2f} enviado com sucesso!")
            #     if self.logger:
            #         await self.logger.info(f"Lance enviado: R$ {valor:.2f}")
            # else:
            #     resultado['mensagem'] = 'Lance rejeitado pelo sistema'
            #     print(f"❌ Lance rejeitado")
            #     if self.logger:
            #         await self.logger.warning(f"Lance rejeitado: R$ {valor:.2f}")
            
            # SIMULAÇÃO (remover em produção):
            resultado['sucesso'] = True
            resultado['mensagem'] = '✅ [SIMULAÇÃO] Lance enviado'
            if self.logger:
                await self.logger.info(
                    f"Lance simulado enviado",
                    {'valor': valor}
                )
            
        except Exception as e:
            resultado['mensagem'] = f'Erro ao executar lance: {str(e)}'
            print(f"❌ Erro: {e}")
            if self.logger:
                await self.logger.error(f"Erro ao executar lance: {e}")
        
        # Registra no histórico
        self.historico_execucoes.append(resultado)
        
        return resultado
    
    async def _digitar_como_humano(self, texto: str):
        """
        Digita texto com delays entre teclas para parecer humano
        """
        for char in texto:
            await self.page.keyboard.type(char)
            await asyncio.sleep(random.uniform(0.05, 0.15))
    
    async def _mover_mouse_humanizado(self, x: int, y: int):
        """
        Move mouse gradualmente até a posição (simulação de movimento)
        Implementa caminho não-linear para parecer mais humano
        
        Args:
            x: Posição X do alvo
            y: Posição Y do alvo
        """
        try:
            # Obtém posição atual do mouse (aproximadamente)
            # Esta é uma simulação; Playwright não expõe posição atual
            
            # Número de passos intermediários (quanto maior, mais suave)
            passos = random.randint(15, 30)
            
            # Posição inicial aproximada (cantos aleatórios)
            inicio_x = random.randint(100, 300)
            inicio_y = random.randint(100, 300)
            
            # Gera caminho com perturbação (não linear)
            for i in range(passos):
                progresso = i / passos
                
                # Interpolação suave (ease-in-out)
                t = progresso ** 2 * (3 - 2 * progresso)
                
                # Posição atual com pequeno desvio aleatório
                pos_x = int(inicio_x + (x - inicio_x) * t + random.uniform(-5, 5))
                pos_y = int(inicio_y + (y - inicio_y) * t + random.uniform(-5, 5))
                
                # Move mouse
                await self.page.mouse.move(pos_x, pos_y)
                
                # Delay variável entre movimentos
                await asyncio.sleep(random.uniform(0.01, 0.05))
        
        except Exception as e:
            # Se movimento falhar, continua mesmo assim
            pass
    
    async def _verificar_sucesso_lance(self) -> bool:
        """
        Verifica se o lance foi aceito pelo sistema
        
        AJUSTAR conforme mensagens do portal real
        """
        try:
            # Opção 1: Verificar mensagem de sucesso
            # mensagem_sucesso = await self.page.query_selector('.alert-success, .mensagem-sucesso')
            # if mensagem_sucesso:
            #     return True
            
            # Opção 2: Verificar se apareceu erro
            # mensagem_erro = await self.page.query_selector('.alert-danger, .mensagem-erro')
            # if mensagem_erro:
            #     return False
            
            return True  # Implementar lógica real
            
        except Exception as e:
            print(f"⚠️  Erro ao verificar sucesso: {e}")
            return False


# ============================================================================
# EXEMPLO DE USO INTEGRADO
# ============================================================================

async def exemplo_integracao():
    """Exemplo de integração Engine + Executor"""
    from playwright.async_api import async_playwright
    
    # Configuração do item
    item_config = {
        'id': 1,
        'numero_item': '00001',
        'valor_minimo': 3000.00,
        'estrategia': 'sniper',
        'intervalo_lance': 1.0,  # 1%
        'tempo_gatilho': 60
    }
    
    # Inicializa componentes
    engine = EngineDecisao(item_config)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        executor = ExecutorLances(page)
        
        # Simula cenário de lance
        lance_atual = 3500.00
        tempo_restante = 45  # segundos
        intervalo_minimo = None
        
        # Avalia se deve dar lance
        decisao = engine.avaliar_lance(lance_atual, tempo_restante, intervalo_minimo)
        
        print(f"📊 Decisão: {decisao['motivo']}")
        
        if decisao['deve_dar_lance']:
            print(f"💰 Valor proposto: R$ {decisao['valor_proposto']:.2f}")
            
            # Executa lance
            resultado = await executor.executar_lance(
                decisao['valor_proposto'],
                item_config['numero_item']
            )
            
            print(f"📝 Resultado: {resultado['mensagem']}")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(exemplo_integracao())
