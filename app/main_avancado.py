"""
Aplicação Flask Avançada - Com WebSocket, Logs Realtime e Controle de Pânico
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import os
from datetime import datetime, timedelta
import asyncio
from threading import Thread
import json
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.environ.get('SECRET_KEY', 'sua-chave-secreta-aqui')
CORS(app)

# Inicializar WebSocket
socketio = SocketIO(app, cors_allowed_origins="*")

# Estado global
sistema_estado = {
    'sessao_ativa': False,
    'ultimo_login': None,
    'itens_monitorados': [],
    'historico_lances': [],
    'panico_ativado': False,
    'heartbeat_status': {
        'vivo': True,
        'ultima_verificacao': None,
        'uptime_segundos': 0
    }
}

# Clientes conectados via WebSocket
clientes_conectados = set()


# ============================================================================
# EVENTOS WEBSOCKET
# ============================================================================

@socketio.on('connect')
def ao_conectar(auth):
    """Quando um cliente se conecta"""
    client_id = request.sid
    clientes_conectados.add(client_id)
    
    logger.info(f"✅ Cliente conectado: {client_id}")
    emit('status', {
        'mensagem': 'Conectado ao servidor',
        'timestamp': datetime.now().isoformat()
    })


@socketio.on('disconnect')
def ao_desconectar():
    """Quando um cliente se desconecta"""
    client_id = request.sid
    clientes_conectados.discard(client_id)
    
    logger.info(f"❌ Cliente desconectado: {client_id}")


@socketio.on('solicitar_logs')
def ao_solicitar_logs(data):
    """Cliente solicita histórico de logs"""
    quantidade = data.get('quantidade', 100)
    
    # TODO: Integrar com LoggerRealtime
    # ultimos_logs = logger_realtime.obter_ultimos_logs(quantidade)
    
    emit('logs', {
        'logs': [],
        'total': 0
    })


# ============================================================================
# FUNÇÕES DE TRANSMISSÃO
# ============================================================================

def transmitir_log(mensagem: str, nivel: str = 'info', dados: dict = None):
    """
    Transmite log para todos os clientes conectados
    
    Args:
        mensagem: Mensagem do log
        nivel: debug, info, warning, error, critical
        dados: Dados adicionais
    """
    log_event = {
        'timestamp': datetime.now().isoformat(),
        'nivel': nivel,
        'mensagem': mensagem,
        'dados': dados or {}
    }
    
    socketio.emit('novo_log', log_event)
    logger.log(
        getattr(logging, nivel.upper()),
        mensagem
    )


def transmitir_atualizacao_status():
    """Transmite status do sistema para todos os clientes"""
    socketio.emit('atualizacao_status', {
        'sessao_ativa': sistema_estado['sessao_ativa'],
        'panico_ativado': sistema_estado['panico_ativado'],
        'itens_ativos': len([i for i in sistema_estado['itens_monitorados'] if i.get('ativo')]),
        'total_lances': len(sistema_estado['historico_lances']),
        'heartbeat': sistema_estado['heartbeat_status'],
        'timestamp': datetime.now().isoformat()
    })


def transmitir_heartbeat(status: dict):
    """Transmite heartbeat para clientes"""
    socketio.emit('heartbeat', {
        'status': status,
        'timestamp': datetime.now().isoformat()
    })


# ============================================================================
# ROTAS HTTP
# ============================================================================

@app.route('/')
def index():
    """Página principal"""
    return render_template('dashboard_avancado.html')


@app.route('/api/status')
def api_status():
    """Status do sistema"""
    return jsonify({
        'success': True,
        'data': {
            'sessao_ativa': sistema_estado['sessao_ativa'],
            'panico_ativado': sistema_estado['panico_ativado'],
            'itens_ativos': len([i for i in sistema_estado['itens_monitorados'] if i.get('ativo')]),
            'total_lances': len(sistema_estado['historico_lances']),
            'heartbeat': sistema_estado['heartbeat_status']
        }
    })


@app.route('/api/panico', methods=['POST'])
def api_ativar_panico():
    """
    Ativa botão de pânico - para TODO o robô imediatamente
    """
    try:
        sistema_estado['panico_ativado'] = True
        
        # Transmite para todos os clientes
        transmitir_log(
            "🚨 BOTÃO DE PÂNICO ATIVADO! Robô parado imediatamente!",
            "critical"
        )
        
        transmitir_atualizacao_status()
        
        return jsonify({
            'success': True,
            'message': '🚨 Pânico ativado! Todas as operações pausadas.'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/panico/cancelar', methods=['POST'])
def api_cancelar_panico():
    """
    Cancela o botão de pânico
    """
    try:
        sistema_estado['panico_ativado'] = False
        
        transmitir_log(
            "✅ Pânico cancelado. Sistema retomando operação.",
            "info"
        )
        
        transmitir_atualizacao_status()
        
        return jsonify({
            'success': True,
            'message': '✅ Pânico cancelado. Sistema pronto para retomar.'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/logs/ultimos')
def api_ultimos_logs():
    """Retorna últimos logs"""
    quantidade = request.args.get('quantidade', 100, type=int)
    
    # TODO: Integrar com LoggerRealtime
    
    return jsonify({
        'success': True,
        'data': [],
        'total': 0
    })


@app.route('/api/itens', methods=['GET', 'POST'])
def api_itens():
    """GET: Lista itens | POST: Adiciona item"""
    
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'data': sistema_estado['itens_monitorados']
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Valida
            required_fields = ['numero_item', 'descricao', 'valor_minimo']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Campo obrigatório: {field}'
                    }), 400
            
            novo_item = {
                'id': len(sistema_estado['itens_monitorados']) + 1,
                'numero_item': data['numero_item'],
                'descricao': data['descricao'],
                'valor_minimo': float(data['valor_minimo']),
                'estrategia': data.get('estrategia', 'sniper'),
                'intervalo_lance': float(data.get('intervalo_lance', 1.0)),
                'tempo_gatilho': int(data.get('tempo_gatilho', 60)),
                'ativo': False,
                'lance_atual': None,
                'meu_ultimo_lance': None,
                'criado_em': datetime.now().isoformat()
            }
            
            sistema_estado['itens_monitorados'].append(novo_item)
            
            transmitir_log(
                f"✅ Item {novo_item['numero_item']} adicionado",
                "info",
                {'item_id': novo_item['id']}
            )
            
            return jsonify({
                'success': True,
                'message': 'Item adicionado',
                'data': novo_item
            })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


@app.route('/api/itens/<int:item_id>/toggle', methods=['POST'])
def api_toggle_item(item_id):
    """Ativa/Desativa item"""
    
    item = next((i for i in sistema_estado['itens_monitorados'] if i['id'] == item_id), None)
    
    if not item:
        return jsonify({
            'success': False,
            'error': 'Item não encontrado'
        }), 404
    
    # Verifica se sistema está em pânico
    if sistema_estado['panico_ativado'] and not item['ativo']:
        return jsonify({
            'success': False,
            'error': '🚨 Sistema em pânico! Não é possível ativar itens.'
        }), 403
    
    item['ativo'] = not item['ativo']
    
    transmitir_log(
        f"{'▶️ Item ativado' if item['ativo'] else '⏸️ Item pausado'}: {item['numero_item']}",
        "info",
        {'item_id': item_id}
    )
    
    transmitir_atualizacao_status()
    
    return jsonify({
        'success': True,
        'message': f'Item {"ativado" if item["ativo"] else "pausado"}',
        'data': item
    })


@app.route('/api/lance/manual', methods=['POST'])
def api_lance_manual():
    """Executa lance manual"""
    
    try:
        if sistema_estado['panico_ativado']:
            return jsonify({
                'success': False,
                'error': '🚨 Sistema em pânico! Lances manuais desativados.'
            }), 403
        
        data = request.get_json()
        item_id = data.get('item_id')
        valor = data.get('valor')
        
        if not item_id or not valor:
            return jsonify({
                'success': False,
                'error': 'item_id e valor obrigatórios'
            }), 400
        
        lance = {
            'id': len(sistema_estado['historico_lances']) + 1,
            'item_id': item_id,
            'valor': float(valor),
            'tipo': 'manual',
            'timestamp': datetime.now().isoformat(),
            'sucesso': True
        }
        
        sistema_estado['historico_lances'].append(lance)
        
        transmitir_log(
            f"💰 Lance manual enviado: R$ {valor}",
            "info",
            {'item_id': item_id, 'valor': valor}
        )
        
        return jsonify({
            'success': True,
            'message': 'Lance enviado',
            'data': lance
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Robô de Lances - Dashboard Avançado")
    print("=" * 60)
    print("\n✨ Recursos:")
    print("  • WebSocket para logs em tempo real")
    print("  • Botão de pânico para emergências")
    print("  • Heartbeat monitor (via integração)")
    print("  • Multi-threading de itens (via integração)")
    print("  • Pós-lance com inteligência comercial (via integração)")
    print("\n🌐 Acesse: http://localhost:5000")
    print("=" * 60 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
