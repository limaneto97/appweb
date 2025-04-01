from app import app, db, Usuario
from sqlalchemy import Column, Boolean

print("Adicionando coluna de disponibilidade aos barbeiros...")

with app.app_context():
    # Verificar se a coluna já existe
    inspector = db.inspect(db.engine)
    colunas = [coluna['name'] for coluna in inspector.get_columns('usuarios')]
    
    if 'is_disponivel' not in colunas:
        # Adicionar a coluna ao modelo
        print("Coluna 'is_disponivel' não encontrada. Adicionando...")
        try:
            # Adiciona a coluna is_disponivel se não existir
            db.engine.execute('ALTER TABLE usuarios ADD COLUMN is_disponivel BOOLEAN DEFAULT 1')
            print("Coluna adicionada com sucesso!")
        except Exception as e:
            print(f"Erro ao adicionar coluna: {e}")
            print("Tentando método alternativo...")
            try:
                # Método alternativo para SQLite
                with db.engine.connect() as conn:
                    conn.execute('ALTER TABLE usuarios ADD COLUMN is_disponivel BOOLEAN DEFAULT 1')
                print("Coluna adicionada com sucesso via método alternativo!")
            except Exception as e:
                print(f"Erro ao adicionar coluna (método alternativo): {e}")
    else:
        print("Coluna 'is_disponivel' já existe na tabela.")
    
    # Atualizar todos os barbeiros para disponíveis por padrão
    barbeiros = Usuario.query.filter_by(is_barbeiro=True).all()
    
    for barbeiro in barbeiros:
        if not hasattr(barbeiro, 'is_disponivel') or barbeiro.is_disponivel is None:
            barbeiro.is_disponivel = True
    
    try:
        db.session.commit()
        print(f"{len(barbeiros)} barbeiros atualizados com disponibilidade padrão!")
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar barbeiros: {e}")

print("Processo concluído!") 