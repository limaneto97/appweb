from app import app, db, Servico

with app.app_context():
    # Verificar se o serviço já existe
    hidratacao = Servico.query.filter_by(nome="Hidratação").first()
    
    if not hidratacao:
        # Adicionar o serviço de Hidratação
        novo_servico = Servico(
            nome="Hidratação",
            descricao="Tratamento completo para cabelos ressecados ou danificados.",
            preco=40.00,
            duracao=45  # 45 minutos para uma hidratação
        )
        
        db.session.add(novo_servico)
        
        try:
            db.session.commit()
            print("Serviço de Hidratação adicionado com sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao adicionar serviço: {e}")
    else:
        print("O serviço de Hidratação já existe no banco de dados.")

# Verificar todos os serviços
with app.app_context():
    todos_servicos = Servico.query.all()
    print("\n=== SERVIÇOS DISPONÍVEIS ===")
    for servico in todos_servicos:
        print(f"Serviço: {servico.nome}, Preço: R${servico.preco:.2f}, Duração: {servico.duracao} minutos") 