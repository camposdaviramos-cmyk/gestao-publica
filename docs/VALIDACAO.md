# Validação da base original

**Atualização de 23/09/2026:** consulte `VALIDACAO-ANEXO-III.md` para os 59 testes de servidor e 55 verificações de navegador da aplicação ampliada. Os resultados abaixo registram a validação anterior.

Execução em **22/09/2026**, Windows, Python 3.12, Chromium automatizado. Os dados e as contas de teste foram criados em bases temporárias, separadas do diretório `data` da aplicação local.

## Resultado

- **38 testes de servidor aprovados**: `python -m pytest tests -q`.
- **25 checks no navegador aprovados**: `python tools/browser_check.py`.
- **8 checks administrativos adicionais aprovados**: `python tools/browser_admin_check.py`.
- Nenhum erro de JavaScript capturado nas duas execuções de navegador.
- Capturas reais de tela em tema claro, escuro e celular, além de download de PDF validado pelo cabeçalho do arquivo.

## Cobertura relevante

| Área | Evidência |
|---|---|
| Autenticação | Instalação única, hash scrypt, login, bloqueio e auditoria de tentativas, cookies, origem e CSRF. |
| Autorização | Perfil de consulta impedido de gravar e acessar administração; personalização individual; conta administrativa preservada. |
| Horários e senhas | Bloqueio fora do calendário individual, troca obrigatória e invalidação de sessões. |
| Dupla custódia | Base não alterada antes da aprovação, proibição de autoaprovação, decisão por segundo usuário, rejeição, controle de versão e bloqueio de decisão repetida. |
| Concorrência lógica | Edição/exclusão obsoleta e aprovação de versão antiga retornam conflito. Não equivale a teste de carga concorrente. |
| Auditoria | Eventos persistidos; triggers rejeitam alteração e exclusão do histórico. |
| Atendimento | Abertura, comentários, notificações, resolução obrigatória e cálculo de horas úteis com final de semana e feriado. |
| Valores e datas | Centavos exatos, rejeição de valores negativos/não finitos/precisão inválida e filtros de data em Brasília. |
| Relatórios | Arquivos reais PDF, XLSX, CSV e DOCX, neutralização de fórmulas e bloqueio de exportação que exige assinatura indisponível. |
| Backups | Geração cifrada, download, restauração, integridade e remoção de sessões restauradas; recusa de inicialização quando a chave de base existente está ausente. |
| Portal | Somente publicações aprovadas; ausência de identificador interno de usuário na resposta pública; filtro visual. |
| Interface | Telas dos módulos, formulários, grupos, configurações, tutorial, relatórios, aprovações, tema persistido e menu móvel. |
| Robustez | Payloads JSON malformados retornam erro de cliente; manutenção limitada às rotinas registradas; dados persistem após reiniciar a aplicação. |

Foi identificado e corrigido um problema de liberação de arquivo temporário na restauração em Windows. Também foram corrigidos o excesso de largura no celular, os limites de datas em UTC versus Brasília e a limpeza dos dados de interface ao sair/trocar de conta. Os testes relevantes foram executados após as correções.

## Medição de desempenho

Base com **10.000 registros fictícios**, cliente de testes Flask, **30 amostras sequenciais** por endpoint, após uma chamada de aquecimento. Não inclui rede, renderização do navegador, usuários simultâneos ou infraestrutura municipal.

| Consulta | Mediana | P95 observado |
|---|---:|---:|
| Painel (`/api/dashboard`) | 47,13 ms | 49,36 ms |
| Primeira página de planejamento | 28,15 ms | 30,91 ms |
| Busca textual em planejamento | 29,54 ms | 32,05 ms |

O painel usa agregações SQL, as listagens são paginadas e há índices para módulo, situação, data de criação e atualização. Esses resultados são evidência local, não promessa de SLA de produção.

## Artefatos

- `artifacts/backend-tests.xml`: resultado automatizado dos 38 testes.
- `artifacts/browser-results.json`: 25 checks e erros de JavaScript capturados.
- `artifacts/browser-admin-results.json`: 8 checks administrativos.
- `artifacts/performance.json`: amostras resumidas da medição local.
- `artifacts/dashboard-light.png`, `dashboard-dark.png`, `dashboard-mobile.png`, `setup-light.png`: capturas da aplicação.
- `artifacts/report-browser.pdf`: relatório baixado pelo navegador.

## Limites

Não foram realizados teste de intrusão, certificação de acessibilidade, validação jurídica, carga municipal concorrente, prova de alta disponibilidade, migração de bases reais, assinatura com certificado institucional, entrega externa de e-mail/SMS ou homologação pela comissão.

O Anexo III foi posteriormente recebido e catalogado; a ampliação continua sem atendimento integral ou percentual de POC homologado. A aplicação é uma base local funcional para validação e continuidade, conforme os limites descritos na análise e na matriz de requisitos.
