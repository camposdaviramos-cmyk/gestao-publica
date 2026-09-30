# Gestão de Frotas — implementação do Anexo III

O módulo cobre integralmente os itens 1 a 27 da seção de Gestão de Frotas do Anexo III do Edital PE 552/2026. A operação utiliza veículos vinculados ao patrimônio municipal, validação de cronologia de hodômetro e horímetro, segregação de acesso por localização/repartição, gestão de tanques próprios com estoque e movimentações, importação de cartões de abastecimento com verificação de duplicidade, ordens de serviço integradas aos almoxarifados e balancetes de custos por quilômetro e hora trabalhada.

## Cadastros e controle de veículos

Os veículos são obrigatoriamente vinculados a bens patrimoniais ativos registrados no módulo de Patrimônio (`assets.items`), garantindo unicidade e impedindo duplicidade de cadastro. O registro contempla:
- Placa oficial (com histórico auditado de trocas de placa anteriores e data de alteração);
- Renavam, chassi, modelo, cor, anos de fabricação e modelo;
- Tipo de veículo com classificação de locomoção (automotora, rebocada, etc.), tipo de rodado e unidade de medida de consumo (km ou horas);
- Medidor inicial (hodômetro ou horímetro), capacidade de tanque e consumo de referência;
- Adaptações e itens agregados (rádios, tacógrafo, antenas, pneus) com controle de agendamento de serviços;
- Bloqueio de movimentações retroativas configurável por veículo, assegurando a integridade dos dados para os Tribunais de Contas (TCE-RJ).

## Motoristas, deslocamentos e reservas

O cadastro de motoristas armazena CPF, CNH, categoria (A, B, C, D, E e combinadas), vencimento e vínculo institucional. 
- **Deslocamentos (`trips`)**: registram saída, retorno, hodômetro inicial e final, roteiro, solicitante e condutor. A cronologia de leituras impede valores retroativos inconsistentes ou saídas com medidor inferior ao retorno anterior. Se a CNH estiver vencida na data de saída, o sistema emite alerta imediato e registra a ocorrência.
- **Reservas de veículos (`reservations`)**: permitem agendamento prévio com verificação algorítmica de sobreposição temporal, impedindo conflito entre reservas e viagens simultâneas.
- **Infrações de trânsito (`infractions`)**: vinculadas ao veículo, condutor e deslocamento correspondente, com controle de valores, prazos e descontos.

## Abastecimento, tanques próprios e cartões

O sistema gerencia abastecimentos em postos próprios e de terceiros:
- **Tanques próprios (`tanks`)**: capacidade para gerenciar centenas de tanques com controle de estoque volumétrico em milionésimos de litro e valor médio. Movimentações de entrada registram nota fiscal e fornecedor; transferências entre tanques validam compatibilidade de combustível.
- **Abastecimentos (`refuels`)**: conferem tipo de combustível compatível com o motor, limite do tanque e leitura cronológica. Abastecimentos em postos próprios realizam saída imediata do estoque do tanque selecionado.
- **Importação de cartões de abastecimento**: endpoint `/api/fleet/import-card` processa arquivos CSV/TXT de redes credenciadas, associando automaticamente o motorista pela matrícula ou CPF, e rejeita transações duplicadas (mesma placa, data/hora e nota).

## Manutenção, serviços e integração com estoque e contabilidade

- **Ordens de serviço (`services`)**: numeradas, controlando custos de serviços preventivos, corretivos e peças. As linhas de serviço (`service_lines`) integram-se diretamente ao módulo de Estoque (`inventory`), requisitando materiais do almoxarifado indicado com baixa automática do saldo físico.
- **Trocas de óleo (`oil_changes`)**: especificam oficina própria ou credenciada com comprovação fiscal.
- **Despesas e tributos (`expenses`)**: vinculam despesas a contas contábeis analíticas do plano de contas (`finance.accounts`), com operação de contabilização.
- **Agenda e alertas (`agendas`)**: prazos de IPVA, seguro obrigatório, licenciamento e manutenções geram notificações automáticas na central do usuário.

## Relatórios gerenciais e controle de acesso

- **Restrição por localização**: usuários não administradores só podem movimentar veículos alocados em repartições expressamente autorizadas na matriz de permissões (`fleet_location_permissions`).
- **Relatórios especializados (`/api/fleet/reports`)**:
  - Consumo discriminando postos próprios e terceiros, com totais físicos e financeiros;
  - Comparativo de consumo por tipo de veículo e combustível;
  - Custos de utilização apurando custo por km rodado e custo por hora trabalhada;
  - Balancete de gastos analítico e consolidado por período;
  - Histórico detalhado do motorista com deslocamentos, ocorrências e serviços;
  - Posição e extrato de movimentação de tanques de combustível;
  - Exportação em PDF e CSV com suporte aos padrões visuais em Light Mode e Dark Mode.

## Evidências

- Regras de negócio e validações: `fleet_core.py`
- Operações transacionais e cálculo de custos: `fleet_operations.py`
- API e relatórios gerenciais: `fleet_api.py`
- Estrutura de banco e índices: `fleet_schema.sql`
- Catálogo e permissões: `fleet_catalog.py`
- Interface do usuário com temas claro/escuro: `static/fleet-ui.js` e `static/fleet.css`
- Suíte de testes automatizados: `tests/test_fleet.py` (5/5 testes aprovados)
