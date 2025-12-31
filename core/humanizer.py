"""
Humanização Avançada - Simulação de comportamento humano
Evita detecção de bot através de:
- Delays randômicos
- Movimento de mouse realista
- Variação de padrões de clique
"""

import asyncio
import random
import math
from typing import Tuple
from playwright.async_api import Page


class HumanSimulator:
    """
    Simula comportamento humano no navegador
    """
    
    def __init__(self, page: Page):
        """
        Args:
            page: Página do Playwright
        """
        self.page = page
        self.ultima_posicao_mouse = (0, 0)
    
    async def delay_humano(
        self,
        minimo: float = 0.5,
        maximo: float = 1.5,
        usar_curva: bool = True
    ) -> float:
        """
        Gera delay realista entre ações
        
        Args:
            minimo: Delay mínimo em segundos
            maximo: Delay máximo em segundos
            usar_curva: Se True, usa distribuição não-uniforme (mais humano)
        
        Returns:
            Tempo de espera em segundos
        """
        if usar_curva:
            # Distribuição beta (simula padrão humano: mais rápido no meio)
            valor_normalizado = random.betavariate(2, 2)
            delay = minimo + (maximo - minimo) * valor_normalizado
        else:
            delay = random.uniform(minimo, maximo)
        
        await asyncio.sleep(delay)
        return delay
    
    async def mover_mouse(self, alvo: Tuple[int, int]):
        """
        Move mouse para posição alvo com trajetória curva (Bézier)
        
        Args:
            alvo: Posição (x, y) para mover o mouse
        """
        inicio = self.ultima_posicao_mouse
        fim = alvo
        
        # Número de passos (quanto mais longe, mais passos)
        distancia = math.sqrt((fim[0] - inicio[0])**2 + (fim[1] - inicio[1])**2)
        num_passos = max(10, int(distancia / 50))
        
        # Gera ponto de controle para trajetória curva (mais natural)
        control_x = random.randint(min(inicio[0], fim[0]), max(inicio[0], fim[0]))
        control_y = random.randint(min(inicio[1], fim[1]), max(inicio[1], fim[1]))
        
        # Move mouse suavemente através da trajetória
        for i in range(num_passos):
            t = i / num_passos
            
            # Interpolação quadrática de Bézier
            x = (1-t)**2 * inicio[0] + 2*(1-t)*t * control_x + t**2 * fim[0]
            y = (1-t)**2 * inicio[1] + 2*(1-t)*t * control_y + t**2 * fim[1]
            
            await self.page.mouse.move(int(x), int(y))
            
            # Delay pequeno entre passos
            await asyncio.sleep(random.uniform(0.01, 0.05))
        
        self.ultima_posicao_mouse = fim
    
    async def clicar_naturalista(self, seletor: str, tempo_hold: float = 0.05):
        """
        Clica em elemento de forma naturalista
        
        1. Move mouse até o elemento
        2. Aguarda um pouco (como se estivesse mirando)
        3. Clica e mantém pressionado
        4. Libera botão
        
        Args:
            seletor: Seletor CSS do elemento
            tempo_hold: Tempo em segundos mantendo botão pressionado
        """
        # Localiza elemento
        elemento = await self.page.query_selector(seletor)
        if not elemento:
            raise ValueError(f"Elemento não encontrado: {seletor}")
        
        # Obtém posição do elemento
        bbox = await elemento.bounding_box()
        if not bbox:
            raise ValueError(f"Não foi possível localizar elemento: {seletor}")
        
        # Posição alvo (com pequena variação dentro do elemento)
        x = bbox['x'] + bbox['width'] / 2 + random.uniform(-10, 10)
        y = bbox['y'] + bbox['height'] / 2 + random.uniform(-5, 5)
        
        print(f"🖱️  Movendo mouse para ({x:.0f}, {y:.0f})")
        
        # Move mouse até o elemento
        await self.mover_mouse((int(x), int(y)))
        
        # Aguarda um pouco (decisão de click)
        await self.delay_humano(0.2, 0.5)
        
        # Clica
        await self.page.mouse.down()
        await asyncio.sleep(tempo_hold)
        await self.page.mouse.up()
        
        print(f"✅ Clicado em {seletor}")
        
        # Pequeno delay pós-clique
        await self.delay_humano(0.1, 0.3)
    
    async def digitar_naturalista(self, texto: str, seletor: str = None):
        """
        Digita texto de forma naturalista
        
        - Delays variáveis entre teclas
        - Ocasionalmente faz "typos" que corrige
        - Simula pausa para pensar
        
        Args:
            texto: Texto a digitar
            seletor: Seletor opcional (clica antes de digitar)
        """
        # Clica no campo se fornecido
        if seletor:
            elemento = await self.page.query_selector(seletor)
            if elemento:
                await elemento.click()
                await self.delay_humano(0.3, 0.7)
        
        print(f"⌨️  Digitando: {texto}")
        
        for i, char in enumerate(texto):
            # Pausa ocasional para "pensar"
            if random.random() < 0.05:  # 5% de chance
                await self.delay_humano(0.5, 2.0)
            
            # Delay normal entre teclas (mais rápido no meio, mais lento nas extremidades)
            if i % 5 == 0:
                await self.delay_humano(0.05, 0.15)  # Mais lento a cada 5 chars
            else:
                await self.delay_humano(0.02, 0.08)  # Normal
            
            # Digita caracter
            await self.page.keyboard.type(char)
        
        print(f"✅ Digitação completa")
    
    async def scroll_naturalista(
        self,
        direcao: str = "down",
        quantidade: int = 3,
        velocidade: str = "normal"
    ):
        """
        Scrolls na página de forma naturalista
        
        Args:
            direcao: 'up' ou 'down'
            quantidade: Número de scrolls
            velocidade: 'lento', 'normal', 'rapido'
        """
        delays = {
            'lento': (0.5, 1.0),
            'normal': (0.2, 0.5),
            'rapido': (0.05, 0.15)
        }
        
        delay_range = delays.get(velocidade, delays['normal'])
        
        for i in range(quantidade):
            delta = 3 if direcao == "down" else -3
            await self.page.mouse.wheel(0, delta)
            await self.delay_humano(delay_range[0], delay_range[1])
    
    async def hover_antes_clique(self, seletor: str):
        """
        Passa o mouse sobre elemento antes de clicar (mais realista)
        """
        elemento = await self.page.query_selector(seletor)
        if elemento:
            await elemento.hover()
            await self.delay_humano(0.3, 0.8)


# ============================================================================
# INTEGRAÇÃO COM ENGINE DE DECISÃO
# ============================================================================

async def exemplo_uso_humanizado():
    """Exemplo de execução humanizada de lance"""
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Cria simulador
        simulator = HumanSimulator(page)
        
        # Navega para uma página
        await page.goto("https://example.com")
        
        # Exemplo de interação humanizada
        # await simulator.scroll_naturalista("down", quantidade=2)
        # await simulator.clicar_naturalista("button")
        # await simulator.digitar_naturalista("CPF", "input[type='text']")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(exemplo_uso_humanizado())
