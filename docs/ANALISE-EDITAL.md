# Análise do recorte original do edital

**Atualização:** o Anexo III foi posteriormente recebido e catalogado. Consulte `ANALISE-ANEXO-III.md` e `MATRIZ-ANEXO-III.md`. O texto abaixo preserva a análise do recorte inicial de páginas 35–48.

## Documento e alcance

Foi lido e extraído o único PDF presente na pasta: **Edital PE 552 2026 Sistema Rio das Ostras-35-48 (2).pdf**, 14 páginas, correspondentes às páginas numeradas **35 a 48**. Processo administrativo **44505/2025 — GOVTIC**. A extração integral está em `edital-extraido.txt`; a matriz preserva 143 ocorrências de cláusulas numeradas, inclusive a numeração 4.1 repetida no próprio documento.

O recorte trata da seção 4, requisitos da contratação. Não contém o catálogo completo das funcionalidades de cada módulo, as características detalhadas do provedor em nuvem ou o **Anexo III — Prova de Conceito** ao qual remete repetidamente. Não há base para afirmar que qualquer implementação produzida somente a partir deste recorte satisfaz integralmente a licitação.

## O que o recorte exige

| Tema | Itens | Consequência para o trabalho |
|---|---|---|
| Capacitação | 4.1–4.8 | Implantação acompanhada de treinamento, inclusive backup; até 40 horas, até 8 horas por dia, 30 usuários, presencial na contratante; EAD com vídeos e tutoriais, acesso gratuito e ilimitado. |
| Referências legais | 4.9 | Referências normativas precisam ser consideradas pelos responsáveis jurídicos e técnicos; código isolado não comprova conformidade. |
| Manutenção e suporte | 4.10–4.18 | Manutenção corretiva, adaptativa e evolutiva, garantias, prioridades de atendimento, workaround e atendimento regular/extraordinário. |
| Prazos e migração | 4.19–4.22 | Implantação em até 90 dias, excepcional extensão de 30; módulos prioritários em 30 dias; conversão de bases e transição sem interrupção das atividades. |
| Segurança e privacidade | 4.23–4.32 | Sigilo, acesso restrito, proteção em armazenamento e trânsito, descarte, devolução e responsabilidades operacionais. |
| Inclusão e sustentabilidade | 4.33–4.35 | Acessibilidade, uso eficiente de recursos, português brasileiro e parametrização institucional. |
| Arquitetura do software | 4.36–4.52 | Senhas, ajuda contextual, Internet, bloqueio e horários, grupos, dupla custódia, permissões, auditoria, validação, atualização, atalhos, scripts criptografados, relatórios, assinatura e chamados. |
| Nuvem | 4.53 | Infraestrutura, continuidade, redundância geográfica, disponibilidade e desempenho; comprovação externa ao frontend/backend local. |
| Execução contratual | 4.54–4.66 | Atualização, implantação integral, equipe, assessoria, ordens de serviço, sustentabilidade e limites/autorizações de subcontratação. |
| Prova de conceito | 4.67–4.81 | Demonstração efetiva, condições isonômicas, fases, registros, percentuais, prazos, complementação, julgamento e aceite. |
| Garantia da contratação | 4.82–4.86 | Garantia correspondente a 5% do contrato e requisitos de apresentação, vigência e substituição de apólice. |

### Prazos de atendimento reproduzidos

| Prioridade | Resposta | Solução |
|---|---|---|
| Crítico | 2 horas | 6 horas |
| Alto | 4 horas | 8 horas úteis |
| Médio | 8 horas úteis | 24 horas úteis |
| Baixo | 24 horas úteis | 48 horas úteis |

Onde a tabela não especifica horas úteis, a implementação considera horas corridas. O calendário útil é segunda a sexta, 08h às 17h, em Brasília, com exclusão dos feriados configurados. Feriados não são presumidos: a administração deve cadastrar seu calendário. Prazos são fixados na abertura para preservar a referência original; mudança posterior do calendário não recalcula os chamados existentes.

Prorrogações excepcionais aceitas pela fiscalização e escala de atendimento extraordinário **não** têm fluxo automatizado específico nesta versão. A equipe e o cumprimento efetivo dos prazos são responsabilidades operacionais.

### Implantação, treinamento e prova de conceito

- Orçamento, contabilidade, folha e transparência são os módulos citados como prioritários para os primeiros 30 dias. Os demais módulos e suas regras não são enumerados neste recorte.
- A implantação depende de ordem de serviço e das bases fornecidas pela prefeitura; a conversão precisa preservar integridade e continuidade dos setores.
- O treinamento deve contemplar alinhamento de programas e ações à estratégia/recursos, avaliação de produtos e efeitos e uso gerencial para corrigir desvios. Os tutoriais incluídos abordam essas operações na base implementada; não substituem treinamento presencial ou vídeos.
- O documento prevê prazos de cinco dias úteis relacionados à apresentação/avaliação e oportunidade de complementação em dois dias úteis, limitada aos itens apontados pela comissão. A matriz mantém os textos exatos para consulta.
- A fase 1 avalia características gerais do sistema e do provedor; a fase 2 avalia individualmente os módulos. Os limites são 90% para características gerais do sistema e para cada módulo, e 100% para nuvem. Itens compostos precisam cumprir todos os subitens. A implantação definitiva exige 100% dos requisitos.
- Demonstração deve executar efetivamente cadastros, alterações, exclusões, consultas, relatórios, integrações e rotinas aplicáveis, incluindo comunicação por e-mail/SMS quando exigida. Sessões, gravações, atas, convocação e julgamento são externos à aplicação.
- A subcontratação acessória indicada no recorte está limitada a 25%, com autorização expressa e responsabilidade mantida pela contratada. Nenhum serviço foi contratado ou subcontratado por esta implementação.

## Implementação entregue

A aplicação oferece um núcleo administrativo real, com dados em SQLite, autenticação, segurança de sessão, gestão de permissões, horários, aprovação por duas pessoas, registro de operações, chamados, relatórios, backups, tutoriais e uma interface completa para os cadastros disponíveis. A interface usa temas claro e escuro, layout responsivo e arquivos locais, sem bibliotecas remotas necessárias para operar.

Os cadastros de planejamento, contabilidade e pessoal são **estruturas preliminares para validação**. Não implementam todo o ciclo PPA/LDO/LOA, empenho/liquidação/pagamento, plano de contas oficial, demonstrações legais, cálculo de folha, tributos ou remessas legais. O portal publica apenas conteúdos cadastrados e aprovados no módulo de publicações; não é apresentado como portal de transparência municipal completo.

Valores são armazenados em centavos. As alterações usam controle de versão. Uma solicitação de aprovação obsoleta não pode sobrescrever uma alteração posterior. As permissões são conferidas pelo backend, não apenas pelo menu. Os dados de demonstração são opcionais e inteiramente fictícios.

## O que permanece necessário

1. **Edital completo e Anexo III:** regras de cada módulo, integrações, relatórios oficiais, critérios de POC e requisitos detalhados de nuvem. Só então será possível fechar o desenho funcional e estabelecer um percentual válido de atendimento.
2. **Dados e responsáveis institucionais:** layout das bases legadas, ambiente de homologação, perfis, unidades, calendário, regras de migração e critérios de aceite.
3. **Infraestrutura:** provedor, TLS, criptografia de disco, gestão de segredos, backups externos, restauração, redundância, monitoramento, capacidade e continuidade. A aplicação está configurada para acesso local.
4. **Assinatura digital:** certificado e serviço de assinatura. Existe parametrização de exigência, mas documentos não são assinados criptograficamente; a exportação exigida é bloqueada para impedir falsa assinatura.
5. **Comunicações externas:** provedores e integração efetiva de e-mail/SMS. Esta versão oferece notificações internas; não envia comunicações externas.
6. **Capacitação e operação:** vídeos, instrutores, agenda, presença, atendimento presencial/remoto e obrigações contratuais.
7. **Segurança e homologação:** avaliação formal de acessibilidade, privacidade, teste de intrusão, carga concorrente e validação pelos departamentos. O resultado dos testes locais não equivale à certificação para dados públicos reais.
8. **Granularidade complementar:** dupla custódia por usuário/grupo/operação e para cadastros administrativos, relatórios assinados e demais exigências parciais indicadas na matriz.

Cada cláusula do recorte foi mantida na [matriz de rastreabilidade](MATRIZ-REQUISITOS.md), com a classificação **Implementado**, **Parcial**, **Operacional** ou **Dependência externa**. Classificação local não corresponde à avaliação da comissão.
