# Rio Gestão — Rio das Ostras

> Atualização de integrações em 23/09/2026: a central administrativa, os conectores PNCP/IBGE e o extrato Siconfi com agenda foram ampliados. Consulte [recursos, testes e pendências da prova de conceito](docs/INTEGRACOES-E-PROVA-DE-CONCEITO.md). Descrições anteriores de ausência total dessas integrações são históricas; isso não significa atendimento integral do edital.

Aplicação web local de gestão administrativa, com banco de dados persistente, tema claro/escuro e interface em português. Desenvolvida a partir do **recorte de 14 páginas (35–48) e do Anexo III de 100 páginas (84–183)** do Edital PE 552/2026, processo 44505/2025 — GOVTIC.

**A aplicação foi ampliada com 11 áreas integradas, mas ainda não atende 100% do Anexo III nem está homologada para produção municipal.** Foram catalogados 1.314 itens numerados do anexo, além das 143 cláusulas do recorte original. A comparação anterior/atual e as pendências estão disponíveis no menu **Anexo III · cobertura** e na [matriz completa](docs/MATRIZ-ANEXO-III.md).

Consulte a [análise da ampliação e seus limites](docs/ANALISE-ANEXO-III.md) e o [manual dos módulos integrados](docs/MANUAL-MODULOS-INTEGRADOS.md). Há pendências internas de implementação, além de integrações, migração, assinatura digital, infraestrutura e homologação.

## Iniciar no Windows

Para publicar o frontend na Vercel e integrar o backend na Render depois, consulte [as instruções de deploy](docs/VERCEL.md).

Requisito: Python 3.12 ou superior. Na pasta do projeto:

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

Ou, com as dependências já instaladas:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Acesse **http://127.0.0.1:8080**. No primeiro acesso, crie a conta administrativa; não existe senha padrão. É possível incluir dados fictícios para conhecer as telas. Essa opção é explícita, aparece na configuração inicial e identifica o ambiente como demonstração. Sem a opção, o banco começa vazio.

O processo deve permanecer executando para manter o sistema disponível. Use `Ctrl+C` para encerrar quando iniciado no terminal. O servidor escuta somente no computador local por padrão.

## Módulos integrados do Anexo III

Abra **Módulos integrados** para acessar execução financeira, controle interno, pessoas, compras/contratos, estoque, patrimônio, frota, assistência social, obras, preparação de pregão e BI. As telas seguem os temas claro/escuro e possuem seleção de entidade e exercício, cadastros tipados, operações, histórico, anexos protegidos e exportação CSV/PDF.

Principais fluxos: dotação → empenho → liquidação → pagamento; partidas dobradas/estorno; recorrência de obrigações; folha RPPS parametrizada com parâmetros aprovados; adjudicação/contrato/aditivo; transferência de estoque em trânsito; depreciação com residual; benefício social com saída automática de insumo; diário → medição → aprovação → pagamento/retenção.

As permissões novas ficam disponíveis automaticamente ao grupo administrativo. Outros usuários precisam de permissão do módulo e vínculo à entidade, configurável em **Entidades e acessos**. Nenhum cadastro antigo é convertido automaticamente em fato financeiro ou folha.

## Recursos da base administrativa

- Dashboard calculado a partir do banco e das permissões do usuário; consultas paginadas.
- Planejamento: programas, ações, metas, indicadores, exercício e valores previstos.
- Cadastros preliminares de documentos contábeis e pessoal, com ligação de documentos a ações orçamentárias. **Não calculam folha, não escrituram contabilidade oficial e não geram obrigações legais.**
- Publicações aprovadas em portal público; rascunhos e dados internos não são expostos.
- Usuários, grupos e permissões individuais; senha forte com hash scrypt, bloqueio, troca obrigatória e horários de acesso.
- Sessões no servidor, cookies HttpOnly/SameSite, proteção CSRF e política CSP.
- Dupla custódia por módulo: inclusão, alteração e exclusão; bloqueio de autoaprovação, controle de versão e justificativa.
- Auditoria persistente, com proteção contra edição/exclusão pela aplicação e por triggers.
- Chamados com prioridades, prazos de resposta/solução, comentários, workaround e notificações internas.
- Ordens de serviço e acompanhamento dos marcos de implantação.
- Relatórios em tela, PDF, XLSX, CSV e DOCX; impressão com recursos do navegador/sistema operacional.
- Ajuda contextual, oito tutoriais, progresso individual e atalhos externos personalizados.
- Backups e rotinas de manutenção criptografados; restauração verificada e encerramento de sessões restauradas.
- Matriz pesquisável das cláusulas do PDF, com situação e evidência de implementação.

As operações de orçamento, contabilidade, pessoal e publicações exigem segunda aprovação por padrão. Para experimentar esse fluxo, crie outra conta autorizada. A conta solicitante não pode aprovar sua própria operação.

## Estrutura

```text
app.py                 Servidor Flask + Waitress e endpoints de apoio
auth.py                Autenticação, sessões, senhas e horários
records.py             Cadastros, controle de versão e dupla custódia
admin.py               Usuários, grupos, parâmetros e manutenção
domain.py              Validações, centavos e calendário de SLA
dashboard.py           Agregações do painel no banco
reports.py             Exportações e prévia
backup.py / manage.py   Backup, restauração e recuperação de conta
schema.sql             Estrutura do banco SQLite, índices e triggers
static/                Interface, temas e acessibilidade básica
docs/                  Análise, matriz, instruções e texto extraído
tests/                 Testes de regras e integração
tools/browser_check.py Fluxos em navegador real e capturas
data/                  Banco, chave e backups (privado; nunca publicar)
```

O frontend usa JavaScript e CSS nativos, sem dependência de CDN ou etapa de build. Os dados administrativos ficam no servidor; o navegador guarda apenas a preferência de tema. SQLite foi escolhido para uma instalação local simples e verificável. Escala municipal com múltiplos nós e alta disponibilidade exige projeto de infraestrutura e evolução do armazenamento.

## Testar

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m playwright install chromium
python tools/browser_check.py
python tools/browser_admin_check.py
python tools/browser_erp_check.py
```

Os testes usam bases temporárias separadas. Os testes de navegador usam as portas 8097, 8098 e 8099 e grava evidências em `artifacts/`. O navegador é executado sem janela.

## Operação

```powershell
python manage.py check
python manage.py backup
python manage.py reset-password nome@exemplo.gov.br
# Interrompa o servidor antes de restaurar:
python manage.py restore data\backups\ARQUIVO.db.enc --confirm-service-stopped
```

Na restauração, o comando preserva uma cópia da base anterior. A chave `data/encryption.key` é indispensável para decifrar os arquivos. Guarde uma cópia em cofre separado; a interface nunca a disponibiliza. Restaurar depende da mesma chave usada na origem.

Leia [o manual de implantação](docs/IMPLANTACAO.md), [o manual de uso](docs/MANUAL.md) e [os limites e resultados de validação](docs/VALIDACAO.md).

## Diretório, assinatura e eSocial

A central administrativa inclui autenticação AD/LDAP, assinatura A1 de relatórios/anexos e envio/consulta de eventos XML eSocial. Configurações e certificados ficam no cofre da instalação. Consulte [o roteiro funcional](docs/LDAP-ASSINATURA-ESOCIAL.md) e [a validação atualizada](docs/VALIDACAO-INTEGRACOES.md).


## Estoque e aquisições

Requisições, cotas, permissões por unidade, comissões, vínculo com licitação, autorização, recebimento parcial de notas, liquidação/contabilização simultâneas, relatórios e tabelas oficiais NCM/NBS estão descritos no [roteiro de estoque e aquisições](docs/ESTOQUE-E-AQUISICOES.md).

O fluxo completo de Patrimônio, incluindo comissões, inventário, depreciação, avaliações, lotes, transferências entre entidades, contabilidade e demonstrativos TCE-RJ, está descrito no [manual patrimonial](docs/PATRIMONIO.md).
