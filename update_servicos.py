from app import app, db, Servico

# Valores atualizados dos serviços conforme a página inicial
servicos_atualizados = [
    {"nome": "Corte de Cabelo", "preco": 30.00},
    {"nome": "Barba", "preco": 25.00},
    {"nome": "Hidratação", "preco": 40.00},
    {"nome": "Corte + Barba", "preco": 50.00}
]

with app.app_context():
    # Atualizar os preços de cada serviço
    for servico_info in servicos_atualizados:
        servico = Servico.query.filter_by(nome=servico_info["nome"]).first()
        if servico:
            old_price = servico.preco
            servico.preco = servico_info["preco"]
            print(f"Serviço: {servico.nome}, Preço atualizado de R${old_price:.2f} para R${servico.preco:.2f}")
        else:
            print(f"Serviço '{servico_info['nome']}' não encontrado")
    
    # Salvar as alterações
    try:
        db.session.commit()
        print("Alterações salvas com sucesso!")
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar alterações: {e}")

# Verificar valores atualizados
with app.app_context():
    todos_servicos = Servico.query.all()
    print("\n=== VALORES ATUALIZADOS DOS SERVIÇOS ===")
    for servico in todos_servicos:
        print(f"Serviço: {servico.nome}, Preço: R${servico.preco:.2f}, Duração: {servico.duracao} minutos") 