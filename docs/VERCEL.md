# Frontend na Vercel

O frontend será publicado na Vercel e o backend Flask será integrado na Render posteriormente.

## Configuração atual

O arquivo `vercel.json` seleciona o framework **Other** (`framework: null`), desativa instalação e build e publica somente a pasta `static`. A Vercel não precisa importar `app.py` nem instalar as dependências Python.

As regras de rewrite preservam os endereços `/static/...` usados pela interface e a página `/portal`. A raiz `/` serve `static/index.html`. Os arquivos Python, bancos locais e documentos internos ficam fora da pasta publicada.

Envie as alterações ao repositório conectado à Vercel e faça um novo deploy. O **Root Directory** deve ser a raiz do repositório, onde está `vercel.json`. As demais opções de build são definidas por esse arquivo.

## Integração posterior com a Render

As requisições continuam usando `/api/...`. Até conectar o backend, a interface exibe a tela de login com um aviso de serviço indisponível; autenticação, cadastros e consultas não estarão disponíveis. Respostas que não sejam JSON são tratadas sem mostrar erros técnicos ao usuário.

Quando a URL do backend estiver definida, adicione um rewrite de `/api/:path*` para `https://SEU-BACKEND.onrender.com/api/:path*`. Isso mantém as chamadas do navegador no domínio do frontend. Valide o encaminhamento de host e protocolo, os cookies e a verificação de origem/CSRF do Flask antes de liberar o acesso.

O backend atual usa SQLite e arquivos locais. Na Render, configure armazenamento persistente e `RIO_DATA_DIR`, ou migre esses dados para serviços externos. A criação inicial do administrador exige acesso local no backend atual e também precisa ser considerada nessa implantação.

Referência: [configuração da Vercel](https://vercel.com/docs/project-configuration/vercel-json).
