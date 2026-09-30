import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

fleet_coverage_map = {
    "fleet.1": "Registro de motoristas com endereço, telefone, CPF, CNH, categoria (A-AE), validade e vínculo funcional. Alerta de CNH vencida na saída do veículo. fleet_core.py e fleet.drivers.",
    "fleet.2": "Tipos de veículos classificando locomoção automotora ou rebocada, rodado e medição de consumo por km ou horas. fleet_catalog.py e fleet.vehicle_types.",
    "fleet.3": "Alertas automáticos de compromissos vencidos e a vencer dos veículos diretamente na central de notificações ao acessar o sistema. fleet_api.py e fleet.agendas.",
    "fleet.4": "Cadastro completo do veículo com vínculo obrigatório ao patrimônio (assets.items), Renavam, chassi, fabricação/modelo, adaptações, hodômetro inicial, capacidade e bloqueio temporal. fleet_core.py.",
    "fleet.5": "Abastecimento em postos próprios e credenciados com verificação de combustível compatível e capacidade máxima do tanque. fleet_operations.py e fleet.refuels.",
    "fleet.6": "Abastecimento de veículos e tanques próprios gerenciados pelo almoxarifado/frota com movimentações de estoque. fleet_operations.py e fleet.tank_movements.",
    "fleet.7": "Importação de abastecimento por cartão com validação de duplicidade por placa, data/hora e nota fiscal, e associação automática do condutor. Endpoint /api/fleet/import-card.",
    "fleet.8": "Gestão de cem ou mais tanques de combustível com capacidade, saldo em litros, transferências e histórico volumétrico. fleet_schema.sql e fleet.tanks.",
    "fleet.9": "Registro de despesas dos veículos identificando o evento originador e integrando com contas contábeis do plano de contas. fleet.expenses e operação post_fleet_expense.",
    "fleet.10": "Gerenciamento de itens agregados aos veículos (rádios, antenas, pneus) com identificação e controle individual. fleet.accessories.",
    "fleet.11": "Agendamento de manutenções e serviços preventivos para itens agregados por prazo ou quilometragem. fleet.accessory_schedules.",
    "fleet.12": "Ordens de serviço com número de OS, peças, mão de obra, tipo (preventiva/corretiva) e integração direta com requisições do almoxarifado. fleet.services e fleet.service_lines.",
    "fleet.13": "Controle de trocas de óleo identificando oficina própria ou terceirizada, insumos utilizados e comprovação fiscal. fleet.oil_changes.",
    "fleet.14": "Agenda de compromissos (IPVA, seguro, licenciamento) com notificações automáticas de vencimento. fleet.agendas.",
    "fleet.15": "Registro de deslocamentos com data/hora de saída e retorno, leitor inicial e final, roteiro, solicitante e validação cronológica. fleet.trips e fleet_operations.py.",
    "fleet.16": "Registro de infrações de trânsito vinculadas ao deslocamento, veículo e motorista responsável, com controle de valores e recursos. fleet.infractions.",
    "fleet.17": "Reserva de veículos para diligências com solicitante, motorista, período e validação algorítmica de conflitos com deslocamentos simultâneos. fleet.reservations.",
    "fleet.18": "Histórico completo do motorista por período consolidando deslocamentos, infrações de trânsito e serviços prestados. Relatório drivers em /api/fleet/reports.",
    "fleet.19": "Gráfico e demonstrativo de consumo por período discriminando postos próprios e credenciados para veículos do patrimônio. Relatório consumption em /api/fleet/reports.",
    "fleet.20": "Consumo de combustíveis por período e por localização/unidade, informando litros consumidos e valores. Relatório consumption.",
    "fleet.21": "Gerenciamento de despesas integrado ao cadastro patrimonial sem duplicidade de itens, refletindo alterações do patrimônio. fleet_core.py e fleet.expenses.",
    "fleet.22": "Relatório de custos de utilização apurando custo por quilômetro rodado e custo por hora trabalhada para máquinas e equipamentos. Relatório costs.",
    "fleet.23": "Restrição de movimentação de veículos apenas a usuários com permissão para a respectiva localização ou repartição. Tabela fleet_location_permissions e location_access.",
    "fleet.24": "Balancete analítico de gastos por localização, por veículo e consolidado para determinado período. Relatório balance com exportação PDF/CSV.",
    "fleet.25": "Análises comparativas de consumo por tipo de veículo, equipamento e combustível. Relatório comparison em /api/fleet/reports.",
    "fleet.26": "Histórico completo de alteração de placa dos veículos registrando placa anterior, data e responsável auditado. Operação change_plate.",
    "fleet.27": "Bloqueio temporal de movimentações retroativas a determinado mês por veículo, garantindo integridade para o TCE-RJ. fleet_core.py."
}

updated = 0
for item in d['items']:
    k = item['key']
    if k in fleet_coverage_map:
        item['status'] = 'Implementado'
        item['coverage'] = fleet_coverage_map[k]
        updated += 1

print(f"Updated {updated} fleet items to Implementado.")

# Update counts
counts = {}
for item in d['items']:
    st = item['status']
    counts[st] = counts.get(st, 0) + 1

d['counts'] = counts
if 'status_counts' in d:
    d['status_counts'] = counts

with open('docs/anexo-iii-conformidade.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print("Saved docs/anexo-iii-conformidade.json. New counts:", counts)
