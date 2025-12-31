"""
Banco de Dados para Multi-tenancy
Gerencia usuários, sessões e robôs independentes
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json
from typing import Optional, List, Dict

db = SQLAlchemy()


class Usuario(db.Model):
    """Modelo de Usuário"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.now)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    sessoes = db.relationship('Sessao', backref='usuario', lazy=True, cascade='all, delete-orphan')
    robos = db.relationship('RoboConfig', backref='usuario', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'criado_em': self.criado_em.isoformat(),
            'ativo': self.ativo
        }


class Sessao(db.Model):
    """Modelo de Sessão (Cookies + LocalStorage)"""
    __tablename__ = 'sessoes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Cookies e localStorage em JSON
    cookies_json = db.Column(db.Text, nullable=True)
    localstorage_json = db.Column(db.Text, nullable=True)
    
    # Metadados
    criado_em = db.Column(db.DateTime, default=datetime.now)
    atualizado_em = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    expira_em = db.Column(db.DateTime, nullable=True)
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    
    def salvar_cookies(self, cookies: List[Dict]):
        """Salva cookies em formato JSON"""
        self.cookies_json = json.dumps(cookies)
        self.atualizado_em = datetime.now()
    
    def obter_cookies(self) -> Optional[List[Dict]]:
        """Recupera cookies do JSON"""
        if self.cookies_json:
            return json.loads(self.cookies_json)
        return None
    
    def salvar_localstorage(self, storage: Dict):
        """Salva localStorage em formato JSON"""
        self.localstorage_json = json.dumps(storage)
        self.atualizado_em = datetime.now()
    
    def obter_localstorage(self) -> Optional[Dict]:
        """Recupera localStorage do JSON"""
        if self.localstorage_json:
            return json.loads(self.localstorage_json)
        return None
    
    def esta_valido(self) -> bool:
        """Verifica se sessão ainda é válida"""
        if not self.ativo:
            return False
        
        if self.expira_em and datetime.now() > self.expira_em:
            return False
        
        return True
    
    def renovar(self, dias_expiracao: int = 7):
        """Renova data de expiração"""
        self.expira_em = datetime.now() + timedelta(days=dias_expiracao)
        self.atualizado_em = datetime.now()
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'criado_em': self.criado_em.isoformat(),
            'atualizado_em': self.atualizado_em.isoformat(),
            'expira_em': self.expira_em.isoformat() if self.expira_em else None,
            'ativo': self.ativo,
            'valido': self.esta_valido()
        }


class RoboConfig(db.Model):
    """Modelo de Configuração de Robô"""
    __tablename__ = 'robo_config'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Informações do item
    numero_item = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    url_item = db.Column(db.String(500), nullable=True)
    
    # Configurações de lance
    valor_minimo = db.Column(db.Float, nullable=False)
    estrategia = db.Column(db.String(20), default='sniper')  # sniper ou escada
    intervalo_lance = db.Column(db.Float, default=1.0)  # percentual
    tempo_gatilho = db.Column(db.Integer, default=60)  # segundos
    
    # Status
    ativo = db.Column(db.Boolean, default=False)
    rodando = db.Column(db.Boolean, default=False)
    
    # Histórico
    criado_em = db.Column(db.DateTime, default=datetime.now)
    iniciado_em = db.Column(db.DateTime, nullable=True)
    parado_em = db.Column(db.DateTime, nullable=True)
    
    # Estatísticas
    total_lances = db.Column(db.Integer, default=0)
    lances_aceitos = db.Column(db.Integer, default=0)
    lances_rejeitados = db.Column(db.Integer, default=0)
    
    # Relacionamento
    historico = db.relationship('HistoricoLance', backref='robo', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'numero_item': self.numero_item,
            'descricao': self.descricao,
            'valor_minimo': self.valor_minimo,
            'estrategia': self.estrategia,
            'intervalo_lance': self.intervalo_lance,
            'tempo_gatilho': self.tempo_gatilho,
            'ativo': self.ativo,
            'rodando': self.rodando,
            'criado_em': self.criado_em.isoformat(),
            'total_lances': self.total_lances,
            'lances_aceitos': self.lances_aceitos,
            'lances_rejeitados': self.lances_rejeitados
        }


class HistoricoLance(db.Model):
    """Registro de cada lance enviado"""
    __tablename__ = 'historico_lance'
    
    id = db.Column(db.Integer, primary_key=True)
    robo_id = db.Column(db.Integer, db.ForeignKey('robo_config.id'), nullable=False)
    
    # Detalhes do lance
    valor_proposto = db.Column(db.Float, nullable=False)
    valor_anterior = db.Column(db.Float, nullable=True)
    
    # Resultado
    sucesso = db.Column(db.Boolean, default=False)
    motivo = db.Column(db.String(255), nullable=True)
    
    # Timing
    timestamp = db.Column(db.DateTime, default=datetime.now)
    tempo_restante = db.Column(db.Integer, nullable=True)
    
    # Tipo de execução
    tipo = db.Column(db.String(20))  # 'sniper', 'escada', 'manual'
    
    def to_dict(self):
        return {
            'id': self.id,
            'robo_id': self.robo_id,
            'valor_proposto': self.valor_proposto,
            'valor_anterior': self.valor_anterior,
            'sucesso': self.sucesso,
            'motivo': self.motivo,
            'timestamp': self.timestamp.isoformat(),
            'tempo_restante': self.tempo_restante,
            'tipo': self.tipo
        }


# ============================================================================
# GERENCIADOR DE BANCO DE DADOS
# ============================================================================

class DatabaseManager:
    """Gerencia operações de banco de dados"""
    
    @staticmethod
    def criar_usuario(nome: str, email: str, senha_hash: str) -> Usuario:
        """Cria novo usuário"""
        usuario = Usuario(
            nome=nome,
            email=email,
            senha_hash=senha_hash
        )
        db.session.add(usuario)
        db.session.commit()
        return usuario
    
    @staticmethod
    def obter_usuario(usuario_id: int) -> Optional[Usuario]:
        """Obtém usuário por ID"""
        return Usuario.query.get(usuario_id)
    
    @staticmethod
    def obter_usuario_por_email(email: str) -> Optional[Usuario]:
        """Obtém usuário por email"""
        return Usuario.query.filter_by(email=email).first()
    
    @staticmethod
    def criar_sessao(usuario_id: int, dias_expiracao: int = 7) -> Sessao:
        """Cria nova sessão"""
        sessao = Sessao(usuario_id=usuario_id)
        sessao.renovar(dias_expiracao)
        db.session.add(sessao)
        db.session.commit()
        return sessao
    
    @staticmethod
    def obter_sessao_ativa(usuario_id: int) -> Optional[Sessao]:
        """Obtém sessão ativa do usuário"""
        sessoes = Sessao.query.filter_by(usuario_id=usuario_id, ativo=True).all()
        for sessao in sessoes:
            if sessao.esta_valido():
                return sessao
        return None
    
    @staticmethod
    def criar_robo(usuario_id: int, configuracao: Dict) -> RoboConfig:
        """Cria nova configuração de robô"""
        robo = RoboConfig(
            usuario_id=usuario_id,
            numero_item=configuracao['numero_item'],
            descricao=configuracao['descricao'],
            valor_minimo=configuracao['valor_minimo'],
            estrategia=configuracao.get('estrategia', 'sniper'),
            intervalo_lance=configuracao.get('intervalo_lance', 1.0),
            tempo_gatilho=configuracao.get('tempo_gatilho', 60)
        )
        db.session.add(robo)
        db.session.commit()
        return robo
    
    @staticmethod
    def obter_robo(robo_id: int) -> Optional[RoboConfig]:
        """Obtém configuração de robô"""
        return RoboConfig.query.get(robo_id)
    
    @staticmethod
    def listar_robos(usuario_id: int) -> List[RoboConfig]:
        """Lista todos os robôs do usuário"""
        return RoboConfig.query.filter_by(usuario_id=usuario_id).all()
    
    @staticmethod
    def listar_robos_ativos(usuario_id: int) -> List[RoboConfig]:
        """Lista robôs ativos e rodando"""
        return RoboConfig.query.filter_by(
            usuario_id=usuario_id,
            ativo=True,
            rodando=True
        ).all()
    
    @staticmethod
    def registrar_lance(robo_id: int, valor_proposto: float, sucesso: bool, **kwargs) -> HistoricoLance:
        """Registra um lance no histórico"""
        robo = RoboConfig.query.get(robo_id)
        
        lance = HistoricoLance(
            robo_id=robo_id,
            valor_proposto=valor_proposto,
            sucesso=sucesso,
            **kwargs
        )
        
        db.session.add(lance)
        
        # Atualiza estatísticas do robô
        robo.total_lances += 1
        if sucesso:
            robo.lances_aceitos += 1
        else:
            robo.lances_rejeitados += 1
        
        db.session.commit()
        return lance
    
    @staticmethod
    def obter_historico_robo(robo_id: int, limite: int = 100) -> List[HistoricoLance]:
        """Obtém histórico de lances de um robô"""
        return HistoricoLance.query.filter_by(robo_id=robo_id).order_by(
            HistoricoLance.timestamp.desc()
        ).limit(limite).all()


if __name__ == "__main__":
    print("Banco de dados configurado com SQLAlchemy")
    print("Use db.create_all() para criar as tabelas")
