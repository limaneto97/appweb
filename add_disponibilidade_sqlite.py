import sqlite3
import os

# Caminho para o banco de dados
db_path = os.path.join('instance', 'barbearia.db')

print(f"Banco de dados: {db_path}")

# Verifica se o arquivo existe
if not os.path.exists(db_path):
    print(f"Erro: Banco de dados não encontrado em {db_path}")
    exit(1)

try:
    # Conecta ao banco de dados
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verifica se a coluna já existe
    cursor.execute("PRAGMA table_info(usuarios)")
    colunas = cursor.fetchall()
    colunas_nomes = [coluna[1] for coluna in colunas]
    
    if 'is_disponivel' not in colunas_nomes:
        print("Adicionando coluna 'is_disponivel' à tabela 'usuarios'...")
        
        cursor.execute("ALTER TABLE usuarios ADD COLUMN is_disponivel BOOLEAN DEFAULT 1")
        conn.commit()
        
        print("Coluna adicionada com sucesso!")
    else:
        print("A coluna 'is_disponivel' já existe na tabela.")
    
    # Consulta os barbeiros atuais
    cursor.execute("SELECT id, nome FROM usuarios WHERE is_barbeiro = 1")
    barbeiros = cursor.fetchall()
    
    print(f"Encontrados {len(barbeiros)} barbeiros:")
    for barbeiro in barbeiros:
        print(f"  - ID: {barbeiro[0]}, Nome: {barbeiro[1]}")
        
        # Garante que estão marcados como disponíveis
        cursor.execute("UPDATE usuarios SET is_disponivel = 1 WHERE id = ?", (barbeiro[0],))
    
    conn.commit()
    print("Barbeiros marcados como disponíveis.")
    
    # Fecha a conexão
    conn.close()
    print("Processo concluído com sucesso!")
    
except Exception as e:
    print(f"Erro: {e}") 