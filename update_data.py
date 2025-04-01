from app import app, db, Usuario, Servico

with app.app_context():
    # Atualizar o nome do barbeiro
    joao = Usuario.query.filter_by(email='joao@barbearia.com').first()
    if joao:
        joao.nome = 'Ycaro Silva'
        print(f"Nome do barbeiro atualizado para: {joao.nome}")
    else:
        print("Barbeiro com email 'joao@barbearia.com' não encontrado")
    
    # Atualizar o valor do corte de cabelo
    corte = Servico.query.filter_by(nome='Corte de Cabelo').first()
    if corte:
        old_price = corte.preco
        corte.preco = 30.00
        print(f"Preço do corte de cabelo atualizado de R${old_price:.2f} para R${corte.preco:.2f}")
    else:
        print("Serviço 'Corte de Cabelo' não encontrado")
        
    # Salvar as alterações
    try:
        db.session.commit()
        print("Alterações salvas com sucesso!")
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar alterações: {e}") 