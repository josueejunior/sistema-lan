"""
Módulo de Pós-Lance
Captura atas, registra concorrentes e gera inteligência comercial
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CapturadorResultados:
    """
    Captura resultados da licitação após encerramento
    """
    
    def __init__(self, diretorio_atas: str = "atas_licitacoes"):
        """
        Args:
            diretorio_atas: Diretório para salvar atas
        """
        self.diretorio = Path(diretorio_atas)
        self.diretorio.mkdir(exist_ok=True)
    
    async def baixar_ata(
        self,
        page,
        item_id: str,
        numero_disputa: str
    ) -> Optional[str]:
        """
        Baixa ata da sessão assim que terminar
        
        Args:
            page: Página do Playwright
            item_id: Identificador do item
            numero_disputa: Número da disputa/pregão
            
        Returns:
            Caminho do arquivo salvo ou None em caso de erro
        """
        try:
            logger.info(f"📥 Baixando ata para item {item_id}...")
            
            # Aguarda elemento de download
            # selector_download = await page.query_selector('a[download], .btn-download-ata')
            
            # if not selector_download:
            #     logger.warning(f"Botão de download não encontrado para {item_id}")
            #     return None
            
            # Configura listener para download
            async with page.expect_download() as download_info:
                # await selector_download.click()
                pass
            
            # download = await download_info.value
            # caminho_arquivo = self.diretorio / f"ata_{numero_disputa}_{item_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Simula salvamento
            caminho_arquivo = self.diretorio / f"ata_{numero_disputa}_{item_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            caminho_arquivo.write_text(f"[Ata da disputa {numero_disputa} - Item {item_id}]\n{datetime.now().isoformat()}\n")
            
            logger.info(f"✅ Ata salva: {caminho_arquivo}")
            return str(caminho_arquivo)
        
        except Exception as e:
            logger.error(f"❌ Erro ao baixar ata: {e}")
            return None
    
    async def extrair_ata_tela(self, page, item_id: str) -> Dict:
        """
        Extrai informações da ata diretamente da tela
        (antes de sair da página)
        
        Args:
            page: Página do Playwright
            item_id: Identificador do item
            
        Returns:
            Dicionário com dados extraídos
        """
        try:
            resultado_ata = {
                'item_id': item_id,
                'timestamp': datetime.now().isoformat(),
                'lance_vencedor': None,
                'fornecedor_vencedor': None,
                'todos_os_lances': [],
                'total_concorrentes': 0
            }
            
            # EXEMPLO: Extrair informações da página
            # texto_ata = await page.inner_text('.resultado-final, #ata-disputa')
            # resultado_ata['conteudo_bruto'] = texto_ata
            
            logger.info(f"📋 Ata extraída para item {item_id}")
            return resultado_ata
        
        except Exception as e:
            logger.error(f"❌ Erro ao extrair ata: {e}")
            return {}


class AnalisadorConcorrentes:
    """
    Analisa concorrentes e mantém banco de dados de inteligência comercial
    """
    
    def __init__(self, arquivo_banco: str = "concorrentes_dados.json"):
        """
        Args:
            arquivo_banco: Arquivo JSON com dados dos concorrentes
        """
        self.arquivo = Path(arquivo_banco)
        self.dados = self._carregar_dados()
    
    def _carregar_dados(self) -> Dict:
        """Carrega dados existentes ou cria novo"""
        if self.arquivo.exists():
            try:
                return json.loads(self.arquivo.read_text(encoding='utf-8'))
            except:
                return {}
        return {}
    
    def salvar_dados(self):
        """Salva dados em JSON"""
        self.arquivo.write_text(
            json.dumps(self.dados, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
    
    async def registrar_concorrentes(
        self,
        numero_disputa: str,
        item_id: str,
        concorrentes: List[Dict]
    ):
        """
        Registra concorrentes de uma disputa
        
        Args:
            numero_disputa: Número da disputa
            item_id: Identificador do item
            concorrentes: Lista com dados dos concorrentes
                [
                    {
                        'nome': 'Empresa XYZ',
                        'cnpj': '12.345.678/0001-00',
                        'lance_final': 45000.00,
                        'posicao': 1,
                        'foi_vencedor': True
                    },
                    ...
                ]
        """
        chave = f"disputa_{numero_disputa}"
        
        if chave not in self.dados:
            self.dados[chave] = {
                'data': datetime.now().isoformat(),
                'itens': {}
            }
        
        self.dados[chave]['itens'][item_id] = {
            'concorrentes': concorrentes,
            'total': len(concorrentes),
            'vencedor': next(
                (c['nome'] for c in concorrentes if c.get('foi_vencedor')),
                None
            )
        }
        
        self.salvar_dados()
        logger.info(f"✅ {len(concorrentes)} concorrentes registrados")
    
    def analisar_concorrencia(self, cnpj: str) -> Dict:
        """
        Analisa histórico de um concorrente
        
        Args:
            cnpj: CNPJ do concorrente
            
        Returns:
            Estatísticas do concorrente
        """
        estatisticas = {
            'total_participacoes': 0,
            'total_vitorias': 0,
            'taxa_vitoria': 0.0,
            'preco_medio': 0.0,
            'preco_minimo': float('inf'),
            'preco_maximo': 0.0,
            'historico_lances': []
        }
        
        # Busca em todos os registros
        total_lances = []
        
        for disputa_key, disputa_data in self.dados.items():
            for item_id, item_data in disputa_data.get('itens', {}).items():
                for concorrente in item_data.get('concorrentes', []):
                    if concorrente.get('cnpj') == cnpj:
                        estatisticas['total_participacoes'] += 1
                        
                        if concorrente.get('foi_vencedor'):
                            estatisticas['total_vitorias'] += 1
                        
                        lance = concorrente.get('lance_final', 0)
                        total_lances.append(lance)
                        
                        estatisticas['historico_lances'].append({
                            'disputa': disputa_key,
                            'item': item_id,
                            'valor': lance
                        })
        
        # Calcula estatísticas
        if total_lances:
            estatisticas['preco_medio'] = sum(total_lances) / len(total_lances)
            estatisticas['preco_minimo'] = min(total_lances)
            estatisticas['preco_maximo'] = max(total_lances)
        
        if estatisticas['total_participacoes'] > 0:
            estatisticas['taxa_vitoria'] = (
                estatisticas['total_vitorias'] / 
                estatisticas['total_participacoes'] * 100
            )
        
        return estatisticas
    
    def obter_concorrentes_frequentes(self, top_n: int = 10) -> List[Dict]:
        """
        Retorna concorrentes mais frequentes nas licitações
        
        Args:
            top_n: Número de concorrentes a retornar
            
        Returns:
            Lista com os N concorrentes mais frequentes
        """
        contagem = {}
        
        for disputa_data in self.dados.values():
            for item_data in disputa_data.get('itens', {}).values():
                for concorrente in item_data.get('concorrentes', []):
                    nome = concorrente.get('nome', 'Desconhecido')
                    if nome not in contagem:
                        contagem[nome] = 0
                    contagem[nome] += 1
        
        # Ordena por frequência
        sorted_concorrentes = sorted(
            contagem.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {'nome': nome, 'frequencia': freq}
            for nome, freq in sorted_concorrentes[:top_n]
        ]
    
    def gerar_relatorio_inteligencia(self) -> str:
        """
        Gera relatório de inteligência comercial
        
        Returns:
            Texto formatado com análise
        """
        relatorio = "=" * 60 + "\n"
        relatorio += "📊 RELATÓRIO DE INTELIGÊNCIA COMERCIAL\n"
        relatorio += "=" * 60 + "\n\n"
        
        relatorio += f"Total de disputas monitoradas: {len(self.dados)}\n"
        
        # Concorrentes frequentes
        relatorio += "\n🏆 CONCORRENTES MÁS FREQUENTES:\n"
        for i, item in enumerate(self.obter_concorrentes_frequentes(5), 1):
            relatorio += f"  {i}. {item['nome']}: {item['frequencia']} participações\n"
        
        relatorio += "\n✅ Dados completos salvos em: " + str(self.arquivo)
        
        return relatorio


# ============================================================================
# INTEGRAÇÃO COM MONITOR
# ============================================================================

class OrquestradorPosLance:
    """
    Coordena coleta de dados pós-lance
    """
    
    def __init__(self):
        self.capturador = CapturadorResultados()
        self.analisador = AnalisadorConcorrentes()
    
    async def processar_resultado(
        self,
        page,
        numero_disputa: str,
        item_id: str,
        logger_realtime=None
    ):
        """
        Processa resultado da disputa após encerramento
        """
        try:
            if logger_realtime:
                await logger_realtime.info(
                    f"Processando resultado do item {item_id}"
                )
            
            # 1. Baixa ata
            ata_path = await self.capturador.baixar_ata(
                page,
                item_id,
                numero_disputa
            )
            
            # 2. Extrai dados da tela
            dados_ata = await self.capturador.extrair_ata_tela(
                page,
                item_id
            )
            
            if logger_realtime:
                await logger_realtime.info(
                    f"Resultado capturado para item {item_id}"
                )
            
            return {
                'ata_arquivo': ata_path,
                'dados_ata': dados_ata
            }
        
        except Exception as e:
            logger.error(f"❌ Erro ao processar resultado: {e}")
            return None


# ============================================================================
# EXEMPLO
# ============================================================================

async def exemplo_pos_lance():
    """Exemplo de uso"""
    
    analisador = AnalisadorConcorrentes()
    
    # Simula registro de concorrentes
    concorrentes_exemplo = [
        {
            'nome': 'Empresa A',
            'cnpj': '12.345.678/0001-00',
            'lance_final': 45000.00,
            'posicao': 1,
            'foi_vencedor': True
        },
        {
            'nome': 'Empresa B',
            'cnpj': '87.654.321/0001-00',
            'lance_final': 46000.00,
            'posicao': 2,
            'foi_vencedor': False
        }
    ]
    
    await analisador.registrar_concorrentes(
        'PREGAO_2025_001',
        'ITEM_001',
        concorrentes_exemplo
    )
    
    # Gera relatório
    relatorio = analisador.gerar_relatorio_inteligencia()
    print(relatorio)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(exemplo_pos_lance())
