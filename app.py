import os
from datetime import datetime, timedelta, time
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, EmailField, SelectField, DateTimeField, SubmitField, BooleanField, SelectMultipleField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from flask_migrate import Migrate
from sqlalchemy import and_, select, func
from flask_wtf.csrf import generate_csrf

# Configuração da aplicação
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-aleatoria-para-ambiente-de-desenvolvimento'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///barbearia.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialização de extensões
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
csrf = CSRFProtect(app)  # Adiciona proteção CSRF

# Modelos de Dados
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20), index=True)
    is_barbeiro = db.Column(db.Boolean, default=False, index=True)
    pontos_fidelidade = db.Column(db.Integer, default=0)  # Pontos do programa de fidelidade
    agendamentos = db.relationship('Agendamento', foreign_keys='Agendamento.cliente_id', backref='cliente', lazy=True)
    agendamentos_barbeiro = db.relationship('Agendamento', foreign_keys='Agendamento.barbeiro_id', backref='barbeiro', lazy=True)
    servicos = db.relationship('Servico', secondary='barbeiro_servico', backref='barbeiros')

    @property
    def senha(self):
        raise AttributeError('senha não é um atributo legível')

    @senha.setter
    def senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

class Servico(db.Model):
    __tablename__ = 'servicos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    preco = db.Column(db.Float, nullable=False)
    preco_sem_agendamento = db.Column(db.Float)  # Preço sem agendamento (40% a mais)
    duracao = db.Column(db.Integer, nullable=False)  # em minutos
    agendamentos_diretos = db.relationship('Agendamento', backref='servico_principal', foreign_keys='Agendamento.servico_id', lazy=True)
    agendamentos = db.relationship('Agendamento', secondary='agendamento_servico', backref='servicos_adicionais')

class Agendamento(db.Model):
    __tablename__ = 'agendamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(20), default='pendente', index=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    barbeiro_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    servico_id = db.Column(db.Integer, db.ForeignKey('servicos.id'), nullable=False)
    duracao_total = db.Column(db.Integer, default=0)  # Duração total em minutos (soma de todos os serviços)
    valor_total = db.Column(db.Float, default=0.0)  # Valor total do agendamento
    finalizado = db.Column(db.Boolean, default=False, index=True)  # Indica se o serviço foi finalizado
    finalizado_em = db.Column(db.DateTime, nullable=True)  # Data e hora da finalização
    valor_sem_agendamento = db.Column(db.Float)  # Valor sem agendamento (40% a mais)
    
    # Índice composto para busca eficiente por data e barbeiro
    __table_args__ = (
        db.Index('idx_agendamento_barbeiro_data', 'barbeiro_id', 'data_hora'),
        db.Index('idx_agendamento_cliente_status', 'cliente_id', 'status'),
    )

# Tabela de associação muitos-para-muitos
barbeiro_servico = db.Table('barbeiro_servico',
    db.Column('barbeiro_id', db.Integer, db.ForeignKey('usuarios.id'), primary_key=True),
    db.Column('servico_id', db.Integer, db.ForeignKey('servicos.id'), primary_key=True)
)

# Tabela de associação muitos-para-muitos para agendamentos e serviços
agendamento_servico = db.Table('agendamento_servico',
    db.Column('agendamento_id', db.Integer, db.ForeignKey('agendamentos.id'), primary_key=True),
    db.Column('servico_id', db.Integer, db.ForeignKey('servicos.id'), primary_key=True)
)

# Formulários
class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class RegistroForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(min=3, max=100)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    telefone = StringField('Telefone', validators=[DataRequired(), Length(min=10, max=20)])
    is_barbeiro = BooleanField('Sou barbeiro')
    submit = SubmitField('Cadastrar')

    def validate_email(self, field):
        if Usuario.query.filter_by(email=field.data).first():
            raise ValidationError('Email já está em uso')

class AgendamentoForm(FlaskForm):
    servico_id = SelectField('Serviço Principal', coerce=int, validators=[DataRequired()])
    servicos_adicionais = SelectMultipleField('Serviços Adicionais', coerce=int)
    barbeiro_id = SelectField('Barbeiro', coerce=int, validators=[DataRequired()])
    data_hora = DateTimeField('Data e Hora', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('Confirmar Agendamento')

class AdminLoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar como Administrador')

# Funções auxiliares
def verificar_disponibilidade(barbeiro_id, data_hora, duracao_total):
    """Verifica se um barbeiro está disponível em um determinado horário considerando a duração total dos serviços"""
    # Verifica se é dia útil (segunda a sábado)
    if data_hora.weekday() >= 6:  # 6 = domingo
        return False, "Não trabalhamos aos domingos"
    
    # Verifica horário de funcionamento (8:00-19:00)
    hora = data_hora.hour
    minuto = data_hora.minute
    hora_minuto = hora + (minuto / 60)
    
    # Verifica se está dentro do horário de funcionamento (8:00-19:00)
    horario_funcionamento = 8.0 <= hora_minuto < 19.0
    
    if not horario_funcionamento:
        return False, "Horário fora do expediente (8:00-19:00 de segunda a sábado)"
    
    # Verifica se não é no passado
    if data_hora < datetime.now():
        return False, "Não é possível agendar para horários no passado"
    
    # Verifica se o horário de término não ultrapassa o fechamento
    fim_agendamento = data_hora + timedelta(minutes=duracao_total)
    fim_hora = fim_agendamento.hour
    fim_minuto = fim_agendamento.minute
    fim_hora_minuto = fim_hora + (fim_minuto / 60)
    
    if fim_hora_minuto > 19.0:
        return False, "O horário de término ultrapassa nosso horário de funcionamento (19:00)"
    
    # Buscar agendamentos que possam conflitar
    agendamentos_conflitantes = Agendamento.query.filter(
        Agendamento.barbeiro_id == barbeiro_id,
        Agendamento.status.in_(['pendente', 'confirmado'])
    ).all()
    
    # Verificar conflitos manualmente
    for agendamento in agendamentos_conflitantes:
        inicio_existente = agendamento.data_hora
        duracao_existente = agendamento.duracao_total or 30  # Duração padrão de 30 minutos
        fim_existente = inicio_existente + timedelta(minutes=duracao_existente)
        
        # Verifica se há sobreposição
        if (data_hora < fim_existente and fim_agendamento > inicio_existente):
            return False, "Barbeiro já tem um agendamento neste horário"
    
    return True, "Horário disponível"

def listar_horarios_disponiveis(barbeiro_id, data_selecionada, duracao=30):
    """
    Lista todos os horários disponíveis para um barbeiro em uma data específica,
    considerando o horário de funcionamento da barbearia em intervalos de 30 minutos.
    """
    try:
        # Converte a data string para objeto date
        if isinstance(data_selecionada, str):
            try:
                data_selecionada = datetime.strptime(data_selecionada, '%Y-%m-%d').date()
            except ValueError:
                return {"error": "Formato de data inválido. Use YYYY-MM-DD"}, 400
        
        # Verifica se a data é um domingo
        if data_selecionada.weekday() == 6:  # 6=domingo
            return {"error": "Não trabalhamos aos domingos"}, 400
        
        # Verifica se a data está no passado
        hoje = datetime.now().date()
        if data_selecionada < hoje:
            return {"error": "Não é possível agendar para datas passadas"}, 400
        
        # Horário de funcionamento: 8:00-19:00 com intervalos de 30 minutos
        horarios_possiveis = []
        
        # Gera todos os horários possíveis em intervalos de 30 minutos das 8:00 às 19:00
        for hora in range(8, 19):
            for minuto in [0, 30]:
                # Não adicionar 19:00, pois é horário de fechamento
                if hora == 19 and minuto == 0:
                    continue
                
                horario = datetime.combine(data_selecionada, time(hora, minuto))
                
                # Verifica se o horário resultante não está no passado
                if horario > datetime.now():
                    # Verifica se o barbeiro está disponível neste horário
                    disponivel, mensagem = verificar_disponibilidade(barbeiro_id, horario, duracao)
                    if disponivel:
                        horarios_possiveis.append({
                            "hora": horario.strftime('%H:%M'),
                            "disponivel": True
                        })
                    else:
                        horarios_possiveis.append({
                            "hora": horario.strftime('%H:%M'),
                            "disponivel": False,
                            "motivo": mensagem
                        })
                else:
                    horarios_possiveis.append({
                        "hora": horario.strftime('%H:%M'),
                        "disponivel": False,
                        "motivo": "Horário já passou"
                    })
        
        # Organiza os horários em manhã e tarde
        manha = [h for h in horarios_possiveis if int(h["hora"].split(":")[0]) < 12]
        tarde = [h for h in horarios_possiveis if int(h["hora"].split(":")[0]) >= 12]
        
        return {
            "manha": manha,
            "tarde": tarde
        }, 200
    except Exception as e:
        app.logger.error(f"Erro ao listar horários: {str(e)}")
        return {"error": f"Erro ao processar horários: {str(e)}"}, 500

@app.route('/verificar_disponibilidade')
@login_required
def verificar_disponibilidade_rota():
    """Endpoint para verificar horários disponíveis para um barbeiro em uma data"""
    barbeiro_id = request.args.get('barbeiro_id', type=int)
    data = request.args.get('data')
    duracao_total = request.args.get('duracao_total', default=30, type=int)  # Duração em minutos
    
    if not barbeiro_id or not data:
        return jsonify({'success': False, 'message': 'Barbeiro e data são obrigatórios'}), 400
    
    try:
        data_obj = datetime.strptime(data, '%Y-%m-%d').date()
        horarios, status = listar_horarios_disponiveis(barbeiro_id, data_obj, duracao_total)
        
        if status != 200:
            return jsonify({'success': False, 'message': horarios.get('error', 'Erro ao listar horários')}), status
        
        return jsonify({
            'success': True,
            'horarios': horarios,
            'duracao': duracao_total
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Configuração do Login Manager
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.context_processor
def inject_admin_check():
    return {'is_admin': is_admin}

# Fornece o token CSRF para os templates
@app.context_processor
def inject_csrf_token():
    return {'csrf_token': generate_csrf()}

# Rotas
@app.route('/')
def index():
    # Busca os serviços do banco de dados para exibir na página inicial
    servicos = Servico.query.order_by(Servico.nome).all()
    
    # Organiza os serviços em um dicionário para facilitar acesso
    servicos_dict = {}
    for servico in servicos:
        servicos_dict[servico.nome.lower()] = {
            'preco': servico.preco,
            'preco_sem_agendamento': servico.preco_sem_agendamento or servico.preco * 1.4,
            'descricao': servico.descricao,
            'duracao': servico.duracao
        }
    
    # Seleciona serviços em destaque para a página inicial
    servicos_destaque = {
        'corte_social': next((s for s in servicos if 'social' in s.nome.lower() or 'degrad' in s.nome.lower()), None),
        'barba': next((s for s in servicos if 'barba' in s.nome.lower() and not 'corte' in s.nome.lower()), None),
        'hidratacao': next((s for s in servicos if 'hidrata' in s.nome.lower()), None),
        'combo': next((s for s in servicos if 'combo' in s.nome.lower() or ('corte' in s.nome.lower() and 'barba' in s.nome.lower())), None)
    }
    
    # Remove serviços não encontrados
    servicos_destaque = {k: v for k, v in servicos_destaque.items() if v is not None}
    
    return render_template('index.html', servicos=servicos, servicos_destaque=servicos_destaque)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistroForm()
    if form.validate_on_submit():
        usuario = Usuario(
            nome=form.nome.data,
            email=form.email.data,
            telefone=form.telefone.data,
            is_barbeiro=form.is_barbeiro.data
        )
        usuario.senha = form.senha.data
        
        try:
            db.session.add(usuario)
            db.session.commit()
            flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar. Tente novamente.', 'error')
    
    return render_template('registro.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        if usuario and usuario.verificar_senha(form.senha.data):
            login_user(usuario)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        flash('Email ou senha inválidos', 'error')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_barbeiro:
        agendamentos = Agendamento.query.filter_by(
            barbeiro_id=current_user.id
        ).order_by(Agendamento.data_hora).all()
        return render_template('dashboard_barbeiro.html', agendamentos=agendamentos)
    else:
        agendamentos = Agendamento.query.filter_by(
            cliente_id=current_user.id
        ).order_by(Agendamento.data_hora).all()
        return render_template('dashboard_cliente.html', agendamentos=agendamentos)

@app.route('/central')
@login_required
def central_agendamentos():
    # Verifica se o usuário é um barbeiro
    if not current_user.is_barbeiro:
        flash('Acesso negado. Área restrita para barbeiros.', 'error')
        return redirect(url_for('dashboard'))
    
    # Obtém todos os agendamentos, não apenas os do barbeiro logado
    agendamentos = Agendamento.query.order_by(Agendamento.data_hora).all()
    
    # Obtém a lista de todos os barbeiros
    barbeiros = Usuario.query.filter_by(is_barbeiro=True).all()
    
    return render_template(
        'central_agendamentos.html', 
        agendamentos=agendamentos, 
        barbeiros=barbeiros
    )

@app.route('/agendar', methods=['GET', 'POST'])
@login_required
def agendar():
    form = AgendamentoForm()
    # Preenche as opções dos serviços
    servicos = Servico.query.order_by(Servico.nome).all()
    form.servico_id.choices = [(s.id, f"{s.nome} - R${s.preco:.2f}") for s in servicos]
    form.servicos_adicionais.choices = [(s.id, f"{s.nome} - R${s.preco:.2f}") for s in servicos]
    
    # Se o cliente_id foi fornecido e o usuário é um barbeiro
    cliente_id = request.args.get('cliente_id', type=int)
    cliente = None
    if cliente_id and current_user.is_barbeiro:
        cliente = Usuario.query.filter_by(id=cliente_id, is_barbeiro=False).first()
        if not cliente:
            flash('Cliente não encontrado', 'error')
            return redirect(url_for('dashboard'))
    
    # Se o usuário é barbeiro, só pode agendar para clientes
    if current_user.is_barbeiro and not cliente:
        form.barbeiro_id.choices = [(current_user.id, current_user.nome)]
        form.barbeiro_id.data = current_user.id
    else:
        # Mostrar todos os barbeiros
        barbeiros = Usuario.query.filter_by(is_barbeiro=True).order_by(Usuario.nome).all()
        form.barbeiro_id.choices = [(u.id, u.nome) for u in barbeiros]
    
    if form.validate_on_submit():
        # Obtém o serviço principal
        servico_principal = db.session.get(Servico, form.servico_id.data)
        
        # Calcula a duração total e valor total
        duracao_total = servico_principal.duracao
        valor_total = servico_principal.preco
        valor_sem_agendamento = servico_principal.preco_sem_agendamento or (servico_principal.preco * 1.4)
        
        # Verifica se serviços adicionais foram selecionados e calcula a duração e valor
        servicos_adicionais_ids = form.servicos_adicionais.data
        servicos_adicionais = []
        
        if servicos_adicionais_ids:
            servicos_adicionais = Servico.query.filter(Servico.id.in_(servicos_adicionais_ids)).all()
            for servico in servicos_adicionais:
                duracao_total += servico.duracao
                valor_total += servico.preco
                valor_sem_agendamento += servico.preco_sem_agendamento or (servico.preco * 1.4)
        
        disponivel, mensagem = verificar_disponibilidade(
            form.barbeiro_id.data,
            form.data_hora.data,
            duracao_total
        )
        
        if not disponivel:
            flash(mensagem, 'error')
            return redirect(url_for('agendar'))
        
        # Se o usuário é barbeiro e o cliente_id foi fornecido, agenda para o cliente
        if current_user.is_barbeiro and cliente:
            cliente_final_id = cliente.id
        else:
            cliente_final_id = current_user.id
        
        novo_agendamento = Agendamento(
            data_hora=form.data_hora.data,
            cliente_id=cliente_final_id,
            barbeiro_id=form.barbeiro_id.data,
            servico_id=form.servico_id.data,
            duracao_total=duracao_total,
            valor_total=valor_total,
            valor_sem_agendamento=valor_sem_agendamento
        )
        
        try:
            db.session.add(novo_agendamento)
            db.session.flush()  # Para obter o ID do agendamento antes do commit
            
            # Adiciona os serviços adicionais à tabela de relação
            for servico in servicos_adicionais:
                db.session.execute(agendamento_servico.insert().values(
                    agendamento_id=novo_agendamento.id,
                    servico_id=servico.id
                ))
            
            db.session.commit()
            
            # Obtém informações para as notificações
            cliente = Usuario.query.get(cliente_final_id)
            barbeiro = Usuario.query.get(form.barbeiro_id.data)
            
            # Mensagem detalhada com todos os serviços
            servicos_mensagem = f"{servico_principal.nome}"
            if servicos_adicionais:
                servicos_mensagem += " + " + ", ".join([s.nome for s in servicos_adicionais])
            
            # Calcular a economia
            economia = valor_sem_agendamento - valor_total
            
            # Adicionar mensagem para o cliente
            flash(f'Agendamento realizado com sucesso! Serviços: {servicos_mensagem}. Você economizou R${economia:.2f} realizando o agendamento!', 'success')
            
            # Notifica o barbeiro solicitado (via flash message se ele estiver logado)
            if current_user.id == barbeiro.id:
                flash(f'Você tem um novo agendamento com {cliente.nome} para {form.data_hora.data.strftime("%d/%m/%Y às %H:%M")}. Serviços: {servicos_mensagem}', 'info')
            
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao agendar. {str(e)}', 'error')
    
    return render_template('agendar.html', form=form, cliente=cliente)

@csrf.exempt
@app.route('/api/horarios_disponiveis')
@login_required
def api_horarios_disponiveis():
    """Endpoint para obter horários disponíveis para um barbeiro em uma data"""
    barbeiro_id = request.args.get('barbeiro_id', type=int)
    data = request.args.get('data')
    duracao = request.args.get('duracao', default=30, type=int)  # Duração em minutos, padrão 30min
    
    if not barbeiro_id or not data:
        return jsonify({'error': 'Parâmetros incompletos'}), 400
    
    try:
        data_obj = datetime.strptime(data, '%Y-%m-%d').date()
        resultado, status = listar_horarios_disponiveis(barbeiro_id, data_obj, duracao)
        
        if status != 200:
            return jsonify(resultado), status
        
        return jsonify({
            'horarios': resultado,
            'duracao': duracao,
            'mensagem': 'Horários disponíveis para agendamentos com duração de ' + str(duracao) + ' minutos'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@csrf.exempt
@app.route('/api/buscar_clientes')
@login_required
def api_buscar_clientes():
    """Endpoint para buscar clientes por nome ou telefone"""
    if not current_user.is_barbeiro:
        return jsonify({'error': 'Acesso negado'}), 403
    
    termo = request.args.get('termo', '')
    
    if not termo or len(termo) < 3:
        return jsonify({'error': 'Forneça pelo menos 3 caracteres para a busca'}), 400
    
    try:
        # Busca usuários por nome, telefone ou email (incluindo barbeiros e clientes)
        usuarios = Usuario.query.filter(
            db.or_(
                Usuario.nome.ilike(f'%{termo}%'),
                Usuario.telefone.ilike(f'%{termo}%'),
                Usuario.email.ilike(f'%{termo}%')
            )
        ).limit(15).all()
        
        # Formata os resultados, mostrando apenas clientes para agendamento
        resultados = [{
            'id': usuario.id,
            'nome': usuario.nome,
            'email': usuario.email,
            'telefone': usuario.telefone,
            'is_barbeiro': usuario.is_barbeiro
        } for usuario in usuarios if not usuario.is_barbeiro]  # Filtra depois da consulta
        
        # Log para depuração
        print(f"Busca por '{termo}' retornou {len(usuarios)} usuários, {len(resultados)} clientes")
        
        return jsonify({
            'clientes': resultados
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@csrf.exempt
@app.route('/api/enviar_lembrete_whatsapp/<int:agendamento_id>', methods=['POST'])
@login_required
def api_enviar_lembrete_whatsapp(agendamento_id):
    """Endpoint para preparar a mensagem de WhatsApp para um agendamento"""
    if not current_user.is_barbeiro:
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        # Busca o agendamento
        agendamento = db.session.get(Agendamento, agendamento_id)
        if not agendamento:
            return jsonify({'error': 'Agendamento não encontrado'}), 404
        
        # Verifica permissão
        if agendamento.barbeiro_id != current_user.id:
            return jsonify({'error': 'Você só pode enviar lembretes para seus próprios agendamentos'}), 403
        
        # Formato amigável para a data e hora
        data_formatada = agendamento.data_hora.strftime('%d/%m/%Y às %H:%M')
        
        # Formata a mensagem
        mensagem = f"Olá {agendamento.cliente.nome}! Este é um lembrete do seu agendamento na Barbearia Souza para {data_formatada}. Serviço: {agendamento.servico_principal.nome}. Aguardamos sua presença!"
        
        # Formata o número de telefone (remove caracteres não numéricos)
        telefone = ''.join(filter(str.isdigit, agendamento.cliente.telefone))
        
        # Verifica se o telefone é válido
        if not telefone:
            return jsonify({'error': 'Cliente não possui um número de telefone válido'}), 400
        
        # Se o telefone não começar com '55' (Brasil), adiciona
        if not telefone.startswith('55'):
            telefone = '55' + telefone
        
        # URL para a API do WhatsApp Web
        url = f"https://wa.me/{telefone}?text={mensagem}"
        
        return jsonify({
            'url': url,
            'mensagem': mensagem,
            'telefone': telefone
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@csrf.exempt
@app.route('/agendamento/<int:id>/cancelar', methods=['POST'])
@login_required
def cancelar_agendamento(id):
    agendamento = db.session.get(Agendamento, id)
    if not agendamento:
        flash('Agendamento não encontrado', 'error')
        return redirect(url_for('dashboard'))
    
    # Verifica permissão
    if agendamento.cliente_id != current_user.id and agendamento.barbeiro_id != current_user.id:
        flash('Você não tem permissão para cancelar este agendamento', 'error')
        return redirect(url_for('dashboard'))
    
    # Verifica se pode ser cancelado
    if agendamento.data_hora < datetime.now():
        flash('Não é possível cancelar um agendamento passado', 'error')
        return redirect(url_for('dashboard'))
    
    if agendamento.status == 'cancelado':
        flash('Este agendamento já foi cancelado', 'warning')
        return redirect(url_for('dashboard'))
    
    try:
        agendamento.status = 'cancelado'
        db.session.commit()
        flash(f'Agendamento de {agendamento.cliente.nome} para {agendamento.data_hora.strftime("%d/%m/%Y às %H:%M")} cancelado com sucesso', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cancelar agendamento: {str(e)}', 'error')
    
    # Verifica se a requisição veio da central de agendamentos
    if request.referrer and 'central' in request.referrer:
        return redirect(url_for('central_agendamentos'))
    else:
        return redirect(url_for('dashboard'))

@csrf.exempt
@app.route('/agendamento/<int:id>/confirmar', methods=['POST'])
@login_required
def confirmar_agendamento(id):
    if not current_user.is_barbeiro:
        flash('Apenas barbeiros podem confirmar agendamentos', 'error')
        return redirect(url_for('dashboard'))
    
    agendamento = db.session.get(Agendamento, id)
    if not agendamento:
        flash('Agendamento não encontrado', 'error')
        return redirect(url_for('dashboard'))
    
    if agendamento.barbeiro_id != current_user.id:
        flash('Você só pode confirmar seus próprios agendamentos', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        agendamento.status = 'confirmado'
        db.session.commit()
        flash(f'Agendamento de {agendamento.cliente.nome} para {agendamento.data_hora.strftime("%d/%m/%Y às %H:%M")} confirmado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao confirmar agendamento: {str(e)}', 'error')
    
    # Verifica se a requisição veio da central de agendamentos
    if request.referrer and 'central' in request.referrer:
        return redirect(url_for('central_agendamentos'))
    else:
        return redirect(url_for('dashboard'))

@csrf.exempt
@app.route('/agendamento/<int:id>/finalizar', methods=['POST'])
@login_required
def finalizar_agendamento(id):
    if not current_user.is_barbeiro:
        flash('Apenas barbeiros podem finalizar agendamentos', 'error')
        return redirect(url_for('dashboard'))
    
    agendamento = db.session.get(Agendamento, id)
    if not agendamento:
        flash('Agendamento não encontrado', 'error')
        return redirect(url_for('dashboard'))
    
    if agendamento.barbeiro_id != current_user.id:
        flash('Você só pode finalizar seus próprios agendamentos', 'error')
        return redirect(url_for('dashboard'))
    
    if agendamento.status != 'confirmado':
        flash('Apenas agendamentos confirmados podem ser finalizados', 'warning')
        return redirect(url_for('dashboard'))
        
    try:
        # Atualiza o agendamento
        agendamento.finalizado = True
        agendamento.finalizado_em = datetime.now()
        agendamento.status = 'finalizado'
        
        # Incrementa pontos de fidelidade do cliente
        cliente = db.session.get(Usuario, agendamento.cliente_id)
        cliente.pontos_fidelidade += 1
        
        # Mensagem geral de sucesso
        mensagem_sucesso = f'Agendamento de {agendamento.cliente.nome} finalizado com sucesso. Ponto de fidelidade adicionado!'
        
        # Verifica se o cliente atingiu 10 pontos para ganhar um corte grátis
        if cliente.pontos_fidelidade >= 10:
            cliente.pontos_fidelidade = 0  # Zera os pontos após usar o benefício
            
            # Cria mensagem com todos os serviços realizados
            servicos_texto = agendamento.servico_principal.nome
            if agendamento.servicos_adicionais:
                servicos_extras = [s.nome for s in agendamento.servicos_adicionais]
                if servicos_extras:
                    servicos_texto += " + " + ", ".join(servicos_extras)
            
            mensagem_sucesso = f'Parabéns! Cliente {cliente.nome} completou 10 agendamentos e ganhou um corte grátis! Pontos de fidelidade zerados.'
        
        db.session.commit()
        flash(mensagem_sucesso, 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao finalizar agendamento: {str(e)}', 'error')
    
    # Verifica se a requisição veio da central de agendamentos
    if request.referrer and 'central' in request.referrer:
        return redirect(url_for('central_agendamentos'))
    else:
        return redirect(url_for('dashboard'))

@csrf.exempt
@app.route('/api/servicos-info')
@login_required
def api_servicos_info():
    """Endpoint para obter informações detalhadas sobre os serviços"""
    try:
        servicos = Servico.query.all()
        
        dados_servicos = {}
        for servico in servicos:
            dados_servicos[servico.id] = {
                'nome': servico.nome,
                'descricao': servico.descricao,
                'preco': float(servico.preco),
                'preco_sem_agendamento': float(servico.preco_sem_agendamento or 0),
                'duracao': servico.duracao
            }
        
        return jsonify({
            'servicos': dados_servicos
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Função para verificar se o usuário é administrador
def is_admin(user):
    """Verifica se o usuário é o administrador do sistema"""
    # Usando emails específicos como método temporário de identificação de admin
    return user.email in ['admin@barbearia.com', 'barbeariasouzaretro@gmail.com']

# Handlers de erro
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(405)
def method_not_allowed(e):
    flash('Operação não permitida. Verifique se está usando o método correto para esta ação.', 'danger')
    return redirect(request.referrer or url_for('dashboard'))

@app.errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    return render_template('500.html'), 500

# Rota para login de administrador
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # Se o usuário já estiver logado e for admin, redireciona para o painel admin
    if current_user.is_authenticated and is_admin(current_user):
        return redirect(url_for('admin_dashboard'))
    
    form = AdminLoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        
        # Verifica se o usuário existe, se a senha está correta e se é um administrador
        if usuario and usuario.verificar_senha(form.senha.data) and is_admin(usuario):
            login_user(usuario)
            flash('Login realizado com sucesso! Bem-vindo ao painel administrativo.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Credenciais inválidas ou você não é um administrador', 'danger')
    
    return render_template('admin_login.html', form=form)

# Rota do painel admin
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Verifica se o usuário é admin
    if not is_admin(current_user):
        flash('Acesso restrito. Você não é um administrador.', 'danger')
        return redirect(url_for('index'))
    
    # Estatísticas para o painel
    total_barbeiros = Usuario.query.filter_by(is_barbeiro=True).count()
    total_clientes = Usuario.query.filter_by(is_barbeiro=False).count()
    total_agendamentos_hoje = Agendamento.query.filter(
        func.date(Agendamento.data_hora) == datetime.now().date()
    ).count()
    total_agendamentos_pendentes = Agendamento.query.filter_by(status='pendente').count()
    total_servicos = Servico.query.count()
    
    # Lista de barbeiros para gerenciamento
    barbeiros = Usuario.query.filter_by(is_barbeiro=True).all()
    
    # Lista de serviços para gerenciamento
    servicos = Servico.query.all()
    
    return render_template(
        'admin_dashboard.html',
        total_barbeiros=total_barbeiros,
        total_clientes=total_clientes,
        total_agendamentos_hoje=total_agendamentos_hoje,
        total_agendamentos_pendentes=total_agendamentos_pendentes,
        total_servicos=total_servicos,
        barbeiros=barbeiros,
        servicos=servicos
    )

# Rota para criar um administrador (acesso protegido)
@app.route('/admin/criar', methods=['GET', 'POST'])
def criar_admin():
    # Verificar se já existe algum administrador
    admin_existente = Usuario.query.filter(
        (Usuario.email == 'admin@barbearia.com') | 
        (Usuario.email == 'barbeariasouzaretro@gmail.com')
    ).first()
    
    # Se já existir administrador e o usuário atual não for admin, bloquear acesso
    if admin_existente and not (current_user.is_authenticated and is_admin(current_user)):
        flash('Operação não permitida', 'danger')
        return redirect(url_for('index'))
    
    # Formulário simplificado para criar admin
    form = RegistroForm()
    
    if form.validate_on_submit():
        novo_admin = Usuario(
            nome=form.nome.data,
            email=form.email.data,
            telefone=form.telefone.data,
            is_barbeiro=form.is_barbeiro.data
        )
        novo_admin.senha = form.senha.data
        
        try:
            db.session.add(novo_admin)
            db.session.commit()
            flash(f'Administrador {novo_admin.nome} criado com sucesso!', 'success')
            
            # Se não estiver logado como admin, fazer login como o novo admin
            if not (current_user.is_authenticated and is_admin(current_user)):
                login_user(novo_admin)
            
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar administrador: {str(e)}', 'danger')
    
    return render_template('admin_criar.html', form=form)

# Rota para gerenciar barbeiros
@app.route('/admin/barbeiros')
@login_required
def admin_barbeiros():
    if not is_admin(current_user):
        flash('Acesso restrito. Você não é um administrador.', 'danger')
        return redirect(url_for('index'))
    
    barbeiros = Usuario.query.filter_by(is_barbeiro=True).all()
    servicos = Servico.query.all()
    return render_template('admin_barbeiros.html', barbeiros=barbeiros, servicos=servicos)

# Rota para adicionar barbeiro
@app.route('/admin/barbeiros/adicionar', methods=['POST'])
@login_required
def admin_barbeiros_adicionar():
    if not is_admin(current_user):
        flash('Acesso restrito. Você não é um administrador.', 'danger')
        return redirect(url_for('index'))
    
    try:
        nome = request.form.get('nome')
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        senha = request.form.get('senha')
        
        # Verifica se o email já existe
        if Usuario.query.filter_by(email=email).first():
            flash('Email já cadastrado', 'danger')
            return redirect(url_for('admin_barbeiros'))
        
        # Cria o novo barbeiro
        novo_barbeiro = Usuario(
            nome=nome,
            email=email,
            telefone=telefone,
            is_barbeiro=True
        )
        novo_barbeiro.senha = senha
        
        db.session.add(novo_barbeiro)
        db.session.commit()
        
        # Adiciona serviços selecionados
        servicos_ids = request.form.getlist('servicos[]')
        if servicos_ids:
            servicos = Servico.query.filter(Servico.id.in_(servicos_ids)).all()
            novo_barbeiro.servicos = servicos
            db.session.commit()
        
        flash('Barbeiro adicionado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao adicionar barbeiro: {str(e)}', 'danger')
    
    return redirect(url_for('admin_barbeiros'))

# Rota para editar barbeiro
@app.route('/admin/barbeiros/editar/<int:id>', methods=['POST'])
@login_required
def admin_barbeiros_editar(id):
    if not is_admin(current_user):
        flash('Acesso restrito. Você não é um administrador.', 'danger')
        return redirect(url_for('index'))
    
    try:
        barbeiro = db.session.get(Usuario, id)
        if not barbeiro:
            flash('Barbeiro não encontrado', 'danger')
            return redirect(url_for('admin_barbeiros'))
        
        # Atualiza os dados do barbeiro
        barbeiro.nome = request.form.get('nome')
        barbeiro.email = request.form.get('email')
        barbeiro.telefone = request.form.get('telefone')
        
        # Atualiza a senha se fornecida
        senha = request.form.get('senha')
        if senha:
            barbeiro.senha = senha
        
        db.session.commit()
        flash('Barbeiro atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar barbeiro: {str(e)}', 'danger')
    
    return redirect(url_for('admin_barbeiros'))

# Rota para excluir barbeiro
@app.route('/admin/barbeiros/excluir/<int:id>', methods=['POST'])
@login_required
def admin_barbeiros_excluir(id):
    if not is_admin(current_user):
        flash('Acesso restrito. Você não é um administrador.', 'danger')
        return redirect(url_for('index'))
    
    try:
        barbeiro = db.session.get(Usuario, id)
        if not barbeiro:
            flash('Barbeiro não encontrado', 'danger')
            return redirect(url_for('admin_barbeiros'))
        
        # Verifica se há agendamentos associados
        agendamentos = Agendamento.query.filter_by(barbeiro_id=id).all()
        if agendamentos:
            # Opcionalmente, pode excluir os agendamentos ou transferi-los
            for agendamento in agendamentos:
                db.session.delete(agendamento)
        
        db.session.delete(barbeiro)
        db.session.commit()
        flash('Barbeiro excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir barbeiro: {str(e)}', 'danger')
    
    return redirect(url_for('admin_barbeiros'))

# Rota para gerenciar serviços de um barbeiro
@app.route('/admin/barbeiros/servicos/<int:id>', methods=['POST'])
@login_required
def admin_barbeiros_servicos(id):
    if not is_admin(current_user):
        flash('Acesso restrito. Você não é um administrador.', 'danger')
        return redirect(url_for('index'))
    
    try:
        barbeiro = db.session.get(Usuario, id)
        if not barbeiro:
            flash('Barbeiro não encontrado', 'danger')
            return redirect(url_for('admin_barbeiros'))
        
        # Atualiza os serviços do barbeiro
        servicos_ids = request.form.getlist('servicos[]')
        servicos = Servico.query.filter(Servico.id.in_(servicos_ids)).all() if servicos_ids else []
        
        barbeiro.servicos = servicos
        db.session.commit()
        flash('Serviços do barbeiro atualizados com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar serviços do barbeiro: {str(e)}', 'danger')
    
    return redirect(url_for('admin_barbeiros'))

# Rota para adicionar serviço
@app.route('/admin/servicos/adicionar', methods=['POST'])
@login_required
def admin_servicos_adicionar():
    if not is_admin(current_user):
        flash('Acesso restrito. Você não é um administrador.', 'danger')
        return redirect(url_for('index'))
    
    try:
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        preco = float(request.form.get('preco'))
        duracao = int(request.form.get('duracao'))
        
        preco_sem_agendamento = request.form.get('preco_sem_agendamento')
        if not preco_sem_agendamento:
            # Cálculo automático (40% a mais)
            preco_sem_agendamento = preco * 1.4
        else:
            preco_sem_agendamento = float(preco_sem_agendamento)
        
        # Cria o novo serviço
        novo_servico = Servico(
            nome=nome,
            descricao=descricao,
            preco=preco,
            duracao=duracao,
            preco_sem_agendamento=preco_sem_agendamento
        )
        
        db.session.add(novo_servico)
        db.session.commit()
        flash('Serviço adicionado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao adicionar serviço: {str(e)}', 'danger')
    
    return redirect(url_for('admin_servicos'))

# Rota para editar serviço
@app.route('/admin/servicos/editar/<int:id>', methods=['POST'])
@login_required
def admin_servicos_editar(id):
    if not is_admin(current_user):
        flash('Acesso restrito. Você não é um administrador.', 'danger')
        return redirect(url_for('index'))
    
    try:
        servico = db.session.get(Servico, id)
        if not servico:
            flash('Serviço não encontrado', 'danger')
            return redirect(url_for('admin_servicos'))
        
        # Atualiza os dados do serviço
        servico.nome = request.form.get('nome')
        servico.descricao = request.form.get('descricao')
        servico.preco = float(request.form.get('preco'))
        servico.duracao = int(request.form.get('duracao'))
        
        preco_sem_agendamento = request.form.get('preco_sem_agendamento')
        if preco_sem_agendamento:
            servico.preco_sem_agendamento = float(preco_sem_agendamento)
        else:
            servico.preco_sem_agendamento = servico.preco * 1.4
        
        db.session.commit()
        flash('Serviço atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar serviço: {str(e)}', 'danger')
    
    return redirect(url_for('admin_servicos'))

# Rota para excluir serviço
@app.route('/admin/servicos/excluir/<int:id>', methods=['POST'])
@login_required
def admin_servicos_excluir(id):
    if not is_admin(current_user):
        flash('Acesso restrito. Você não é um administrador.', 'danger')
        return redirect(url_for('index'))
    
    try:
        servico = db.session.get(Servico, id)
        if not servico:
            flash('Serviço não encontrado', 'danger')
            return redirect(url_for('admin_servicos'))
        
        # Verifica se há agendamentos associados
        agendamentos = Agendamento.query.filter_by(servico_id=id).all()
        if agendamentos:
            flash('Este serviço não pode ser excluído pois existem agendamentos associados a ele.', 'warning')
            return redirect(url_for('admin_servicos'))
        
        db.session.delete(servico)
        db.session.commit()
        flash('Serviço excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir serviço: {str(e)}', 'danger')
    
    return redirect(url_for('admin_servicos'))

# Rota para gerenciar serviços
@app.route('/admin/servicos')
@login_required
def admin_servicos():
    if not is_admin(current_user):
        flash('Acesso restrito. Você não é um administrador.', 'danger')
        return redirect(url_for('index'))
    
    servicos = Servico.query.all()
    return render_template('admin_servicos.html', servicos=servicos)

# Rota para relatórios
@app.route('/admin/relatorios')
@login_required
def admin_relatorios():
    if not is_admin(current_user):
        flash('Acesso restrito. Você não é um administrador.', 'danger')
        return redirect(url_for('index'))
    
    # Dados para o relatório
    agendamentos = Agendamento.query.filter(
        Agendamento.status == 'finalizado'
    ).order_by(Agendamento.data_hora.desc()).all()
    
    # Cálculos de faturamento
    total_faturado = sum(a.valor_total for a in agendamentos if a.valor_total)
    
    # Serviços mais populares
    servicos_contagem = {}
    for a in agendamentos:
        if a.servico_principal.nome in servicos_contagem:
            servicos_contagem[a.servico_principal.nome] += 1
        else:
            servicos_contagem[a.servico_principal.nome] = 1
    
    # Ordenar serviços por popularidade
    servicos_populares = sorted(servicos_contagem.items(), key=lambda x: x[1], reverse=True)
    
    return render_template(
        'admin_relatorios.html',
        agendamentos=agendamentos,
        total_faturado=total_faturado,
        servicos_populares=servicos_populares
    )

# Inicialização do aplicativo
def criar_admin_padrao():
    """Cria um administrador padrão se não existir"""
    try:
        # Verifica se o email já existe
        admin_existente = Usuario.query.filter(Usuario.email == 'admin@barbearia.com').first()
        
        if not admin_existente:
            print("Criando administrador padrão...")
            admin = Usuario(
                nome='Administrador',
                email='admin@barbearia.com',
                telefone='00000000000',
                is_barbeiro=True
            )
            admin.senha = 'admin123'  # Senha padrão
            
            db.session.add(admin)
            db.session.commit()
            print('Administrador padrão criado com sucesso!')
        else:
            print('Administrador já existe')
    except Exception as e:
        db.session.rollback()
        print(f'Erro ao criar administrador padrão: {str(e)}')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Cria administrador padrão
        criar_admin_padrao()
        # Cria serviços iniciais se não existirem
        if not Servico.query.first():
            servicos_iniciais = [
                Servico(nome='Corte Social/Degradê', descricao='Corte moderno e estiloso com degradê suave', preco=30.00, duracao=30, preco_sem_agendamento=42.00),
                Servico(nome='Corte navalhado', descricao='Corte especial finalizado com navalha para maior precisão', preco=35.00, duracao=35, preco_sem_agendamento=49.00),
                Servico(nome='Barba', descricao='Barba com toalha quente e produtos especiais', preco=20.00, duracao=25, preco_sem_agendamento=28.00),
                Servico(nome='Sobrancelha', descricao='Modelagem de sobrancelha masculina', preco=8.00, duracao=10, preco_sem_agendamento=11.20),
                Servico(nome='Alisamento dos fios', descricao='Progressiva, formou, orgânica ou botox', preco=70.00, duracao=90, preco_sem_agendamento=98.00),
                Servico(nome='Alisamento americano', descricao='Alisamento com técnica americana', preco=40.00, duracao=60, preco_sem_agendamento=56.00),
                Servico(nome='Pigmentação', descricao='Pigmentação de barba ou cabelo', preco=8.00, duracao=15, preco_sem_agendamento=11.20),
                Servico(nome='Pintura capilar', descricao='Coloração de cabelo', preco=15.00, duracao=30, preco_sem_agendamento=21.00),
                Servico(nome='Pezinho', descricao='Acabamento na nuca/pezinho', preco=5.00, duracao=10, preco_sem_agendamento=7.00),
                Servico(nome='Penteado', descricao='Modelagem e penteado', preco=10.00, duracao=15, preco_sem_agendamento=14.00),
                Servico(nome='Luzes', descricao='Mechas e luzes no cabelo', preco=40.00, duracao=60, preco_sem_agendamento=56.00),
                Servico(nome='Descoloração platinado', descricao='Descoloração completa para efeito platinado', preco=80.00, duracao=120, preco_sem_agendamento=112.00),
                Servico(nome='Hidratação', descricao='Hidratação profunda para cabelos', preco=10.00, duracao=20, preco_sem_agendamento=14.00),
                Servico(nome='Corte + Barba', descricao='Combinação de corte de cabelo e barba', preco=45.00, duracao=50, preco_sem_agendamento=63.00),
            ]
            for servico in servicos_iniciais:
                db.session.add(servico)
            
            db.session.commit()
            print("Serviços iniciais criados com sucesso!")
    
    # Iniciando o servidor
    print("Iniciando o servidor Flask...")
    app.run(debug=True, port=5057)