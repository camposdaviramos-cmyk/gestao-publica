"""Extrai os itens numerados sem resumir ou descartar subitens."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SECTIONS={
 'CARACTERÍSTICAS GERAIS DOS SISTEMA':'general',
 'CARACTERÍSTICAS GERAIS DO PROVEDOR EM NUVEM (CLOUD COMPUTING)':'cloud',
 'ADMINISTRAÇÃO ORÇAMENTÁRIA E FINANCEIRA, CONTABILIDADE,':'finance',
 'Controle Interno – Controladoria':'control',
 'Gestão de Recursos Humanos - Pessoal':'people',
 'COMPRAS E CONTRATOS':'procurement','PREGÃO ELETRÔNICO':'auction',
 'GESTÃO DE ESTOQUE':'inventory','PATRIMÔNIO':'assets',
 'PAINEL DO GESTOR E INFORMAÇÕES GERENCIAS - BI':'bi',
 'PORTAL DA TRANSPARÊNCIA':'transparency','GESTÃO DE FROTAS':'fleet',
 'GESTÃO DE ASSISTÊNCIA SOCIAL':'social','OBRAS PÚBLICAS':'works'}
pages=json.loads((ROOT/'docs/anexo-iii-paginas.json').read_text(encoding='utf-8'))
items=[];current=None;section=None
for page,text in enumerate(pages,1):
 lines=text.splitlines();lines=[l.strip() for l in lines]
 # Cabeçalho do edital e número de página, antes do conteúdo.
 for i,line in enumerate(lines):
  if line.startswith('PROCESSO ADMINISTRATIVO'):
   lines=lines[i+2:];break
 for line in lines:
  line=re.sub(r'\s+',' ',line).strip()
  if line in SECTIONS:section=SECTIONS[line];current=None;continue
  if not line or not section:continue
  if line.startswith(('Item Descritivo','ATENDIMENTO OBRIGATÓRIO','atende','SISTEMAS INTEGRADOS','DESCRIÇÃO DE CADA','OBRIGATÓRIO -','PLANEJAMENTO E TESOURARIA')):continue
  m=re.match(r'^(\d{1,3})\.?\s*(.*)$',line)
  if m and int(m[1]) == (1 if current is None else (300 if section=='social' and current['item']==290 else current['item']+1)) and (not m[2] or re.match(r'^[A-Za-zÀ-ÿ•·]',m[2])):
   current={'key':f'{section}.{int(m[1])}','module':section,'item':int(m[1]),'pdf_page':page,'page':page+83,'text':m[2]};items.append(current)
  elif current:current['text']+=' '+line
for item in items:item['text']=re.sub(r'\s+',' ',item['text']).strip()
counts={s:sum(x['module']==s for x in items) for s in SECTIONS.values()}
duplicates=[x['key'] for x in items if sum(y['key']==x['key'] for y in items)>1]
result={'source':'ANEXO III.pdf','pages':100,'counts':counts,'items':items}
(ROOT/'docs/anexo-iii-itens.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'counts':counts,'total':len(items),'duplicates':duplicates},ensure_ascii=False))
for section in counts:
 nums=[x['item'] for x in items if x['module']==section]
 print(section,'faltas na sequência:',sorted(set(range(1,max(nums)+1))-set(nums)))
