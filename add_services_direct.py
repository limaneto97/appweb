import sqlite3
import os

# Caminho para o banco de dados SQLite
db_path = os.path.join('instance', 'barbearia.db')

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

# Adiciona os serviços ao banco de dados
try:
    # Conecta ao banco de dados SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verifica se a tabela de serviços já tem a coluna preco_sem_agendamento
    cursor.execute("PRAGMA table_info(servicos)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    # Adiciona a coluna se não existir
    if 'preco_sem_agendamento' not in column_names:
        print("Adicionando coluna preco_sem_agendamento à tabela servicos...")
        cursor.execute("ALTER TABLE servicos ADD COLUMN preco_sem_agendamento FLOAT")
        
    # Atualiza os serviços existentes com o preço sem agendamento
    cursor.execute("UPDATE servicos SET preco_sem_agendamento = preco * 1.4 WHERE preco_sem_agendamento IS NULL")
    
    # Verifica se a coluna pontos_fidelidade existe na tabela usuarios
    cursor.execute("PRAGMA table_info(usuarios)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    # Adiciona a coluna se não existir
    if 'pontos_fidelidade' not in column_names:
        print("Adicionando coluna pontos_fidelidade à tabela usuarios...")
        cursor.execute("ALTER TABLE usuarios ADD COLUMN pontos_fidelidade INTEGER DEFAULT 0")
        
    # Verifica se as colunas finalizado e finalizado_em existem na tabela agendamentos
    cursor.execute("PRAGMA table_info(agendamentos)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    # Adiciona as colunas se não existirem
    if 'finalizado' not in column_names:
        print("Adicionando coluna finalizado à tabela agendamentos...")
        cursor.execute("ALTER TABLE agendamentos ADD COLUMN finalizado BOOLEAN DEFAULT 0")
        
    if 'finalizado_em' not in column_names:
        print("Adicionando coluna finalizado_em à tabela agendamentos...")
        cursor.execute("ALTER TABLE agendamentos ADD COLUMN finalizado_em DATETIME")
    
    if 'duracao_total' not in column_names:
        print("Adicionando coluna duracao_total à tabela agendamentos...")
        cursor.execute("ALTER TABLE agendamentos ADD COLUMN duracao_total INTEGER DEFAULT 0")
    
    if 'valor_total' not in column_names:
        print("Adicionando coluna valor_total à tabela agendamentos...")
        cursor.execute("ALTER TABLE agendamentos ADD COLUMN valor_total FLOAT DEFAULT 0")
    
    if 'valor_sem_agendamento' not in column_names:
        print("Adicionando coluna valor_sem_agendamento à tabela agendamentos...")
        cursor.execute("ALTER TABLE agendamentos ADD COLUMN valor_sem_agendamento FLOAT DEFAULT 0")
    
    # Cria tabela de associação agendamento_servico se não existir
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agendamento_servico (
        agendamento_id INTEGER,
        servico_id INTEGER,
        PRIMARY KEY (agendamento_id, servico_id),
        FOREIGN KEY (agendamento_id) REFERENCES agendamentos (id),
        FOREIGN KEY (servico_id) REFERENCES servicos (id)
    )
    """)
    
    # Adiciona os serviços se não existirem
    count = 0
    for nome, desc, preco, duracao in services:
        # Verifica se o serviço já existe
        cursor.execute("SELECT id FROM servicos WHERE nome = ?", (nome,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO servicos (nome, descricao, preco, preco_sem_agendamento, duracao) VALUES (?, ?, ?, ?, ?)",
                (nome, desc, preco, preco * 1.4, duracao)
            )
            count += 1
    
    # Commit das alterações
    conn.commit()
    
    print(f"Banco de dados atualizado com sucesso! {count} novos serviços adicionados.")
    
except Exception as e:
    print(f"Erro ao acessar o banco de dados: {str(e)}")
    
finally:
    if conn:
        conn.close() 