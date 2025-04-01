# Sistema de Agendamento para Barbearia

Um sistema web para gerenciamento de agendamentos de barbearia, desenvolvido com Flask e Python.

## Funcionalidades

### Funcionalidades Originais
- Cadastro e login de usuários
- Agendamento de horários
- Visualização de agendamentos
- Gerenciamento de serviços
- Gerenciamento de barbeiros
- Interface responsiva e moderna

### Novas Funcionalidades
- **Verificação de horários disponíveis**: Sistema verifica automaticamente a disponibilidade de horários antes de permitir agendamentos
- **Seleção visual de horários**: Interface intuitiva mostrando apenas horários livres para agendamento
- **Otimização de banco de dados**: Índices para busca rápida de agendamentos e usuários
- **Busca avançada de clientes**: Barbeiros podem buscar clientes por nome, telefone ou email
- **Agendamentos para clientes**: Barbeiros podem criar agendamentos para seus clientes
- **Integração com WhatsApp**: Envio de lembretes automáticos para clientes via WhatsApp
- **Prevenção de conflitos de horários**: Sistema evita agendamentos duplicados no mesmo horário
- **Detecção inteligente de disponibilidade**: Considera a duração dos serviços ao verificar disponibilidade

### Melhorias Recentes (Março 2023)
- **Atualização de Preços**: Ajuste do valor do corte de cabelo para R$30,00
- **Exibição de Preços**: Adicionados preços dos serviços na página inicial para fácil visualização pelos clientes
- **Informações de Pagamento**: Adicionado card informativo sobre métodos de pagamento aceitos no dashboard do cliente
- **Layout Aprimorado**: Redesign da interface com animações suaves, cores harmoniosas e elementos visuais mais atrativos
- **Rodapé Informativo**: Adicionado rodapé com informações de contato, horário de funcionamento e redes sociais
- **Experiência Mobile**: Melhorias na navegação e visualização em dispositivos móveis
- **Alertas Interativos**: Adicionados botões de fechamento para alertas do sistema

## Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## Instalação

1. Clone o repositório:
```bash
git clone [URL_DO_REPOSITORIO]
cd barbearia_app
```

2. Crie um ambiente virtual (recomendado):
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Configuração

1. Configure as variáveis de ambiente (opcional):
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

2. Inicialize o banco de dados:
```bash
python init_db.py
python criar_dados.py
```

## Executando o Sistema

1. Inicie o servidor:
```bash
python app.py
```

2. Acesse o sistema no navegador:
```
http://localhost:5001
```

3. Use as seguintes credenciais para teste:
   - **Cliente**: Email: cliente@teste.com, Senha: 123456
   - **Barbeiro**: Email: joao@barbearia.com, Senha: 123456

## APIs Disponíveis

O sistema conta com as seguintes APIs internas:

- `/api/horarios_disponiveis`: Retorna horários disponíveis para um barbeiro em uma data
- `/api/buscar_clientes`: Busca clientes por nome, email ou telefone
- `/api/enviar_lembrete_whatsapp/<id>`: Prepara mensagem WhatsApp para envio

## Estrutura do Projeto

```
barbearia_app/
├── app.py                 # Aplicação principal
├── init_db.py             # Inicialização do banco de dados
├── criar_dados.py         # Criação de dados iniciais
├── update_data.py         # Script para atualização de dados
├── verify_data.py         # Script para verificação de dados
├── add_test_client.py     # Adição de cliente de teste
├── requirements.txt       # Dependências do projeto
├── static/                # Arquivos estáticos (CSS, JS, imagens)
├── templates/             # Templates HTML
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── registro.html
│   ├── dashboard_cliente.html
│   ├── dashboard_barbeiro.html
│   ├── agendar.html
│   ├── 404.html
│   └── 500.html
└── README.md
```

## Otimizações de Banco de Dados

- Índices em campos de consulta frequente: `email`, `telefone`, `is_barbeiro`, `data_hora`, `status`
- Índices compostos para busca eficiente:
  - `idx_agendamento_barbeiro_data`: Otimiza busca de agendamentos por barbeiro e data
  - `idx_agendamento_cliente_status`: Otimiza busca de agendamentos por cliente e status

## Design e UI/UX

- **Paleta de Cores**: Esquema de cores profissional com tons de azul escuro e detalhes em vermelho
- **Tipografia**: Fonte legível e moderna (Segoe UI) para melhor experiência de leitura
- **Componentes Interativos**: Cards com efeito de hover, botões com feedback visual
- **Iconografia**: Utilização de ícones Bootstrap para melhorar a compreensão visual
- **Layout Responsivo**: Adaptação para todos os tamanhos de tela, de smartphones a desktops

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes. 