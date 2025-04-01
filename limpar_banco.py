from app import app, db, Usuario, Servico, Agendamento, barbeiro_servico, agendamento_servico
import sys

# Rodar com o contexto da aplicação
with app.app_context():
    try:
        # Verifica se o administrador existe
        admin = Usuario.query.filter_by(email='barbeariasouzaretro@gmail.com').first()
        
        if admin:
            print(f"Administrador encontrado: {admin.email}")
            
            # Salvar os dados do administrador para restaurar depois
            admin_id = admin.id
            admin_nome = admin.nome
            admin_email = admin.email
            admin_senha_hash = admin.senha_hash
            admin_telefone = admin.telefone
            admin_is_barbeiro = admin.is_barbeiro
            admin_pontos = admin.pontos_fidelidade
            
            # Limpar todas as tabelas
            print("Removendo todos os dados do banco...")
            db.session.execute(db.delete(agendamento_servico))
            db.session.execute(db.delete(barbeiro_servico))
            db.session.execute(db.delete(Agendamento))
            db.session.execute(db.delete(Usuario))
            db.session.execute(db.delete(Servico))
            db.session.commit()
            
            # Recriar o administrador
            print("Recriando o administrador...")
            admin = Usuario(
                id=admin_id,
                nome=admin_nome,
                email=admin_email,
                senha_hash=admin_senha_hash,
                telefone=admin_telefone,
                is_barbeiro=admin_is_barbeiro,
                pontos_fidelidade=admin_pontos
            )
            db.session.add(admin)
            db.session.commit()
            
            print(f"Administrador restaurado: {admin.email}")
            print("Banco de dados limpo com sucesso.")
        else:
            print("Administrador não encontrado. Operação cancelada.")
            sys.exit(1)
    except Exception as e:
        print(f"Erro: {e}")
        db.session.rollback()
        sys.exit(1)
