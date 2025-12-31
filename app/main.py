"""
Aplicação Flask - Sistema de Automação de Lances
Interface web para configurar e monitorar lances automáticos
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
from datetime import datetime, timedelta
import asyncio
from threading import Thread
import json
import sys
from pathlib import Path

# Adiciona diretórios ao path
sys.path.append(str(Path(__file__).parent.parent))

from core.database import db, DatabaseManager, Usuario, RoboConfig
from core.logger import logger, LogLevel
from core.heartbeat import HeartbeatMonitor, AlertaManager
from core.emergency_control import EmergencyController

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.environ.get('SECRET_KEY', 'sua-chave-secreta-aqui-mude-em-producao')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///lance_system.db')

CORS(app)
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Estado global do sistema (em produção, usar Redis ou DB)
sistema_estado = {
    'sessao_ativa': False,
    'ultimo_login': None,
    'itens_monitorados': [],
    'historico_lances': []
}


# ============================================================================
# WebSocket Events
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Quando cliente WebSocket conecta"""
    user_id = session.get('user_id', 'global')
    join_room(user_id)
    
    logger.info(f"Cliente conectado", user_id=user_id)
    emit('status', {'data': 'Conectado ao servidor'})


@socketio.on('disconnect')
def handle_disconnect():
    """Quando cliente WebSocket desconecta"""
    user_id = session.get('user_id', 'global')
    leave_room(user_id)
    
    logger.info(f"Cliente desconectado", user_id=user_id)


# ============================================================================
# Callbacks para Logger (emite via WebSocket)
# ============================================================================

def _on_log_event(evento):
    """Callback chamado quando há novo log"""
    user_id = session.get('user_id', 'global')
    socketio.emit('log_evento', evento.to_dict(), room=user_id)


logger.subscribe('global', _on_log_event)


@app.route('/')
def index():
    """Página principal - Dashboard"""
    return render_template('dashboard.html', estado=sistema_estado)


@app.route('/api/status')
def api_status():
    """Retorna status atual do sistema"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({
            'success': False,
            'error': 'Não autenticado'
        }), 401
    
    return jsonify({
        'success': True,
        'data': {
            'sessao_ativa': sistema_estado['sessao_ativa'],
            'ultimo_login': sistema_estado['ultimo_login'],
            'itens_ativos': len([i for i in sistema_estado['itens_monitorados'] if i.get('ativo')]),
            'total_lances': len(sistema_estado['historico_lances'])
        }
    })


@app.route('/api/login', methods=['POST'])
def api_login():
    """
    Inicia processo de login manual
    Abre navegador para usuário fazer autenticação no gov.br
    """
    try:
        # Importa o módulo de autenticação
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from auth.session_manager import SessionManager
        
        # Executa login em thread separada para não bloquear Flask
        def run_login():
            async def do_login():
                manager = SessionManager(storage_path="compras_session.json")
                await manager.create_new_session("https://www.gov.br/compras/pt-br")
                sistema_estado['sessao_ativa'] = True
                sistema_estado['ultimo_login'] = datetime.now().isoformat()
            
            asyncio.run(do_login())
        
        thread = Thread(target=run_login)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Processo de login iniciado. Verifique a janela do navegador.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/itens', methods=['GET', 'POST'])
def api_itens():
    """
    GET: Lista todos os itens configurados
    POST: Adiciona novo item para monitoramento
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Não autenticado'}), 401
    
    if request.method == 'GET':
        robos = DatabaseManager.listar_robos(user_id)
        return jsonify({
            'success': True,
            'data': [robo.to_dict() for robo in robos]
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Valida dados obrigatórios
            required_fields = ['numero_item', 'descricao', 'valor_minimo']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Campo obrigatório ausente: {field}'
                    }), 400
            
            # Cria novo robô no banco
            robo = DatabaseManager.criar_robo(user_id, data)
            
            logger.info(f"Novo robô criado: {robo.numero_item}", user_id=str(user_id))
            
            return jsonify({
                'success': True,
                'message': 'Item adicionado com sucesso',
                'data': robo.to_dict()
            })
            
        except Exception as e:
            logger.error(f"Erro ao criar robô: {str(e)}", user_id=str(user_id))
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


@app.route('/api/itens/<int:item_id>', methods=['PUT', 'DELETE'])
def api_item_operacoes(item_id):
    """
    PUT: Atualiza configuração do item
    DELETE: Remove item do monitoramento
    """
    item = next((i for i in sistema_estado['itens_monitorados'] if i['id'] == item_id), None)
    
    if not item:
        return jsonify({
            'success': False,
            'error': 'Item não encontrado'
        }), 404
    
    if request.method == 'PUT':
        data = request.get_json()
        item.update(data)
        return jsonify({
            'success': True,
            'message': 'Item atualizado',
            'data': item
        })
    
    elif request.method == 'DELETE':
        sistema_estado['itens_monitorados'].remove(item)
        return jsonify({
            'success': True,
            'message': 'Item removido'
        })


@app.route('/api/itens/<int:item_id>/toggle', methods=['POST'])
def api_toggle_item(item_id):
    """Ativa/Desativa monitoramento de um item"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Não autenticado'}), 401
    
    robo = DatabaseManager.obter_robo(item_id)
    
    if not robo or robo.usuario_id != user_id:
        return jsonify({
            'success': False,
            'error': 'Item não encontrado'
        }), 404
    
    robo.ativo = not robo.ativo
    if robo.ativo:
        robo.iniciado_em = datetime.now()
        robo.rodando = True
    else:
        robo.parado_em = datetime.now()
        robo.rodando = False
    
    db.session.commit()
    
    logger.info(f"Item {robo.numero_item} {'ativado' if robo.ativo else 'desativado'}", 
                user_id=str(user_id))
    
    return jsonify({
        'success': True,
        'message': f'Item {"ativado" if robo.ativo else "desativado"}',
        'data': robo.to_dict()
    })


@app.route('/api/historico')
def api_historico():
    """Retorna histórico de lances realizados"""
    return jsonify({
        'success': True,
        'data': sistema_estado['historico_lances']
    })


@app.route('/api/lance/manual', methods=['POST'])
def api_lance_manual():
    """Executa um lance manual imediatamente"""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        valor = data.get('valor')
        
        if not item_id or not valor:
            return jsonify({
                'success': False,
                'error': 'item_id e valor são obrigatórios'
            }), 400
        
        # TODO: Integrar com executor de lances
        # Por enquanto, apenas registra no histórico
        
        lance = {
            'id': len(sistema_estado['historico_lances']) + 1,
            'item_id': item_id,
            'valor': float(valor),
            'tipo': 'manual',
            'timestamp': datetime.now().isoformat(),
            'sucesso': True
        }
        
        sistema_estado['historico_lances'].append(lance)
        
        return jsonify({
            'success': True,
            'message': 'Lance enviado com sucesso',
            'data': lance
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health')
def health():
    """Endpoint de health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.before_request
def before_request():
    """Executado antes de cada request"""
    db.session.get = lambda: db.session
    return None


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Limpa sessão após request"""
    db.session.remove()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria tabelas se não existirem
    
    print("="*60)
    print("🚀 Sistema de Automação de Lances - Compras.gov.br")
    print("="*60)
    print("⚠️  AVISO LEGAL:")
    print("Este sistema é para fins educacionais e de desenvolvimento.")
    print("Certifique-se de estar em conformidade com:")
    print("  • Termos de uso do Compras.gov.br")
    print("  • Edital da licitação")
    print("  • IN nº 03/2011 do MPOG")
    print("="*60)
    print("\n🌐 Acesse: http://localhost:5000")
    print("📖 Documentação: README.md\n")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
