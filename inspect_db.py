from app import app, db, Usuario

with app.app_context():
    print("Usuários cadastrados:")
    usuarios = Usuario.query.all()
    for u in usuarios:
        print(f"ID: {u.id}, Nome: {u.nome}, Email: {u.email}, Telefone: {u.telefone}, Barbeiro: {u.is_barbeiro}") 