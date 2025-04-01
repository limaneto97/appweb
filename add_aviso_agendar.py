import os
from bs4 import BeautifulSoup

# Caminho para o template de agendamento
template_path = os.path.join('templates', 'agendar.html')

# Texto do aviso
aviso_html = '''
<div class="alert alert-warning mb-4">
    <h5><i class="bi bi-exclamation-triangle-fill"></i> Importante: Compromisso de Agendamento</h5>
    <p>Ao agendar um horário, lembre-se que:</p>
    <ul>
        <li><strong>Pontualidade é essencial:</strong> O barbeiro reservou este horário exclusivamente para você.</li>
        <li><strong>Em caso de ausência:</strong> Outro cliente poderia estar sendo atendido neste horário.</li>
        <li><strong>Economia:</strong> Serviços agendados têm preço especial comparados aos serviços sem agendamento.</li>
        <li><strong>Acréscimo sem agendamento:</strong> Serviços sem agendamento prévio têm acréscimo de 40% no valor.</li>
    </ul>
</div>

<div class="alert alert-success mb-4">
    <h5><i class="bi bi-trophy"></i> Programa de Fidelidade</h5>
    <p>Como cliente da Barbearia, você participa automaticamente do nosso programa de fidelidade:</p>
    <ul>
        <li><strong>A cada 10 agendamentos concluídos:</strong> Você ganha um corte de cabelo gratuitamente!</li>
        <li><strong>Progresso:</strong> Acompanhe seus pontos no seu perfil.</li>
        <li><strong>Exclusivo para agendamentos:</strong> Apenas serviços agendados e concluídos contam pontos.</li>
    </ul>
</div>
'''

try:
    # Lê o conteúdo atual do arquivo
    with open(template_path, 'r') as file:
        content = file.read()
    
    # Parse HTML
    soup = BeautifulSoup(content, 'html.parser')
    
    # Verifica se o aviso já existe
    if "Programa de Fidelidade" not in content:
        # Encontra o local para inserir o aviso (após o título e antes do formulário)
        form_tag = soup.find('form', {'id': 'formAgendamento'})
        
        if form_tag:
            # Cria os elementos do aviso
            aviso_soup = BeautifulSoup(aviso_html, 'html.parser')
            
            # Insere antes do formulário
            form_tag.insert_before(aviso_soup)
            
            # Salva as alterações
            with open(template_path, 'w') as file:
                file.write(str(soup))
            
            print("Aviso de compromisso de agendamento e programa de fidelidade adicionado com sucesso!")
        else:
            print("Não foi possível encontrar o formulário no template.")
    else:
        print("O aviso já existe no template.")
        
except Exception as e:
    print(f"Erro ao modificar o template: {str(e)}") 