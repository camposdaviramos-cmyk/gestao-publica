"""Validação e conversão de cadastros para os serviços de inclusão do PNCP 2.6."""
import hashlib,json,re
from datetime import date,datetime
from decimal import Decimal,ROUND_HALF_UP
from auth import ApiError
from db import get_db
from erp_core import load,integer,decimal,valid_document

def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)

def sources(source):
 rows=[source]
 if source['kind']=='processes':
  rows += [load(x['id'],'procurement','items') for x in get_db().execute("SELECT id FROM erp_objects WHERE entity_id=? AND module='procurement' AND kind='items' AND deleted=0 AND json_extract(data,'$.process')=? ORDER BY id",(source['entity_id'],source['id']))]
 else:rows += [load(source['data']['supplier'],'procurement','suppliers'),load(source['data']['process'],'procurement','processes')]
 return rows

def fingerprint(source):return hashlib.sha256(canonical([(x['id'],x['version'],x['state'],x['data']) for x in sources(source)]).encode()).hexdigest()

def template(source):
 d=source['data']
 if source['kind']=='contracts':
  supplier=load(d['supplier'],'procurement','suppliers');process=load(d['process'],'procurement','processes');value=d['amount']/100
  return {'cnpjCompra':'','anoCompra':process['exercise'],'sequencialCompra':None,'tipoContratoId':None,'numeroContratoEmpenho':source['code'],
   'anoContrato':source['exercise'],'processo':process['code'],'categoriaProcessoId':None,'receita':False,'codigoUnidade':'',
   'niFornecedor':supplier['data']['document'],'tipoPessoaFornecedor':'PF' if len(supplier['data']['document'])==11 else 'PJ',
   'nomeRazaoSocialFornecedor':supplier['name'],'objetoContrato':source['name'],'valorInicial':value,'numeroParcelas':1,'valorParcela':value,
   'valorGlobal':value,'valorAcumulado':value,'dataAssinatura':'','dataVigenciaInicio':d['start'],'dataVigenciaFim':d['end']}
 items=[]
 for item in sources(source)[1:]:
  x=item['data'];n=integer(item['code'],'Número do item',1);q=Decimal(x['quantity'])/1000000;v=Decimal(x['unit_price'])/100
  items.append({'numeroItem':n,'materialOuServico':'','tipoBeneficioId':None,'incentivoProdutivoBasico':False,'descricao':item['name'],
   'quantidade':float(q),'unidadeMedida':x['unit'],'orcamentoSigiloso':False,'valorUnitarioEstimado':float(v),
   'valorTotal':float((q*v).quantize(Decimal('.0001'),rounding=ROUND_HALF_UP)),'criterioJulgamentoId':None,'itemCategoriaId':3,
   'aplicabilidadeMargemPreferenciaNormal':False,'aplicabilidadeMargemPreferenciaAdicional':False})
 return {'codigoUnidadeCompradora':'','tipoInstrumentoConvocatorioId':None,'modalidadeId':None,'modoDisputaId':None,
  'numeroCompra':source['code'].split('/')[0],'anoCompra':source['exercise'],'numeroProcesso':source['code'],'objetoCompra':source['name'],
  'srp':False,'amparoLegalId':None,'dataAberturaProposta':'','dataEncerramentoProposta':'','itensCompra':sorted(items,key=lambda x:x['numeroItem'])}

def text_value(payload,name,maxlen,required=True):
 value=payload.get(name)
 if not required and value in (None,''):return
 if not isinstance(value,str) or not value.strip() or len(value)>maxlen or any(ord(c)<32 for c in value):raise ApiError(name+': texto obrigatório ou inválido.')

def boolean(payload,*names):
 for name in names:
  if not isinstance(payload.get(name),bool):raise ApiError(name+': informe verdadeiro ou falso.')

def number(payload,name,places=4):
 value=payload.get(name)
 if isinstance(value,bool) or not isinstance(value,(int,float)):raise ApiError(name+': informe um número.')
 n=decimal(value,name)
 if n.as_tuple().exponent < -places:raise ApiError(name+': precisão máxima de quatro casas decimais.')
 return n

def date_value(payload,name,with_time=False):
 value=payload.get(name)
 try:
  if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}' if with_time else r'\d{4}-\d{2}-\d{2}',value):raise ValueError()
  return datetime.fromisoformat(value) if with_time else date.fromisoformat(value)
 except ValueError:raise ApiError(name+': data inválida'+(' (horário de Brasília, AAAA-MM-DDTHH:MM:SS).' if with_time else '.')) from None

def validate(source,payload):
 if not isinstance(payload,dict):raise ApiError('Dados da publicação devem ser um objeto JSON.')
 expected=template(source)
 if source['kind']=='contracts':
  fixed=['numeroContratoEmpenho','anoContrato','processo','niFornecedor','tipoPessoaFornecedor','nomeRazaoSocialFornecedor','objetoContrato','valorInicial','dataVigenciaInicio','dataVigenciaFim']
  allowed=set(expected)|{'sequencialAta','frutoAdesao','temRemanejamento','informacaoComplementar','identificadorCipi','urlCipi'}
  for field,maxlen in [('codigoUnidade',20),('numeroContratoEmpenho',50),('processo',50),('nomeRazaoSocialFornecedor',100),('objetoContrato',5120)]:text_value(payload,field,maxlen)
  valid_document(payload.get('cnpjCompra',''),'cnpj');boolean(payload,'receita')
  for f in ['anoCompra','anoContrato']:integer(payload.get(f),f,2000,2100)
  for f in ['sequencialCompra','tipoContratoId','categoriaProcessoId','numeroParcelas']:integer(payload.get(f),f,1)
  for f in ['valorInicial','valorParcela','valorGlobal','valorAcumulado']:number(payload,f)
  if date_value(payload,'dataAssinatura')>date_value(payload,'dataVigenciaFim') or date_value(payload,'dataVigenciaInicio')>date_value(payload,'dataVigenciaFim'):raise ApiError('Datas do contrato inconsistentes.')
  for f in ['frutoAdesao','temRemanejamento']:
   if f in payload:boolean(payload,f)
  if 'sequencialAta' in payload:integer(payload['sequencialAta'],'Sequencial da ata',1)
 else:
  fixed=['anoCompra','numeroProcesso','objetoCompra'];allowed=set(expected)|{'informacaoComplementar','linkSistemaOrigem','linkProcessoEletronico','justificativaPresencial','fontesOrcamentarias'}
  for f,maxlen in [('codigoUnidadeCompradora',20),('numeroCompra',50),('numeroProcesso',50),('objetoCompra',5120)]:text_value(payload,f,maxlen)
  for f in ['tipoInstrumentoConvocatorioId','modalidadeId','modoDisputaId','amparoLegalId']:integer(payload.get(f),f,1)
  integer(payload.get('anoCompra'),'Ano da compra',2000,2100);boolean(payload,'srp')
  if int(payload['tipoInstrumentoConvocatorioId']) in (1,2):
   if date_value(payload,'dataAberturaProposta',True)>=date_value(payload,'dataEncerramentoProposta',True):raise ApiError('Encerramento deve ser posterior à abertura das propostas.')
  items=payload.get('itensCompra')
  if not isinstance(items,list) or not 1<=len(items)<=2000 or len(items)!=len(expected['itensCompra']):raise ApiError('Envie todos os itens cadastrados: mínimo 1 e máximo 2.000.')
  numbers=[]
  for item,original in zip(items,expected['itensCompra']):
   if not isinstance(item,dict):raise ApiError('Item inválido.')
   for f in ['numeroItem','descricao','quantidade','unidadeMedida','valorUnitarioEstimado','valorTotal']:
    if item.get(f)!=original[f]:raise ApiError('Dados do item divergentes do cadastro: '+f+'. Corrija o cadastro antes de publicar.')
   numbers.append(integer(item['numeroItem'],'Número do item',1))
   for f in ['tipoBeneficioId','criterioJulgamentoId']:integer(item.get(f),f,1)
   if item.get('materialOuServico') not in ['M','S']:raise ApiError('Classifique cada item como M (material) ou S (serviço).')
   boolean(item,'incentivoProdutivoBasico','orcamentoSigiloso','aplicabilidadeMargemPreferenciaNormal','aplicabilidadeMargemPreferenciaAdicional')
   text_value(item,'descricao',2048);text_value(item,'unidadeMedida',30)
   for f in ['quantidade','valorUnitarioEstimado','valorTotal']:number(item,f)
   if number(item,'quantidade')<=0:raise ApiError('Quantidade deve ser positiva.')
   for suffix in ['Normal','Adicional']:
    if item['aplicabilidadeMargemPreferencia'+suffix] and number(item,'percentualMargemPreferencia'+suffix)>=100:raise ApiError('Margem de preferência deve ser inferior a 100%.')
   if item['aplicabilidadeMargemPreferenciaAdicional'] and not item['aplicabilidadeMargemPreferenciaNormal']:raise ApiError('Margem adicional requer margem normal.')
   extras={'patrimonio','codigoRegistroImobiliario','percentualMargemPreferenciaNormal','percentualMargemPreferenciaAdicional','codigoTipoMargemPreferencia','inConteudoNacional','ncmNbsCodigo','ncmNbsDescricao','catalogoId','categoriaItemCatalogoId','catalogoCodigoItem','informacaoComplementar'}
   if set(item)-set(original)-extras:raise ApiError('Campo desconhecido no item PNCP.')
  if len(set(numbers))!=len(numbers):raise ApiError('Numeração de itens duplicada.')
  if 'fontesOrcamentarias' in payload:
   if not isinstance(payload['fontesOrcamentarias'],list):raise ApiError('Fontes orçamentárias inválidas.')
   for v in payload['fontesOrcamentarias']:integer(v,'Fonte orçamentária',1)
 for f in fixed:
  if payload.get(f)!=expected[f]:raise ApiError('Publicação divergente do cadastro: '+f+'.')
 if set(payload)-allowed:raise ApiError('Campo não previsto na publicação PNCP.')
 for f in ['informacaoComplementar','linkSistemaOrigem','linkProcessoEletronico','justificativaPresencial','identificadorCipi','urlCipi']:
  if f in payload:text_value(payload,f,5120 if f=='informacaoComplementar' else 512,False)
 try:canonical(payload)
 except (ValueError,TypeError):raise ApiError('Número ou tipo JSON inválido.') from None
