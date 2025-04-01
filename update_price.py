import sqlite3
import os

# Caminho para o banco de dados SQLite
db_path = os.path.join('instance', 'barbearia.db')

try:
    # Conecta ao banco de dados SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Obtém o preço atual da hidratação
    cursor.execute("SELECT id, preco, preco_sem_agendamento FROM servicos WHERE nome LIKE '%Hidrata%'")
    resultado = cursor.fetchone()
    
    if resultado:
        servico_id, preco_atual, preco_sem_agendamento_atual = resultado
        
        # Atualiza para o novo preço
        novo_preco = 10.00
        novo_preco_sem_agendamento = novo_preco * 1.4
        
        cursor.execute(
            "UPDATE servicos SET preco = ?, preco_sem_agendamento = ? WHERE id = ?",
            (novo_preco, novo_preco_sem_agendamento, servico_id)
        )
        
        conn.commit()
        
        print(f"Preço da hidratação atualizado com sucesso:")
        print(f"  - Preço anterior: R$ {preco_atual:.2f}")
        print(f"  - Preço atual: R$ {novo_preco:.2f}")
        print(f"  - Preço sem agendamento anterior: R$ {preco_sem_agendamento_atual:.2f}")
        print(f"  - Preço sem agendamento atual: R$ {novo_preco_sem_agendamento:.2f}")
    else:
        print("Serviço de hidratação não encontrado no banco de dados.")
    
except Exception as e:
    print(f"Erro ao acessar o banco de dados: {str(e)}")
    
finally:
    if 'conn' in locals() and conn:
        conn.close() 