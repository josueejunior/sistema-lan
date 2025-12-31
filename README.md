# Sistema de Automação de Lances - Compras.gov.br

🤖 Sistema automatizado para participação em disputas de licitações no portal Compras.gov.br, desenvolvido com Playwright, Flask e Python.

## ⚠️ AVISO LEGAL IMPORTANTE

**Este sistema é para fins educacionais e de desenvolvimento.**

Antes de utilizar este sistema em ambiente de produção, certifique-se de:

1. ✅ Estar em conformidade com o **edital da licitação**
2. ✅ Consultar a **IN nº 03/2011 do MPOG** sobre uso de sistemas automatizados
3. ✅ Verificar os **Termos de Uso** do portal Compras.gov.br
4. ✅ Obter autorização legal e regulatória necessária

**O uso inadequado pode resultar em:**
- ❌ Desclassificação da licitação
- ❌ Penalidades administrativas
- ❌ Bloqueio do acesso ao portal
- ❌ Consequências legais

## 📋 Características

### 🔐 Autenticação Persistente
- Login híbrido com suporte a CAPTCHA e MFA
- Sessão persistente via cookies (não precisa logar toda vez)
- Detecção automática de sessão expirada

### 📊 Estratégias de Lance

**1. 🎯 Sniper (Atirador)**
- Aguarda até os últimos segundos (configurável)
- Minimiza exposição da sua estratégia
- Ideal para disputas acirradas

**2. 📉 Escada (Gradual)**
- Lances imediatos e contínuos
- Redução gradual do preço
- Respeita intervalo mínimo do sistema

### 🛡️ Recursos de Segurança
- **Hard Stop**: Valor mínimo que nunca será ultrapassado
- **Delays Humanizados**: Randomização de tempos para evitar detecção
- **Anti-Bot Protection**: Remove flags de automação do navegador
- **Interval Respect**: Respeita intervalo mínimo entre lances do portal

### 📱 Interface Web
- Dashboard intuitivo em Flask
- Configuração de múltiplos itens simultâneos
- Monitoramento em tempo real
- Histórico de lances

## 🚀 Instalação

### Pré-requisitos
- Python 3.8+
- pip
- Navegador Chromium (instalado automaticamente pelo Playwright)

### Passo 1: Clone o Repositório
```bash
cd /home/josue/lance
```

### Passo 2: Crie Ambiente Virtual
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### Passo 3: Instale Dependências
```bash
pip install -r requirements.txt
playwright install chromium
```

### Passo 4: Configure Variáveis de Ambiente
```bash
cp .env.example .env
nano .env  # Edite conforme necessário
```

## 📖 Uso

### 1️⃣ Primeira Execução: Login Manual

Execute o script de autenticação para fazer o login inicial:

```bash
python3 auth/session_manager.py
```

Você verá:
1. Um navegador abrir automaticamente
2. Faça login no gov.br manualmente
3. Complete CAPTCHA e MFA se solicitados
4. Aguarde até estar na área logada
5. Pressione ENTER no terminal

✅ Os cookies serão salvos em `compras_session.json`

### 2️⃣ Iniciar a Aplicação Flask

```bash
python3 app/main.py
```

Acesse: **http://localhost:5000**

### 3️⃣ Configurar Itens

No dashboard:
1. Clique em "Configurar Novo Item"
2. Preencha:
   - Número do item
   - Descrição
   - Valor mínimo (hard stop)
   - Estratégia (Sniper ou Escada)
   - Intervalo de lance (%)
   - Tempo de gatilho (segundos)
3. Clique em "Ativar" para iniciar monitoramento

## 📁 Estrutura do Projeto

```
lance/
├── auth/
│   └── session_manager.py      # Gerenciamento de sessão com gov.br
├── monitor/
│   └── lance_monitor.py        # Monitoramento de lances em tempo real
├── engine/
│   └── lance_engine.py         # Lógica de decisão e execução
├── app/
│   └── main.py                 # Aplicação Flask (API + servidor)
├── templates/
│   └── dashboard.html          # Interface web
├── static/                     # Arquivos estáticos (CSS, JS)
├── requirements.txt            # Dependências Python
├── .env.example                # Exemplo de configuração
└── README.md                   # Este arquivo
```

## 🔧 Configuração Avançada

### Ajustar Seletores CSS

Os seletores CSS/XPath precisam ser ajustados conforme a estrutura real do portal:

**Arquivo:** `monitor/lance_monitor.py`

```python
# Exemplo: Ajustar seletor do lance atual
elemento = await self.page.query_selector('#seu-seletor-aqui')
```

**Arquivo:** `engine/lance_engine.py`

```python
# Exemplo: Ajustar seletor do campo de valor
input_valor = await self.page.query_selector('#campo-valor')
```

### Modificar Estratégias

Você pode criar estratégias customizadas editando `engine/lance_engine.py`:

```python
def _avaliar_estrategia_customizada(self, lance_atual, tempo_restante):
    # Sua lógica aqui
    pass
```

## 🧪 Testes

### Testar Autenticação
```bash
python3 auth/session_manager.py
```

### Testar Monitor (simulação)
```bash
python3 monitor/lance_monitor.py
```

### Testar Engine (simulação)
```bash
python3 engine/lance_engine.py
```

## 🐛 Solução de Problemas

### ❌ "Sessão expirada"
**Solução:** Execute novamente o `session_manager.py` para refazer o login.

### ❌ "Seletor não encontrado"
**Solução:** Ajuste os seletores CSS conforme a estrutura real da página. Use DevTools do navegador (F12) para inspecionar elementos.

### ❌ "Lance rejeitado"
**Solução:** 
- Verifique se o intervalo mínimo foi respeitado
- Confirme que o valor está acima do mínimo do sistema
- Verifique se não está em período de "random time" do pregão

### ❌ Navegador não abre
**Solução:**
```bash
playwright install chromium
```

## 📚 Referências Técnicas

### Arquitetura de Componentes

```
┌─────────────────┐
│  Flask Web UI   │  ← Interface do usuário
└────────┬────────┘
         │
┌────────▼────────┐
│  SessionManager │  ← Autenticação gov.br
└────────┬────────┘
         │
┌────────▼────────┐
│  MonitorLances  │  ← Observa mudanças na página
└────────┬────────┘
         │
┌────────▼────────┐
│  EngineDecisao  │  ← Decide se/quando dar lance
└────────┬────────┘
         │
┌────────▼────────┐
│ ExecutorLances  │  ← Executa ação na página
└─────────────────┘
```

### Fluxo de Execução

1. **Login Manual** → Salva cookies
2. **Inicia Monitor** → Observa lance_atual e tempo_restante
3. **Callback "lance_mudou"** → Aciona Engine de Decisão
4. **Engine avalia** → Retorna {deve_dar_lance: true/false, valor}
5. **Executor envia** → Preenche campo e clica botão
6. **Registra histórico** → Salva no banco de dados (ou arquivo)

## 🤝 Contribuições

Este é um projeto educacional. Contribuições são bem-vindas:

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m 'Adiciona nova funcionalidade'`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

## 📄 Licença

Este projeto é fornecido "como está", sem garantias de qualquer tipo.

**Uso por sua conta e risco.**

## 📞 Suporte

Para dúvidas técnicas:
- Consulte a documentação do [Playwright](https://playwright.dev/python/)
- Verifique a documentação do [Flask](https://flask.palletsprojects.com/)

## 🎯 Roadmap

- [ ] Suporte a múltiplos pregões simultâneos
- [ ] Integração com Telegram para alertas
- [ ] Dashboard com gráficos em tempo real
- [ ] Modo "Treino" com dados simulados
- [ ] Export de relatórios em PDF
- [ ] Backup automático de sessões

---

**Desenvolvido para fins educacionais** | Última atualização: Dezembro 2025
