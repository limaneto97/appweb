from app import app, db, Usuario

with app.app_context():
    # Verifica se o cliente já existe
    if not Usuario.query.filter_by(email='silva@teste.com').first():
        cliente_silva = Usuario(
            nome='Maria Silva',
            email='silva@teste.com',
            telefone='(11) 98765-4321',
            is_barbeiro=False
        )
        cliente_silva.senha = '123456'
        
        db.session.add(cliente_silva)
        db.session.commit()
        print("Cliente de teste 'Maria Silva' adicionado com sucesso!")
    else:
        print("Cliente de teste 'Maria Silva' já existe.") 