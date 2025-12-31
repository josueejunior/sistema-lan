"""
Módulo de Autenticação Persistente com Playwright
Gerencia login no gov.br e mantém sessão ativa através de cookies
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class SessionManager:
    """
    Gerenciador de sessão persistente para o portal Compras.gov.br
    
    AVISO LEGAL: Este código é para fins educacionais e de desenvolvimento.
    O uso de automação em licitações públicas pode violar os Termos de Uso
    do portal e legislação aplicável. Certifique-se de consultar:
    - Edital da licitação
    - IN nº 03/2011
    - Termos de uso do Compras.gov.br
    """
    
    def __init__(self, storage_path: str = "session_storage.json"):
        """
        Inicializa o gerenciador de sessão
        
        Args:
            storage_path: Caminho para salvar os dados de sessão (cookies, localStorage)
        """
        self.storage_path = Path(storage_path)
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None
        
    async def initialize_browser(self, headless: bool = False):
        """
        Inicializa o navegador Chromium com configurações anti-detecção
        
        Args:
            headless: Se False, abre navegador visível para login manual
        """
        playwright = await async_playwright().start()
        
        # Configurações para evitar detecção de bot
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
    async def create_new_session(self, login_url: str):
        """
        Cria nova sessão com login manual assistido
        Abre navegador visível para usuário fazer login
        
        Args:
            login_url: URL da página de login do Compras.gov.br
        """
        print("🔓 Iniciando processo de autenticação manual...")
        print("⚠️  AGUARDE: Você precisará fazer o login manualmente no navegador")
        
        await self.initialize_browser(headless=False)
        
        # Cria contexto com user agent realista
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='pt-BR',
            timezone_id='America/Sao_Paulo'
        )
        
        # Injeta script para remover webdriver flag
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        self.page = await self.context.new_page()
        await self.page.goto(login_url, wait_until='networkidle')
        
        print("\n" + "="*60)
        print("🧑 AÇÃO NECESSÁRIA:")
        print("1. Complete o login no navegador que acabou de abrir")
        print("2. Resolva o CAPTCHA (se houver)")
        print("3. Complete a autenticação de 2 fatores (se solicitado)")
        print("4. Aguarde até estar DENTRO da área logada")
        print("="*60)
        
        # Aguarda usuário pressionar Enter após login manual
        input("\n✅ Pressione ENTER após completar o login e estar na área logada... ")
        
        # Salva o estado da sessão (cookies + localStorage)
        await self._save_session_state()
        
        print(f"💾 Sessão salva em: {self.storage_path.absolute()}")
        print("✅ Nas próximas execuções, o robô usará esta sessão automaticamente!")
        
        return self.context
    
    async def load_existing_session(self, target_url: str, headless: bool = True):
        """
        Carrega sessão existente a partir dos cookies salvos
        
        Args:
            target_url: URL para navegar após carregar sessão
            headless: Se True, executa sem interface gráfica
            
        Returns:
            BrowserContext com sessão ativa
            
        Raises:
            FileNotFoundError: Se arquivo de sessão não existir
        """
        if not self.storage_path.exists():
            raise FileNotFoundError(
                f"❌ Arquivo de sessão não encontrado: {self.storage_path}\n"
                "Execute primeiro o método create_new_session()"
            )
        
        print(f"🔄 Carregando sessão existente de: {self.storage_path}")
        
        await self.initialize_browser(headless=headless)
        
        # Carrega o storage_state salvo
        self.context = await self.browser.new_context(
            storage_state=str(self.storage_path),
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='pt-BR',
            timezone_id='America/Sao_Paulo'
        )
        
        # Remove webdriver flag
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        self.page = await self.context.new_page()
        
        try:
            await self.page.goto(target_url, wait_until='networkidle', timeout=30000)
            
            # Verifica se ainda está logado
            if await self._check_if_logged_in():
                print("✅ Sessão válida! Navegando na área autenticada...")
                return self.context
            else:
                print("⚠️  Sessão expirada. É necessário fazer novo login.")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao carregar sessão: {e}")
            return None
    
    async def _save_session_state(self):
        """Salva cookies e localStorage no arquivo JSON"""
        storage_state = await self.context.storage_state()
        
        # Adiciona metadados
        storage_state['metadata'] = {
            'created_at': datetime.now().isoformat(),
            'url': self.page.url
        }
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(storage_state, f, indent=2, ensure_ascii=False)
    
    async def _check_if_logged_in(self) -> bool:
        """
        Verifica se a sessão ainda está ativa
        IMPORTANTE: Ajustar seletores conforme portal real
        
        Returns:
            True se estiver logado, False caso contrário
        """
        try:
            # EXEMPLO: Verificar se existe elemento que só aparece quando logado
            # Ajustar seletores conforme o portal real
            
            # Opção 1: Verificar por redirecionamento para login
            if 'sso.acesso.gov.br' in self.page.url or 'login' in self.page.url.lower():
                return False
            
            # Opção 2: Verificar presença de elemento da área logada
            # await self.page.wait_for_selector('[data-testid="user-menu"]', timeout=5000)
            
            # Opção 3: Verificar cookie específico
            cookies = await self.context.cookies()
            auth_cookie = any('JSESSIONID' in c['name'] or 'auth' in c['name'].lower() for c in cookies)
            
            return auth_cookie
            
        except Exception as e:
            print(f"⚠️  Erro ao verificar login: {e}")
            return False
    
    async def refresh_session(self):
        """Atualiza a sessão salvando novamente o estado atual"""
        if self.context:
            await self._save_session_state()
            print("🔄 Sessão atualizada!")
    
    async def close(self):
        """Fecha navegador e libera recursos"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        print("👋 Navegador fechado")


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def exemplo_primeiro_login():
    """Exemplo: Primeira execução - Login manual"""
    manager = SessionManager(storage_path="compras_session.json")
    
    # URL do portal (AJUSTAR conforme necessário)
    login_url = "https://www.gov.br/compras/pt-br"
    
    try:
        await manager.create_new_session(login_url)
        
        # Após login, você pode navegar para outras páginas
        await manager.page.goto("https://www.gov.br/compras/pt-br/acesso-restrito/disputa")
        
        # Fazer scraping ou ações necessárias...
        print(f"📍 Página atual: {manager.page.url}")
        
    finally:
        await manager.close()


async def exemplo_uso_sessao_existente():
    """Exemplo: Execuções subsequentes - Reutilização automática"""
    manager = SessionManager(storage_path="compras_session.json")
    
    target_url = "https://www.gov.br/compras/pt-br/acesso-restrito/disputa"
    
    try:
        context = await manager.load_existing_session(target_url, headless=True)
        
        if context is None:
            print("❌ Sessão inválida. Execute primeiro o login manual.")
            return
        
        # Robô está autenticado e pronto para operar
        print(f"🤖 Robô operando na URL: {manager.page.url}")
        
        # Exemplo: Buscar informações da página
        title = await manager.page.title()
        print(f"📄 Título da página: {title}")
        
        # Aqui entraria a lógica de monitoramento/lances...
        
    finally:
        await manager.close()


if __name__ == "__main__":
    # Primeira vez: descomentar linha abaixo
    # asyncio.run(exemplo_primeiro_login())
    
    # Execuções posteriores:
    asyncio.run(exemplo_uso_sessao_existente())
