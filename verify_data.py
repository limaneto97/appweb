from app import app, db, Usuario, Servico

with app.app_context():
    print("\n=== DADOS ATUALIZADOS ===\n")
    
    # Verificar dados do barbeiro
    barbeiro = Usuario.query.filter_by(email='joao@barbearia.com').first()
    if barbeiro:
        print(f"Barbeiro: {barbeiro.nome}, Email: {barbeiro.email}")
    else:
        print("Barbeiro não encontrado")
    
    # Verificar dados do serviço
    corte = Servico.query.filter_by(nome='Corte de Cabelo').first()
    if corte:
        print(f"Serviço: {corte.nome}, Preço: R${corte.preco:.2f}, Duração: {corte.duracao} minutos")
    else:
        print("Serviço 'Corte de Cabelo' não encontrado")
    
    print("\n=== TODOS OS SERVIÇOS ===\n")
    
    # Listar todos os serviços
    servicos = Servico.query.all()
    for servico in servicos:
        print(f"Serviço: {servico.nome}, Preço: R${servico.preco:.2f}, Duração: {servico.duracao} minutos") 