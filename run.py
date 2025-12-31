"""
Arquivo de inicialização principal
Integra todos os módulos e inicializa o sistema
"""

import sys
from pathlib import Path
import asyncio
import os

# Setup paths
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Carrega variáveis de ambiente
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

from app.main import app, db, socketio
from core.heartbeat import HeartbeatMonitor, AlertaManager
from core.emergency_control import EmergencyController
from core.logger import logger


def inicializar_banco_dados():
    """Cria tabelas do banco de dados"""
    print("🗄️  Inicializando banco de dados...")
    with app.app_context():
        db.create_all()
    print("✅ Banco de dados pronto!")


def inicializar_logger():
    """Configura logger global"""
    print("📝 Logger configurado")
    logger.info("Sistema iniciado", user_id="global")


def inicializar_heartbeat():
    """Inicializa monitor de heartbeat"""
    print("💓 Heartbeat Monitor configurado")
    # Será iniciado quando primeiro robô começar


def inicializar_alertas():
    """Configura gerenciador de alertas"""
    print("🚨 Sistema de Alertas configurado")


def main():
    """Função principal"""
    print("\n" + "="*70)
    print("🤖 SISTEMA DE AUTOMAÇÃO DE LANCES - COMPRAS.GOV.BR")
    print("="*70)
    print("⚠️  AVISO LEGAL:")
    print("   Este sistema é para fins educacionais e de desenvolvimento.")
    print("   Certifique-se de estar em conformidade com:")
    print("   • Termos de uso do Compras.gov.br")
    print("   • Edital da licitação")
    print("   • IN nº 03/2011 do MPOG")
    print("="*70 + "\n")
    
    # Inicializa componentes
    inicializar_banco_dados()
    inicializar_logger()
    inicializar_heartbeat()
    inicializar_alertas()
    
    print("\n✨ Sistema pronto para iniciar!")
    print(f"🌐 Acesse: http://localhost:5000")
    print(f"📖 Documentação: {PROJECT_ROOT}/README.md")
    print("\n")
    
    # Inicia servidor Flask com WebSockets
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=os.environ.get('FLASK_ENV') == 'development',
        use_reloader=False  # Evita inicializar sistema 2x
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Sistema parado pelo usuário")
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
