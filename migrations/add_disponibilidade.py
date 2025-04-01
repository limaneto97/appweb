from flask_migrate import Migrate
from app import app, db, Usuario
import os

migrate = Migrate(app, db)

# Criar diretório migrations se não existir
if not os.path.exists('migrations'):
    os.makedirs('migrations')
    os.makedirs('migrations/versions')

# Iniciar migração
with app.app_context():
    # Verificar se a migração já foi aplicada
    try:
        usuarios = Usuario.query.first()
        has_attribute = hasattr(usuarios, 'is_disponivel')
    except Exception:
        has_attribute = False

    if not has_attribute:
        print("Executando a migração para adicionar a coluna is_disponivel...")
        try:
            # Criar arquivo de migração
            migration_script = """
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001_add_disponibilidade'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('usuarios', sa.Column('is_disponivel', sa.Boolean(), nullable=True, server_default='1'))
    
def downgrade():
    op.drop_column('usuarios', 'is_disponivel')
"""
            with open('migrations/versions/001_add_disponibilidade.py', 'w') as f:
                f.write(migration_script)
            
            # Executar a migração
            os.system('flask db upgrade')
            
            print("Migração concluída com sucesso!")
        except Exception as e:
            print(f"Erro na migração: {e}")
    else:
        print("A coluna is_disponivel já existe. Pulando migração.")
        
    # Definir valores padrão para todos os barbeiros
    barbeiros = Usuario.query.filter_by(is_barbeiro=True).all()
    updated = 0
    
    for barbeiro in barbeiros:
        try:
            if barbeiro.is_disponivel is None:
                barbeiro.is_disponivel = True
                updated += 1
        except:
            # Adiciona o atributo se não existir
            setattr(barbeiro, 'is_disponivel', True)
            updated += 1
    
    if updated > 0:
        try:
            db.session.commit()
            print(f"Atualizados {updated} barbeiros com disponibilidade padrão")
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao atualizar barbeiros: {e}")
    else:
        print("Não foi necessário atualizar os barbeiros.")

print("Processo concluído!") 