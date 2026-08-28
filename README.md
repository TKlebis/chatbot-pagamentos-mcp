# 🛒 ChatPay - Chatbot de Pagamentos com MCP (Model Context Protocol)
<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-005571?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB" alt="React">
  <img src="https://img.shields.io/badge/SQLite-07405E?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/Ollama-000000?style=flat-square&logo=ollama&logoColor=white" alt="Ollama">
</p>

ChatPay é um assistente virtual inteligente integrado a um sistema de pagamentos seguro utilizando a arquitetura **MCP (Model Context Protocol)**. O projeto conecta um agente de linguagem natural a ferramentas backend controladas para gerenciar catálogo de produtos, intenções de compra temporárias e efetivação de transações com controle de limite de crédito.

---

## 🚀 Tecnologias Utilizadas

* **Backend:** Python, FastAPI, Uvicorn, SQLite
* **Segurança e Autenticação:** JWT (JSON Web Tokens), Argon2 (`pwdlib`)
* **IA & MCP:** Ollama, Python MCP SDK (`mcp`)
* **Frontend:** React, Vite, CSS Moderno

---

## 🛠️ Arquitetura e Ferramentas (MCP Tools)

O servidor MCP (`mcp_server/server.py`) expõe **3 ferramentas principais** que o LLM aciona de forma autônoma e segura:

1. **`listar_catalogo`**: Consulta os produtos ativos e com estoque disponível no banco de dados.
2. **`registrar_intencao`**: Cria um carrinho temporário (expira em 10 minutos) validando estoque, quantidade e regras de negócio sem movimentar saldo financeiro.
3. **`realizar_compra`**: Valida a intenção gerada na sessão, checa o limite de saldo disponível do usuário, processa o pagamento (Pix ou Cartão) de forma atômica e atualiza o estoque.

---

## 📂 Estrutura do Projeto

```text
chatbot-pagamentos-mcp/
├── backend/
│   └── main.py          # API FastAPI principal (Endpoints de chat, login, JWT e ponte com MCP)
├── data/
│   └── .gitkeep         # Mantém a pasta no versionamento (o app.db é gerado pelo seed)
├── frontend/            # Interface visual em React/Vite
│   ├── src/
│   ├── package.json
│   └── ...
├── mcp_server/
│   └── server.py        # Servidor MCP com as regras de negócio e tools
├── seed.py              # Script de inicialização e carga de dados (Seed)
└── README.md
```

# ⚙️ Como Executar o Projeto Localmente
## 1. Pré-requisitos
* Python 3.10+ instalado

* Node.js e npm instalados

* Servidor Ollama rodando localmente

## 2. Configurar o Backend e o Banco de Dados
No terminal, navegue até a raiz do projeto e configure o ambiente virtual:

```python
# Criar e ativar ambiente virtual (Windows)
python -m venv .venv
.venv\Scripts\activate

# Instalar dependências da API e do MCP
pip install fastapi uvicorn pydantic pyjwt pwdlib argon2-cffi ollama mcp

# Executar o seed para criar e popular o banco de dados do zero
python seed.py
```

## 3. Iniciar o Servidor Backend (FastAPI)

```python
uvicorn backend.main:app --reload
```
## 4. Iniciar o Frontend (React)
Abra um novo terminal na pasta do frontend:

```python
cd frontend
npm install
npm run dev
```

# 👥 Usuários de Teste

Para testar os cenários de limite excedido e sucesso, utilize as credenciais padrão geradas pelo seed:

* Usuário Normal (Limite Alto - R$ 2.000,00):

* Username: user_normal

* Senha: 123456

* Usuário com Limite Baixo (R$ 100,00):

* Username: user_baixo

* Senha: 123456

# 📸 Evidências dos Testes (Prints)

## Cenário de Sucesso (Compra Aprovada)
<img width="597" height="697" alt="O Print de Sucesso da Compra" src="https://github.com/user-attachments/assets/2584b635-2dd8-4f1b-8b07-2c49d4f93069" />

## Cenário de Regra (Limite Excedido)
<img width="597" height="692" alt="O Print de Limite Excedido" src="https://github.com/user-attachments/assets/a6072d49-a1f7-42fc-87b4-fbf69eee4fae" />

## Cenário de Amostra (Catalogo entregue)
<img width="598" height="696" alt="O Print do CatálogoInterface" src="https://github.com/user-attachments/assets/e180d3ea-dbdc-4f2c-a41b-73284a320579" />

## Sistema de Chat 
https://github.com/user-attachments/assets/6ae4dccd-7843-4b20-8695-16d0b76b920c


# 🛡️ Principais Validações de Segurança Implementadas
* Prevenção de Deadlock: Uso de timeout configurado no SQLite e commits atômicos para evitar travamentos de concorrência.

* Isolamento de Sessão: Validação estrita de user_id e chat_id em todas as ferramentas MCP.

* Prevenção de Fraudes: O preço real do produto nunca é enviado pelo modelo de IA; ele é buscado diretamente no banco de dados com base no produto_id.

## 🚀 Squad 9

*Autor:* [Thiago Klebis](https://www.linkedin.com/in/thiagoklebis/)
