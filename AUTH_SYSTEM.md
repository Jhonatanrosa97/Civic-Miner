# Sistema de Autenticação - CivicMiner

## Como Funciona

### Armazenamento de Usuários
- Os usuários são armazenados em um array `usuariosRegistrados` no localStorage
- Cada usuário tem:
  - `name`: Nome completo
  - `email`: Email único (não pode duplicar)
  - `password`: Senha
  - `joinDate`: Data de cadastro
  - `phone`: Telefone
  - `company`: Empresa
  - `position`: Cargo
  - `avatar`: Foto de perfil (base64)
  - `cityHistory`: Histórico de cidades (JSON string)

### Login
1. Usuário entra com email e senha
2. Sistema valida se email existe no banco
3. Sistema valida se senha está correta
4. Se correto, todos os dados do usuário são carregados
5. `usuarioAtual` é definido com o email do usuário logado
6. Dados são isolados por usuário

### Registro
1. Usuário preenche formulário de registro
2. Sistema verifica se email já existe
3. Se existe, mostra erro: "Este email já está cadastrado"
4. Se não existe, cria novo usuário com todos os campos
5. Auto-faz login após registro bem-sucedido

### Persistência de Dados
Todos os dados do usuário são salvos em dois lugares:

1. **localStorage (sessão atual)**
   - `userEmail`: Email
   - `userName`: Nome
   - `userPhone`: Telefone
   - `userCompany`: Empresa
   - `userPosition`: Cargo
   - `userPassword`: Senha
   - `userAvatar`: Foto de perfil
   - `cityHistory`: Histórico de cidades
   - `usuarioAtual`: Email do usuário logado (controla qual usuário está usando)

2. **usuariosRegistrados (banco de dados permanente)**
   - Array de objetos usuários
   - Persiste mesmo depois de logout
   - Usado para validar login e manter histórico

### Logout
1. Salva dados da sessão atual no banco de usuários
2. Remove dados da sessão do localStorage
3. Volta para tela de login

### Deletar Conta
1. Remove usuário completamente do `usuariosRegistrados`
2. Limpa todos os dados da sessão
3. Volta para tela de login
4. **Não pode fazer login novamente com essa conta**

### Isolamento de Dados
Cada usuário só vê seus próprios dados porque:
- Ao fazer login, carrega seus dados específicos
- Histórico de cidades é associado ao email do usuário
- Ao deletar conta, remove tudo permanentemente
- `usuarioAtual` controla qual usuário está na sessão

## Funções de Autenticação

### `getUsuariosRegistrados()`
Retorna array de usuários do localStorage

### `salvarUsuariosRegistrados(usuarios)`
Salva array de usuários no localStorage

### `usuarioExiste(email)`
Verifica se email já está registrado

### `validarLogin(email, senha)`
Valida credenciais e retorna objeto do usuário se correto

## Segurança
- Senhas são armazenadas em plaintext (melhorar no futuro com hash)
- Sistema é client-side (para deploy real, usar backend com autenticação JWT)
- Dados são persistidos no navegador
- Cada usuário pode ver apenas seus dados
