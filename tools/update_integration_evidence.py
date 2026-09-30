import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'tools/build_annex_coverage.py';s=p.read_text(encoding='utf-8')
insertion="""# Ampliação de integrações: evidência específica, sem declarar o anexo integralmente atendido.
mark('control',[25,26,29],'Parcial','Consulta real ao extrato de entregas Siconfi, sincronização por entidade/exercício, vínculo explícito com ocorrência, histórico e notificação de mudança de status. Não há agenda periódica automática, geração/envio de declarações ou regras completas do ranking. integration_siconfi.py; tests/test_siconfi_agenda.py; docs/INTEGRACOES-E-PROVA-DE-CONCEITO.md.')
mark('procurement',[79,81,82,85,86,88],'Parcial','Inclusão PNCP de contratações e contratos com documento PDF selecionado, pacote imutável, dupla revisão, envio explícito, recibo e histórico, com acesso pelo cadastro de origem. Testes locais de protocolo e concorrência; credenciamento/homologação externa pendentes. Não cobre todas as espécies de ato, retificações, atas e PCA. integration_publications.py, pncp_payloads.py; tests/test_integrations.py.')
mark('auction',[1],'Dependência externa','As nove plataformas constam na central administrativa com situação técnica explícita e registro institucional. Não há conector de transmissão/retorno implementado para essas plataformas. Documentação de parceiro, credenciamento, implementação e homologação permanecem necessários. integration_catalog.py; docs/INTEGRACOES-E-PROVA-DE-CONCEITO.md.')
"""
if insertion not in s:s=s.replace('items=[]\nfor r in source',insertion+'items=[]\nfor r in source');p.write_text(s,encoding='utf-8')
for name in ['README.md','docs/ANALISE-ANEXO-III.md','docs/VALIDACAO-ANEXO-III.md']:
 p=ROOT/name;s=p.read_text(encoding='utf-8');link='docs/INTEGRACOES-E-PROVA-DE-CONCEITO.md' if name=='README.md' else 'INTEGRACOES-E-PROVA-DE-CONCEITO.md'
 note='\n> Atualização de integrações em 23/09/2026: a central administrativa, os conectores PNCP/IBGE e o extrato Siconfi com agenda foram ampliados. Consulte [recursos, testes e pendências da prova de conceito]('+link+'). Descrições anteriores de ausência total dessas integrações são históricas; isso não significa atendimento integral do edital.\n'
 if note not in s:
  lines=s.splitlines(keepends=True);lines.insert(1,note);p.write_text(''.join(lines),encoding='utf-8')
directory=ROOT/'docs/integracoes/fontes'
manifest=[{'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(directory.iterdir()) if p.is_file() and p.name!='manifest.json']
(directory/'manifest.json').write_text(json.dumps({'retrieved_on':'2026-09-23','files':manifest},indent=2),encoding='utf-8')
print('Documentação e evidências atualizadas.')
