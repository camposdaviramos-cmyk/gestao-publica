/* Forms use the shared modal and the application's authenticated API client. */
(() => {
  const F = (name, label, type = 'text', value = '', optional = false) => [name,label,type,value,optional];
  const id = (name, label) => F(name,label,'number');
  const date = (name, label) => F(name,label,'date');
  const show = (title, data) => ModulesUI.show(title,data);
  const postForm = (title, path, fields, done, transform = data => data) =>
    ModulesUI.form(title,fields,data => api(path,'POST',transform(data)),done || (data => show(title,data)));

  FinanceUI.openNewJournalModal = () => postForm('Novo lançamento contábil','/finance/journal/post',[
    id('exercise','Exercício'),date('entry_date','Data do lançamento'),F('fact_type','Fato contábil'),
    F('debit_account','Conta de débito'),F('credit_account','Conta de crédito'),id('amount','Valor (R$)'),
    F('history_summary','Histórico','textarea'),F('superavit_attribute','Atributo (F ou P)')
  ],() => FinanceUI.loadJournalEntries(),d => ({...d,amount_cents:Math.round(d.amount*100)}));
  FinanceUI.openNewReinfInvoiceModal = () => postForm('Registrar nota fiscal / RPS','/finance/reinf/invoices',[
    id('taxpayer_id','Código do contribuinte'),F('creditor_document','CPF / CNPJ do credor'),F('creditor_name','Nome do credor'),
    F('invoice_number','Número da nota fiscal'),F('service_type_code','Código do serviço'),id('gross','Valor bruto (R$)'),id('rate_percent','Alíquota (%)'),
    F('rps_number','Número do RPS','text','',true)
  ],null,d => ({...d,gross_cents:Math.round(d.gross*100)}));
  FinanceUI.openCheckModal = () => postForm('Emitir cheque','/finance/treasury/checks',[
    F('bank_account_code','Conta bancária'),id('check_number','Número do cheque'),F('bearer_name','Favorecido'),id('amount','Valor (R$)')
  ],null,d => ({...d,amount_cents:Math.round(d.amount*100)}));
  FinanceUI.openAdvanceFundModal = () => postForm('Conceder adiantamento','/finance/treasury/advance-funds',[
    F('server_cpf','CPF do servidor'),F('server_name','Nome do servidor'),F('commitment_id','Empenho'),id('amount','Valor (R$)'),F('advance_type','Tipo de adiantamento','text','Suprimento_Fundos')
  ],() => FinanceUI.loadAdvanceFunds(),d => ({...d,amount_cents:Math.round(d.amount*100)}));
  FinanceUI.renderAccountability = fundId => postForm('Prestar contas do adiantamento','/finance/treasury/advance-funds/accountability',[
    F('fund_id','Código do adiantamento','number',fundId || ''),id('spent','Valor utilizado (R$)'),id('returned','Valor devolvido (R$)')
  ],() => FinanceUI.loadAdvanceFunds(),d => ({fund_id:d.fund_id,spent_cents:Math.round(d.spent*100),returned_cents:Math.round(d.returned*100)}));
  FinanceUI.generateObeBatch = () => postForm('Gerar lote de ordem bancária','/finance/treasury/obe/generate',[
    id('contract_id','Código do contrato'),F('commitment_ids','Códigos dos empenhos (separados por vírgula)'),F('payment_method','Forma de pagamento','text','OBE')
  ],null,d => {
    const ids=d.commitment_ids.split(',').map(value => Number(value.trim()));
    if (!ids.length || ids.some(value => !Number.isInteger(value) || value<=0)) throw new Error('Informe códigos de empenhos inteiros e positivos.');
    return {...d,commitment_ids:ids};
  });
  FinanceUI.simulateBankReturn = () => postForm('Importar retorno bancário','/finance/treasury/obe/return',[
    id('order_id','Código da ordem bancária'),F('return_content','Arquivo de retorno','file')
  ]);
  FinanceUI.simulateOfxImport = () => postForm('Importar extrato OFX','/finance/treasury/ofx/import',[
    F('bank_account_id','Conta bancária'),F('ofx_content','Arquivo OFX','file')
  ]);
  FinanceUI.runAutoReconcile = () => postForm('Conciliar extrato','/finance/treasury/ofx/reconcile',[id('reconciliation_id','Código da conciliação')]);
  FinanceUI.lockCalendar = () => postForm('Bloquear período de conciliação','/finance/treasury/ofx/lock',[
    id('exercise','Exercício'),id('month','Mês'),F('reason','Justificativa','textarea')
  ]);
  FinanceUI.transmitReinfEvent = eventType => postForm('Processar evento EFD-Reinf','/finance/reinf/events/transmit',[
    F('event_type','Evento','text',eventType),F('competence','Competência','month'),id('taxpayer_id','Código do contribuinte')
  ],d => show('Resultado do processamento EFD-Reinf',d));
  FinanceUI.loadSiaficAuthModal = () => {
    openModal('Identificação do operador SIAFIC',`<p>A autenticação por CPF e a assinatura do termo ainda precisam de validação. A sessão atual pertence a <strong>${ModulesUI.escape(state.me?.name || 'usuário autenticado')}</strong>.</p><p><a class="button" href="#/annex">Consultar a pendência AUD-005 no Anexo III</a></p>`);
    document.querySelector('#modal a').addEventListener('click',() => closeModal());
  };
  FinanceUI.importLoaIntoPpa = () => postForm('Importar LOA para PPA','/finance/budget/import-loa',[
    id('source_exercise','Exercício de origem'),id('target_exercise','Exercício de destino')
  ]);
  SocialUI.dischargeSheltering = shelterId => postForm('Desligamento do acolhimento',`/social/shelterings/${shelterId}/discharge`,[
    date('discharge_date','Data do desligamento'),F('discharge_reason','Motivo do desligamento','textarea')
  ],() => SocialUI.loadShelterings());
  window.duplicateSiconfiRule = (ruleId,ruleCode) => postForm('Duplicar regra SICONFI','/control/siconfi/rules',[
    F('new_code','Novo código da regra','text',ruleCode+'-V2')
  ],() => switchControlTab('siconfi'),d => ({...d,action:'duplicate',rule_id:ruleId}));
  FinanceUI.loadAdvanceFunds = async () => {
    const body=document.getElementById('finance-advance-body');
    if (!body) return;
    try {
      const rows=await api('/finance/treasury/advance-funds');
      const e=ModulesUI.escape;
      body.innerHTML=rows.length ? rows.map(row => `<tr><td>${e(row.request_number)}</td><td>${e(row.server_name)}</td><td>${e(row.advance_type)}</td><td>${e(row.commitment_id)}</td><td>${(row.amount_cents/100).toLocaleString('pt-BR',{style:'currency',currency:'BRL'})}</td><td>${e(row.due_date)}</td><td>${e(row.status)}</td><td>${row.status==='Aberto' ? `<button class="finance-btn-secondary" data-module-click="finance-44" data-arg0="${row.id}">Prestar Contas</button>` : 'Concluído'}</td></tr>`).join('') : '<tr><td colspan="8">Nenhum adiantamento cadastrado.</td></tr>';
    } catch(error) {body.innerHTML=`<tr><td colspan="8">${ModulesUI.escape(error.message)}</td></tr>`;}
  };
  FinanceUI.viewReport = async type => show('Demonstrativo contábil',await api('/finance/dcasp/'+type));
  FinanceUI.viewLrf = async (kind, annex) => show(`LRF ${kind.toUpperCase()} — Anexo ${annex}`,await api(`/finance/lrf/${kind}/${annex}`));
  FinanceUI.exportMscFile = async () => {
    const d = await api('/finance/msc/generate?exercise=2026&month=1&format=XBRL');
    ModulesUI.download('msc-2026-01.xml',d.content,'application/xml');
  };
  FinanceUI.exportManad = async () => {const d=await api('/finance/exports/manad?exercise=2026&competence=2026-01');ModulesUI.download('manad-2026-01.txt',d.content);};
  FinanceUI.exportSigfis = async () => {const d=await api('/finance/exports/sigfis?exercise=2026&competence=01');ModulesUI.download('sigfis-2026-01.xml',d.xml_batch,'application/xml');};

  window.openCopyEmployeeModal = () => postForm('Copiar registro de servidor','/people/employees/copy',[
    id('source_employee_id','Código do servidor de origem'),F('new_registration','Nova matrícula')
  ],() => switchPeopleTab('employees'));
  window.openSubstituteModal = () => postForm('Cadastrar substituto eventual','/people/substitutes',[
    id('original_employee_id','Código do servidor titular'),id('substitute_employee_id','Código do substituto'),
    F('new_registration','Nova matrícula'),id('position_id','Código do cargo'),date('start_date','Início'),date('end_date','Término')
  ],() => switchPeopleTab('employees'));
  window.openReintegrationModal = () => postForm('Reintegração judicial','/people/reintegrations',[
    id('employee_id','Código do servidor'),F('reintegration_type','Tipo','text','JUDICIAL'),F('process_number','Número do processo'),
    F('amnesty_law','Lei de anistia','text','',true),date('retroactive_date','Data retroativa')
  ],() => switchPeopleTab('employees'));
  window.viewEmployeeDetails = async employeeId => {
    const d=await api('/people/employees');
    const employee=d.items.find(e => e.id===employeeId);
    if (!employee) throw new Error('Servidor não encontrado. Atualize a lista.');
    show('Detalhes do servidor',employee);
  };
  window.loadPendingPortalUpdates = async () => show('Atualizações cadastrais pendentes',(await api('/people/portal/updates/pending')).pending_updates);
  window.loadEpiCatalog = async () => show('Catálogo de EPIs',(await api('/people/sst/epis')).epis);
  window.loadPppDocument = () => ModulesUI.form('Consultar PPP',[id('employee_id','Código do servidor')],
    d => api('/people/sst/ppp/'+d.employee_id),d => show('Perfil profissiográfico previdenciário',d.ppp));
  window.openCatModal = () => postForm('Comunicação de acidente de trabalho','/people/sst/cat',[
    id('employee_id','Código do servidor'),F('cat_type','Tipo de CAT','text','INICIAL'),date('accident_date','Data do acidente'),
    F('accident_time','Horário','time'),F('accident_type','Tipo de acidente'),id('hours_worked_before','Horas trabalhadas antes do acidente'),
    F('accident_location','Local do acidente'),F('cep','CEP'),F('address_street','Logradouro'),F('address_neighborhood','Bairro'),
    F('address_city','Município'),F('address_uf','UF'),F('affected_body_part','Parte do corpo atingida'),F('causative_agent','Agente causador'),
    F('doctor_name','Nome do médico'),F('doctor_crm','CRM'),F('doctor_uf','UF do CRM')
  ]);

  SocialUI.openNewFamilyModal = () => postForm('Cadastrar família','/social/families',[
    F('family_code','Código da família'),F('head_nis','NIS do responsável'),F('head_name','Nome do responsável'),F('head_cpf','CPF do responsável'),
    date('head_birth_date','Nascimento'),F('address','Endereço'),F('neighborhood','Bairro'),id('cras_unit_id','Código da unidade CRAS'),
    id('total_income','Renda familiar (R$)'),F('members_count','Quantidade de membros','number',1)
  ],() => SocialUI.refresh());
  SocialUI.openGrantBenefitModal = () => postForm('Conceder benefício','/social/benefits',[
    id('family_id','Código da família'),F('benefit_type','Tipo de benefício'),id('supply_id','Código do material'),id('batch_id','Código do lote'),
    F('quantity','Quantidade','number',1),F('technical_opinion','Parecer técnico','textarea'),F('social_worker_cress','CRESS'),F('social_worker_name','Assistente social responsável')
  ],() => SocialUI.refresh());
  SocialUI.openNewShelteringModal = () => postForm('Admissão em acolhimento','/social/shelterings',[
    id('unit_id','Código da unidade'),F('resident_name','Nome completo'),F('reason','Motivo','textarea'),F('responsible_technician','Técnico responsável')
  ],() => SocialUI.refresh());
  SocialUI.openViolenceRecordModal = () => postForm('Registrar atendimento sigiloso','/social/violence',[
    F('victim_initials','Iniciais da pessoa atendida'),id('age','Idade'),F('police_report_number','Boletim de ocorrência'),
    F('violence_types','Tipos de violência'),F('aggressor_relationship','Vínculo com o agressor'),F('technician_cress_crp','CRESS / CRP do técnico'),
    F('has_children','Possui filhos (0: não, 1: sim)','number',0),F('protective_measure_granted','Medida protetiva (0: não, 1: sim)','number',0),F('shelter_required','Necessita acolhimento (0: não, 1: sim)','number',0)
  ]);
  SocialUI.openNewHousingAppModal = () => postForm('Inscrição habitacional','/social/housing/applications',[
    id('program_id','Código do programa'),id('complex_id','Código do empreendimento'),id('family_id','Código da família'),F('manual_points','Pontuação adicional','number',0)
  ],d => show('Inscrição habitacional registrada',d));
  SocialUI.openNewStockBatchModal = () => postForm('Entrada de estoque','/social/stock/batches',[
    id('warehouse_id','Código do almoxarifado'),id('supply_id','Código do material'),F('batch_number','Número do lote'),id('quantity','Quantidade'),
    date('expiration_date','Validade'),F('supplier_name','Fornecedor')
  ],() => SocialUI.refresh());
  SocialUI.openNewOscModal = () => postForm('Cadastrar organização da sociedade civil','/social/oscs',[
    F('cnpj','CNPJ'),F('corporate_name','Razão social'),F('legal_representative','Representante legal'),F('representative_cpf','CPF do representante')
  ],() => SocialUI.refresh());
  SocialUI.viewOscCertificates = async oscId => {
    const records=await api('/social/oscs');
    const record=records.find(o => o.id===oscId);
    if (!record) throw new Error('OSC não encontrada.');
    show('Certidões e situação cadastrada da OSC',record);
  };
  BiUI.openShareModal = async () => {
    const d=await api('/bi/share','POST',{dashboard_code:({lrf:'DASH-EXEC-LRF',cash:'DASH-FINANCEIRO',funnel:'DASH-FINANCEIRO',hr:'DASH-PESSOAL',procurement:'DASH-COMPRAS',assets:'DASH-PATRIMONIO',person360:'DASH-CIDADAO-360'})[BiUI.currentTab] || BiUI.currentTab,filters:{exercise:BiUI.currentExercise,tab:BiUI.currentTab}});
    openModal('Compartilhar painel',`<label class="field">Link de acesso<input readonly id="bi-share-link" value="${ModulesUI.escape(location.origin+'/api/public/bi/shared/'+encodeURIComponent(d.token))}"></label><p>Selecione e copie o endereço para compartilhar.</p>`);
    document.getElementById('bi-share-link').select();
  };
  BiUI.toggleKioskMode = async () => {
    if (document.getElementById('bi-kiosk-view')) return BiUI.exitKioskMode();
    const cfg=await api('/bi/kiosk/slides');
    const renderers={EXECUTIVE_LRF:'renderLrfTab',FINANCEIRO:'renderCashTab',PESSOAS:'renderHrTab',COMPRAS:'renderProcurementTab',PATRIMONIO:'renderAssetsTab'};
    const slides=(cfg.slides || []).filter(slide => renderers[slide.area]);
    if (!slides.length) throw new Error('Nenhum painel disponível para projeção. Cadastre os painéis do BI.');
    const banner=document.createElement('div');
    banner.id='bi-kiosk-view'; banner.className='bi-kiosk-banner';
    banner.innerHTML='<div class="bi-kiosk-header"><h1 id="bi-kiosk-title"></h1><button class="button" id="bi-kiosk-exit">Sair do modo TV (Esc)</button></div><div id="bi-kiosk-content"></div>';
    document.body.append(banner);
    document.getElementById('bi-kiosk-exit').addEventListener('click',() => BiUI.exitKioskMode());
    let index=0;
    const advance=async () => {
      const slide=slides[index++ % slides.length];
      const content=document.getElementById('bi-kiosk-content');
      if (!content) return;
      document.getElementById('bi-kiosk-title').textContent=slide.title;
      try {await BiUI[renderers[slide.area]](content);}
      catch(error) {content.textContent=error.message;}
      if (document.getElementById('bi-kiosk-view')) BiUI.kioskInterval=setTimeout(advance,Math.max(5,slide.duration || cfg.rotation_interval_seconds || 15)*1000);
    };
    await advance();
  };
})();
