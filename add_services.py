from app import app, db, Servico

# Lista de serviços: (nome, descrição, preço, duração em minutos)
services = [
    ('Corte Social/Degradê', 'Corte moderno e estiloso com degradê suave', 30.00, 30),
    ('Corte navalhado', 'Corte finalizado com navalha para maior precisão', 35.00, 30),
    ('Barba', 'Aparo e modelagem completa da barba', 20.00, 25),
    ('Sobrancelha', 'Design e acabamento de sobrancelha', 8.00, 15),
    ('Alisamentos dos fios', 'Progressiva, formou, orgânica ou botox para alisamento', 70.00, 90),
    ('Alisamento americano', 'Técnica americana de alisamento capilar', 40.00, 60),
    ('Pigmentação', 'Pigmentação para barba ou couro cabeludo', 8.00, 20),
    ('Pintura capilar', 'Coloração dos fios', 15.00, 40),
    ('Pezinho', 'Acabamento da nuca', 5.00, 10),
    ('Penteado', 'Modelagem e penteado', 10.00, 15),
    ('Luzes', 'Mechas e luzes no cabelo', 40.00, 60),
    ('Descoloração platinado', 'Processo de descoloração completa', 80.00, 120),
    ('Hidratação', 'Hidratação profunda dos fios', 10.00, 30),
    ('Corte + Barba', 'Combinação de corte de cabelo e barba', 45.00, 50)
]

with app.app_context():
    print('Tentando adicionar serviços...')
    
    existing_services = {s.nome: s for s in Servico.query.all()}
    count = 0
    
    for nome, desc, preco, duracao in services:
        if nome not in existing_services:
            s = Servico(
                nome=nome, 
                descricao=desc, 
                preco=preco, 
                preco_sem_agendamento=preco*1.4, 
                duracao=duracao
            )
            db.session.add(s)
            count += 1
    
    db.session.commit()
    print(f'Foram adicionados {count} novos serviços') 