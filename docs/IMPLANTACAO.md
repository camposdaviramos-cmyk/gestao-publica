# Implantação e operação

## Instalação local

1. Instale Python 3.12 ou superior e execute `start.ps1` na pasta do projeto. O script cria um ambiente virtual e instala as dependências fixadas.
2. Abra `http://127.0.0.1:8080`. Configure a primeira conta diretamente no servidor local. Não existe credencial padrão.
3. Para demonstração, marque a opção de dados fictícios. Para validar uma base vazia, deixe desmarcada.
4. Crie pelo menos dois usuários autorizados antes de testar a dupla custódia. Mantenha uma conta administrativa ativa sem restrições individuais para recuperação.
5. Configure instituição, suporte, feriados, dias/horários e grupos.

`data/rio.db`, `data/encryption.key` e `data/backups` são privados e não são servidos pelo servidor web. A aplicação serve somente `static/`. Não exponha a pasta do projeto inteira em outro servidor.

## Configuração por ambiente

| Variável | Padrão | Uso |
|---|---|---|
| `RIO_HOST` | `127.0.0.1` | Interface do processo Waitress. Não publica externamente por padrão. |
| `RIO_PORT` | `8080` | Porta local. |
| `RIO_DATA_DIR` | `data` na pasta do projeto | Diretório privado de banco, chave e backups. |
| `RIO_TRUSTED_HOSTS` | `localhost,127.0.0.1` | Hosts aceitos, separados por vírgula. Configure o domínio institucional no servidor. |
| `RIO_SECURE_COOKIE` | ausente | Use `1` somente com HTTPS corretamente configurado. Ativa cookie Secure e HSTS. |
| `RIO_ENCRYPTION_KEY` | arquivo `data/encryption.key` | Chave Fernet fornecida por cofre institucional, opcional. Preserve a chave usada nos backups. |

O servidor não confia indiscriminadamente em cabeçalhos encaminhados. Ao configurar proxy reverso, alinhe esquema/host com HTTPS e a validação de origem da aplicação, confiando somente no proxy controlado. Não desative CSRF ou CSP para contornar uma configuração incorreta. Neste ambiente, o endereço de auditoria é a origem vista pelo servidor; atrás de proxy, deve ser configurado e validado um mecanismo confiável de encaminhamento.

## Backup diário

Com a conta de serviço e ambiente Python corretos, agende diariamente:

```powershell
Set-Location -LiteralPath 'C:\CAMINHO\Sistema Rio das Ostras'
& '.\.venv\Scripts\python.exe' manage.py backup
```

O comando usa a API de snapshot do SQLite, compatível com banco em uso. O arquivo resultante é criptografado. O agendamento deve ser criado no Agendador de Tarefas do Windows ou no sistema de automação da infraestrutura. **Nenhum agendamento foi instalado automaticamente.**

Guarde a chave de criptografia em cofre separado. Replicar o backup para outra região/local, configurar retenção, alertar sobre falhas e validar recuperação são tarefas da infraestrutura. Não basta guardar cópias no mesmo disco do banco.

Uma pasta temporária contém uma cópia não cifrada durante a geração/validação; use volume protegido e permissões exclusivas para a conta de serviço. A criptografia Fernet desta versão protege os arquivos de backup e scripts, **não** cifra o banco SQLite ativo. Criptografia de volume e proteção de memória/host são necessárias no ambiente produtivo.

## Restauração

1. Interrompa o processo servidor e confirme ausência de gravações.
2. Confirme que a chave corresponde ao backup de origem.
3. Execute:

```powershell
python manage.py restore data\backups\ARQUIVO.db.enc --confirm-service-stopped
python manage.py check
```

O processo preserva uma cópia do banco anterior, verifica integridade e referências, restaura e invalida as sessões recuperadas. A flag é uma confirmação do operador: o comando não detecta todos os serviços externos que possam estar usando o arquivo. Reinicie e confira registros, autenticação e relatórios antes de disponibilizar aos usuários.

## Recuperar acesso

```powershell
python manage.py reset-password servidor@exemplo.gov.br
```

A senha é solicitada sem exibição no terminal. A ação fica registrada e exige nova troca no próximo acesso. Conta inativa ou fora do horário permitido não é reativada automaticamente. Proteja o acesso ao sistema operacional, que permite administrar banco e chaves.

## Requisitos antes de produção

Esta instalação local não demonstra alta disponibilidade municipal. A liberação de produção depende de:

- Completar os itens parciais e não implementados da matriz do Anexo III já recebido; executar homologação por módulo e por cláusula.
- Homologar módulos e migrações por unidade, com dados e reconciliação das bases legadas.
- Prover TLS, domínio e configuração segura de proxy, cofre, permissões de arquivos e conta de serviço dedicada.
- Projetar banco/armazenamento para escala e concorrência municipal; SQLite local não substitui arquitetura distribuída ou redundância geográfica.
- Configurar backups externos, retenção, alertas, recuperação e testes de continuidade.
- Homologar certificado/serviço de assinatura e fornecedores de comunicação, quando aplicáveis.
- Validar acessibilidade, privacidade, segurança, carga real, atendimento e treinamento.
- Definir atualização, rollback e janela operacional. Faça backup antes de alterações de esquema ou dados.

Nenhuma contratação de nuvem, publicação na Internet, envio de mensagens ou migração de dados reais foi realizada.
