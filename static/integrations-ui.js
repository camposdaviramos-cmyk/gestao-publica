'use strict';
const integrationState={entity:'',environment:'homologacao',items:[],filter:''};
const integrationAccessible=accessible,integrationShell=shell,integrationSettings=settingsPage,integrationClear=clearAccount;
names.integrations='Integrações externas';icons.integrations='link';
accessible=function(r){return r==='integrations'?state.me?.user?.group_id===1&&can('settings'):integrationAccessible(r);};
shell=function(){integrationShell();if(accessible('integrations'))$('.sidebar nav').insertAdjacentHTML('beforeend',navItem('integrations'));};
clearAccount=function(){Object.assign(integrationState,{entity:'',environment:'homologacao',items:[],filter:'',draft:null,job:null,siconfiReport:null});integrationClear();};
settingsPage=async function(){return await integrationSettings()+(accessible('integrations')?'<section class="panel int-settings"><div class="panel-head"><div><h2>Integrações externas</h2><p>Credenciais, ambientes, consultas e publicações oficiais.</p></div><a class="button" href="#/integrations">'+icon('link')+'Abrir central</a></div></section>':'');};
const intEnv=env=>env==='producao'?'Produção':'Homologação';
const intButton=(label,action,attrs='',primary=false)=>`<button type="button" class="button ${primary?'primary':''}" data-action="int-${action}" ${attrs}>${esc(label)}</button>`;
async function integrationsPage(){
 const entities=(await api('/erp/entities')).items;
 if(!entities.some(x=>String(x.id)===String(integrationState.entity)))integrationState.entity=entities[0]?.id||'';
 if(!integrationState.entity)return heading('Integrações externas','Configure uma entidade antes de continuar.');
 const data=await api('/integrations?entity='+integrationState.entity);integrationState.items=data.items;
 const env=integrationState.environment;
 const cards=data.items.filter(p=>!integrationState.filter||(p.label+' '+p.area).toLowerCase().includes(integrationState.filter.toLowerCase())).map(p=>{
  const available=env in p.environments,c=p.configs[env];
  return `<article class="panel int-card" data-provider="${p.id}"><div class="int-card-top"><span class="stat-icon">${icon('link')}</span><span class="muted">${esc(p.area)}</span></div><h2>${esc(p.label)}</h2><p>${esc(p.description)}</p><div class="int-status">${badge(available?(c.enabled?'Ativa':c.version?'Configurada':'Não configurada'):'Somente produção')}<small>${esc(p.status)}</small></div><div class="int-actions">${available?intButton('Configurar','config',`data-provider="${p.id}"`):''}${available&&Object.keys(p.operations).length?intButton('Consultar','consult',`data-provider="${p.id}" ${!c?.enabled?'disabled':''}`):''}${available?intButton('Histórico','history',`data-provider="${p.id}"`):''}${p.id==='esocial'&&available?'<button class="button" data-action="eso-list">Eventos e recibos</button>':''}${p.id==='ldap'&&available&&can('users')?'<button class="button" data-action="ent-bindings">Vincular usuários</button>':''}${p.id==='siconfi'&&available&&can('control','write')?'<button class="button" data-action="sic-reports">Agenda e extrato</button>':''}${p.documentation?`<a class="button" href="${esc(p.documentation)}" target="_blank" rel="noopener noreferrer">Fonte oficial ${icon('external')}</a>`:''}</div></article>`;
 }).join('');
 return heading('Integrações externas','Parâmetros por entidade, credenciais protegidas e operações rastreáveis.',can('procurement')?intButton('Publicações PNCP','jobs'):'')+
 `<div class="erp-context">${selectField('entity','Entidade',entities.map(e=>[e.id,e.name]),integrationState.entity,'id="int-entity"')}${selectField('environment','Ambiente',[['homologacao','Homologação'],['producao','Produção']],env,'id="int-environment"')}${field('exercise','Exercício das publicações',erpState.exercise,'number','id="int-exercise" min="2000" max="2100"')}</div>`+
 notice(env==='producao'?'Ambiente de produção. Consultar não publica documentos; cada envio ao PNCP exige revisão e confirmação do destino.':'Ambiente de homologação. Serviços públicos sem ambiente de testes estão disponíveis na opção Produção.')+
 `<form id="int-filter" class="toolbar"><input name="filter" type="search" aria-label="Filtrar integrações" placeholder="Buscar serviço ou área…" value="${esc(integrationState.filter)}"><button class="button" type="submit">Buscar</button></form><div class="erp-module-grid int-grid">${cards}</div>`;
}
function intProvider(id){const p=integrationState.items.find(p=>p.id===id);if(!p)throw new Error('Atualize a página de integrações.');return p;}
function intContext(){return {entity:Number(integrationState.entity),environment:integrationState.environment};}
function intConfig(id){
 const p=intProvider(id),env=integrationState.environment,c=p.configs[env];
 const fields=Object.entries(p.fields).map(([key,f])=>{
  const saved=c.secrets_set[key],hint=f.secret?(saved?'Já cadastrada. Deixe vazio para manter; informe um novo valor para substituir.':'Ainda não cadastrada.'):'';
  let html=f.type==='pem'?textField(key,esc(f.label),'','maxlength="100000" autocomplete="off"')+(saved?'<small>Já cadastrada. Deixe vazio para manter.</small>':''):f.type==='certificate'?`<label class="field full">${esc(f.label)}<input name="${key}" type="file" accept=".pfx,.p12"><small>${hint} Limite: 150 KB.</small></label>`:field(key,esc(f.label),f.secret?'':c.parameters[key]||'',f.secret?'password':'text',f.secret?'autocomplete="new-password" maxlength="4096"':'maxlength="250"',hint);
  if(f.secret&&saved)html+=`<label class="check"><input name="clear_${key}" type="checkbox">Remover ${esc(f.label)}</label>`;
  return html;
 }).join('');
 openModal(esc(p.label),`<form id="int-config" data-provider="${id}" data-version="${c.version}"><p>${esc(p.description)}</p><p><strong>${intEnv(env)}</strong> · ${esc(p.version)}</p>${p.environments[env]?`<p class="int-endpoint">${esc(p.environments[env])}</p>`:''}<fieldset ${can('settings','write')?'':'disabled'} class="int-fieldset"><div class="form-grid">${fields||'<p>Este serviço não possui credenciais de API validadas para cadastro.</p>'}</div>${p.activatable?`<label class="check int-enable"><input name="enabled" type="checkbox" ${c.enabled?'checked':''}>Ativar conector neste ambiente</label>`:notice(p.status,true)}${c.certificate.subject?`<dl class="erp-details"><div><dt>Titular</dt><dd>${esc(c.certificate.subject)}</dd></div><div><dt>Validade</dt><dd>${date(c.certificate.expires_at,true)}</dd></div></dl>${notice(c.certificate.chain_validation)}`:''}<div class="form-error" role="alert"></div>${formActions()}</fieldset></form>`,'Configuração exclusiva desta entidade e ambiente');
}
async function intConsult(id,operation='test'){
 const p=intProvider(id);openModal('Consulta · '+esc(p.label),'<div class="loading-panel"><div class="loader"></div>Consultando o serviço oficial…</div>',intEnv(integrationState.environment));
 const r=await api('/integrations/'+id+'/consult','POST',{...intContext(),operation});
 openModal('Consulta · '+esc(p.label),notice(esc(r.message),!r.success)+(r.result?`<pre class="int-json">${esc(JSON.stringify(r.result,null,2))}</pre>`:'')+(id==='ibge'&&r.success?intButton('Consultar distritos','districts','data-provider="ibge"'):''),intEnv(integrationState.environment));
}
async function intHistory(id){
 const p=intProvider(id),d=await api(`/integrations/${id}/history?entity=${integrationState.entity}&environment=${integrationState.environment}`);
 openModal('Histórico · '+esc(p.label),d.items.length?`<div class="int-history">${d.items.map(x=>`<article><strong>${x.success?'Concluída':'Falhou'} · ${date(x.created_at,true)}</strong><p>${esc(x.message)}</p><small>${esc(x.actor)} · ${x.duration_ms} ms</small></article>`).join('')}</div>`:empty('Nenhuma consulta realizada','Os resultados das consultas serão registrados aqui.'),intEnv(integrationState.environment));
}
async function intJobs(){
 const d=await api(`/integration-jobs?entity=${integrationState.entity}&environment=${integrationState.environment}`);
 openModal('Publicações PNCP',intButton('Preparar publicação','new-job','',true)+`<div class="int-history">${d.items.map(x=>`<article><strong>${esc(x.source_name)}</strong><p>${badge(x.state)} · ${intEnv(x.environment)} · ${date(x.created_at,true)}</p>${intButton('Revisar pacote','job',`data-id="${x.id}"`)}</article>`).join('')||'<p>Nenhum pacote preparado neste ambiente.</p>'}</div>`,'Revisão, envio e recibos por ambiente');
}
async function intNewJob(){
 openModal('Preparar publicação PNCP',`<form id="int-source"><div class="form-grid">${selectField('kind','Cadastro de origem',[['processes','Processo de contratação'],['contracts','Contrato']],'processes')}${field('q','Buscar por número ou objeto','','search')}</div><div class="form-error" role="alert"></div><div class="form-actions"><button class="button primary" type="submit">Buscar cadastros</button></div></form><div id="int-source-results"></div>`,intEnv(integrationState.environment));
}
const pncpLabels={codigoUnidadeCompradora:'Código da unidade compradora',tipoInstrumentoConvocatorioId:'Instrumento convocatório · código PNCP',modalidadeId:'Modalidade · código PNCP',modoDisputaId:'Modo de disputa · código PNCP',numeroCompra:'Número da contratação (sem ano)',anoCompra:'Ano da contratação',numeroProcesso:'Número do processo',objetoCompra:'Objeto',srp:'Sistema de registro de preços',amparoLegalId:'Amparo legal · código PNCP',dataAberturaProposta:'Início do recebimento de propostas (Brasília)',dataEncerramentoProposta:'Encerramento de propostas (Brasília)',numeroItem:'Número do item',materialOuServico:'Material ou serviço',tipoBeneficioId:'Benefício · código PNCP',incentivoProdutivoBasico:'Incentivo produtivo básico',descricao:'Descrição',quantidade:'Quantidade',unidadeMedida:'Unidade de medida',orcamentoSigiloso:'Orçamento sigiloso',valorUnitarioEstimado:'Valor unitário estimado',valorTotal:'Valor total estimado',criterioJulgamentoId:'Critério de julgamento · código PNCP',itemCategoriaId:'Categoria do item · código PNCP',aplicabilidadeMargemPreferenciaNormal:'Margem de preferência normal',aplicabilidadeMargemPreferenciaAdicional:'Margem de preferência adicional',cnpjCompra:'CNPJ do órgão da contratação',sequencialCompra:'Sequencial da contratação no PNCP',tipoContratoId:'Tipo de contrato · código PNCP',numeroContratoEmpenho:'Número do contrato',anoContrato:'Ano do contrato',processo:'Processo',categoriaProcessoId:'Categoria do processo · código PNCP',receita:'Contrato de receita',codigoUnidade:'Código da unidade executora',niFornecedor:'CPF/CNPJ do fornecedor',tipoPessoaFornecedor:'Tipo de pessoa do fornecedor',nomeRazaoSocialFornecedor:'Fornecedor',objetoContrato:'Objeto do contrato',valorInicial:'Valor inicial',numeroParcelas:'Número de parcelas',valorParcela:'Valor da parcela',valorGlobal:'Valor global',valorAcumulado:'Valor acumulado',dataAssinatura:'Data de assinatura',dataVigenciaInicio:'Início da vigência',dataVigenciaFim:'Fim da vigência'};
function pncpInput(key,value,prefix=''){
 const name=prefix+key,label=pncpLabels[key]||key;
 if(typeof value==='boolean')return `<label class="check"><input name="${name}" type="checkbox" ${value?'checked':''}>${esc(label)}</label>`;
 if(key==='materialOuServico')return selectField(name,label,[['','Selecione'],['M','Material'],['S','Serviço']],value,'required');
 const type=key.startsWith('data')?(key.includes('Proposta')?'datetime-local':'date'):(typeof value==='number'||value===null?'number':'text');
 return field(name,esc(label),value??'',type,(type==='number'?'step="any" min="0"':type==='datetime-local'?'step="1"':'maxlength="5120"')+(value===null?' required':''));
}
async function intPrepare(id){
 const r=await api('/integrations/pncp/template/'+id);integrationState.entity=r.entity;integrationState.draft=r;
 const p=r.payload,fields=Object.entries(p).filter(([k])=>k!=='itensCompra').map(([k,v])=>pncpInput(k,v)).join('');
 const items=(p.itensCompra||[]).map((item,i)=>`<details class="int-item"><summary>Item ${item.numeroItem} · ${esc(item.descricao)}</summary><div class="form-grid">${Object.entries(item).map(([k,v])=>pncpInput(k,v,`item${i}_`)).join('')}</div>${field(`item${i}_percentualMargemPreferenciaNormal`,'Percentual de margem normal','','number','min="0" max="99.9999" step=".0001"')}${field(`item${i}_percentualMargemPreferenciaAdicional`,'Percentual de margem adicional','','number','min="0" max="99.9999" step=".0001"')}</details>`).join('');
 openModal('Preparar publicação',`<form id="int-prepare" data-id="${id}"><p><strong>${esc(r.source_name)}</strong> · ${intEnv(integrationState.environment)}</p>${notice('Confira os códigos nas tabelas oficiais do PNCP. Os dados e valores de origem precisam corresponder ao cadastro. Preparar o pacote não envia a publicação.')}<a class="button" href="https://pncp.gov.br/app/entidades-dominio" target="_blank" rel="noopener noreferrer">Tabelas oficiais do PNCP</a><div class="form-grid int-form-space">${fields}</div>${items}<div class="form-grid int-form-space">${field('document_title','Título do documento','','text','required maxlength="255"')}${field('document_type','Tipo de documento · código PNCP','','number','required min="1"')}<label class="field full">Documento da publicação (PDF, até 500 KB)<input type="file" name="document" accept="application/pdf" required></label></div><div class="form-error" role="alert"></div><div class="form-actions"><button class="button primary" type="submit">Preparar para revisão</button></div></form>`,'Pacote separado por entidade e ambiente');
}
async function intJob(id){
 const r=await api('/integration-jobs/'+id),j=r.item;integrationState.job=j;
 const p=JSON.parse(j.payload);let actions=intButton('Baixar PDF para revisão','document',`data-id="${id}"`);
 if(['Preparado','Rejeitado'].includes(j.state))actions+=intButton('Aprovar pacote','approve',`data-id="${id}"`);
 if(j.state==='Aprovado')actions+=intButton('Enviar ao PNCP','send',`data-id="${id}"`,true);
 if(['Preparado','Aprovado','Rejeitado'].includes(j.state))actions+=intButton('Cancelar pacote','cancel',`data-id="${id}"`);
 if(j.state==='Enviando')actions+=intButton('Verificar envio interrompido','recover',`data-id="${id}"`);
 const summary=Object.entries(p).filter(([k])=>k!=='itensCompra').map(([k,v])=>`<div><dt>${esc(pncpLabels[k]||k)}</dt><dd>${esc(typeof v==='boolean'?(v?'Sim':'Não'):v)}</dd></div>`).join('');
 openModal('Pacote PNCP #'+id,`<p>${badge(j.state)} · <strong>${intEnv(j.environment)}</strong></p>${j.message?notice(esc(j.message),j.state==='Resultado incerto'):''}<div class="int-actions">${actions}</div><dl class="erp-details">${summary}</dl>${p.itensCompra?`<details class="int-item"><summary>Conferir ${p.itensCompra.length} itens</summary><pre class="int-json">${esc(JSON.stringify(p.itensCompra,null,2))}</pre></details>`:''}<p class="int-digest">SHA-256 do pacote: ${esc(j.digest)}</p><details class="int-item"><summary>Recibo e retorno do PNCP</summary><pre class="int-json">${esc(JSON.stringify(JSON.parse(j.receipt),null,2))}</pre></details><div class="int-history">${r.events.map(e=>`<article><strong>${esc(e.state)}</strong><p>${esc(e.detail)}</p><small>${esc(e.actor)} · ${date(e.created_at,true)}</small></article>`).join('')}</div>`,'Leia o documento e confira os dados antes de aprovar.');
}
function intActionForm(operation){
 const j=integrationState.job,token=j.environment==='producao'?'PUBLICAR EM PRODUCAO':'ENVIAR PARA HOMOLOGACAO';
 openModal(operation==='send'?'Confirmar envio ao PNCP':'Cancelar pacote',`<form id="int-job-action" data-operation="${operation}" data-id="${j.id}" data-version="${j.version}">${operation==='send'?notice('Destino: '+intEnv(j.environment)+'. Esta ação transmite o documento e os dados ao PNCP.')+field('confirmation','Digite '+token,'','text','required autocomplete="off"'):textField('reason','Motivo do cancelamento','','required minlength="10" maxlength="1000"')}<div class="form-error" role="alert"></div><div class="form-actions"><button class="button primary" type="submit">${operation==='send'?'Confirmar envio':'Cancelar pacote'}</button></div></form>`);
}
async function intReadFile(file,max){if(!file?.size||file.size>max)throw new Error('Arquivo ausente ou maior que o limite permitido.');const bytes=new Uint8Array(await file.arrayBuffer());let value='';for(let i=0;i<bytes.length;i+=8192)value+=String.fromCharCode(...bytes.subarray(i,i+8192));return btoa(value);}
document.addEventListener('change',e=>{if(e.target.id==='int-exercise'){e.stopImmediatePropagation();const v=Number(e.target.value);if(Number.isInteger(v)&&v>=2000&&v<=2100)erpState.exercise=v;else e.target.value=erpState.exercise;return;}if(!['int-entity','int-environment'].includes(e.target.id))return;e.stopImmediatePropagation();integrationState[e.target.id==='int-entity'?'entity':'environment']=e.target.value;route();},true);
document.addEventListener('click',async e=>{
 const b=e.target.closest('[data-action^="int-"]');if(!b)return;e.preventDefault();e.stopImmediatePropagation();if(b.disabled)return;b.disabled=true;
 try{const action=b.dataset.action.slice(4),id=b.dataset.id,p=b.dataset.provider;
  if(action==='config')intConfig(p);
  else if(action==='consult'||action==='districts')await intConsult(p,action==='districts'?'districts':'test');
  else if(action==='history')await intHistory(p);
  else if(action==='jobs')await intJobs();
  else if(action==='new-job')await intNewJob();
  else if(action==='prepare')await intPrepare(id);
  else if(action==='job')await intJob(id);
  else if(action==='document')await download('/integration-jobs/'+id+'/document');
  else if(action==='send'||action==='cancel')intActionForm(action);
  else if(action==='approve'||action==='recover'){const r=await api(`/integration-jobs/${id}/${action}`,'POST',{version:integrationState.job.version});toast(r.message);await intJob(id);}
 }catch(error){toast(error.message,true);}finally{b.disabled=false;}
},true);
document.addEventListener('submit',async e=>{
 const f=e.target;if(!f.id.startsWith('int-'))return;e.preventDefault();e.stopImmediatePropagation();const b=$('[type=submit]',f);if(b?.disabled)return;if(b)b.disabled=true;
 try{const fd=new FormData(f);
  if(f.id==='int-filter'){integrationState.filter=fd.get('filter');await route();}
  if(f.id==='int-config'){
   const p=intProvider(f.dataset.provider),parameters={},secrets={},clear=[];
   for(const [name,spec] of Object.entries(p.fields)){if(fd.get('clear_'+name))clear.push(name);if(spec.secret){const value=spec.type==='certificate'?(fd.get(name)?.size?await intReadFile(fd.get(name),150000):''):fd.get(name);if(value)secrets[name]=value;}else parameters[name]=fd.get(name)||'';}
   const r=await api('/integrations/'+p.id,'PUT',{...intContext(),version:Number(f.dataset.version),enabled:fd.get('enabled')==='on',parameters,secrets,clear_secrets:clear});closeModal();toast(r.message);await route();
  }
  if(f.id==='int-source'){
   const d=await api(`/erp/procurement/${fd.get('kind')}?entity=${integrationState.entity}&exercise=${erpState.exercise}&q=${encodeURIComponent(fd.get('q'))}&limit=100`);
   $('#int-source-results').innerHTML='<p>Exercício '+erpState.exercise+'</p>'+d.items.map(x=>`<article class="int-source-row"><span>${esc(x.code)} · ${esc(x.name)}</span>${intButton('Selecionar','prepare',`data-id="${x.id}"`)}</article>`).join('')+(d.total>100?notice('Há mais resultados. Refine a busca.'):!d.items.length?notice('Nenhum cadastro encontrado neste exercício.'): '');
  }
  if(f.id==='int-prepare'){
   const source=integrationState.draft.payload,payload={};
   function read(key,value,prefix=''){const name=prefix+key;if(typeof value==='boolean')return fd.get(name)==='on';if(typeof value==='number'||value===null)return fd.get(name)===''?null:Number(fd.get(name));let v=String(fd.get(name)||'');if(key.includes('Proposta')&&v.length===16)v+=':00';return v;}
   for(const [k,v] of Object.entries(source))if(k!=='itensCompra')payload[k]=read(k,v);
   if(source.itensCompra)payload.itensCompra=source.itensCompra.map((item,i)=>{const x={};for(const [k,v] of Object.entries(item))x[k]=read(k,v,`item${i}_`);for(const suffix of ['Normal','Adicional'])if(x['aplicabilidadeMargemPreferencia'+suffix])x['percentualMargemPreferencia'+suffix]=Number(fd.get(`item${i}_percentualMargemPreferencia${suffix}`));return x;});
   const r=await api('/integration-jobs','POST',{...intContext(),source_id:Number(f.dataset.id),payload,document:await intReadFile(fd.get('document'),500000),document_title:fd.get('document_title'),document_type:Number(fd.get('document_type'))});integrationState.draft=null;toast(r.message);await intJob(r.id);
  }
  if(f.id==='int-job-action'){const r=await api(`/integration-jobs/${f.dataset.id}/${f.dataset.operation}`,'POST',{version:Number(f.dataset.version),confirmation:fd.get('confirmation'),reason:fd.get('reason')});toast(r.message,r.state==='Resultado incerto');await intJob(f.dataset.id);}
 }catch(error){const target=$('.form-error',f);if(target)target.textContent=error.message;else toast(error.message,true);}finally{if(b)b.disabled=false;}
},true);
