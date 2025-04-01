from app import app, db, Usuario, Servico

def criar_dados_iniciais():
    with app.app_context():
        # Criar usuário de teste
        if not Usuario.query.filter_by(email='cliente@teste.com').first():
            usuario = Usuario(
                nome='Cliente Teste',
                email='cliente@teste.com',
                telefone='(11) 99999-9999',
                is_barbeiro=False
            )
            usuario.senha = '123456'
            db.session.add(usuario)

        # Criar barbeiros
        barbeiros_data = [
            {
                'nome': 'Ycaro Silva',
                'email': 'joao@barbearia.com',
                'senha': '123456',
                'telefone': '(11) 98888-8888',
                'is_barbeiro': True
            },
            {
                'nome': 'Pedro Santos',
                'email': 'pedro@barbearia.com',
                'senha': '123456',
                'telefone': '(11) 97777-7777',
                'is_barbeiro': True
            }
        ]

        for barbeiro_data in barbeiros_data:
            if not Usuario.query.filter_by(email=barbeiro_data['email']).first():
                senha = barbeiro_data.pop('senha')
                barbeiro = Usuario(**barbeiro_data)
                barbeiro.senha = senha
                db.session.add(barbeiro)

        # Criar serviços
        servicos_data = [
            {
                'nome': 'Corte de Cabelo',
                'descricao': 'Corte de cabelo tradicional ou moderno',
                'preco': 35.00,
                'duracao': 30
            },
            {
                'nome': 'Barba',
                'descricao': 'Fazer a barba com toalha quente',
                'preco': 35.00,
                'duracao': 20
            },
            {
                'nome': 'Corte + Barba',
                'descricao': 'Corte de cabelo e barba',
                'preco': 70.00,
                'duracao': 45
            }
        ]

        for servico_data in servicos_data:
            if not Servico.query.filter_by(nome=servico_data['nome']).first():
                servico = Servico(**servico_data)
                db.session.add(servico)

        try:
            db.session.commit()
            print('Dados iniciais criados com sucesso!')
        except Exception as e:
            db.session.rollback()
            print(f'Erro ao criar dados iniciais: {e}')

if __name__ == '__main__':
    criar_dados_iniciais() 