// ============================================================================
// PORTAL DA TRANSPARÊNCIA — RIO GESTÃO / RIO DAS OSTRAS
// Interface pública para 147 cláusulas do Anexo III e LAI (Lei 12.527/2011)
// ============================================================================

let currentPortalTab = 'geral';
let portalDataCache = {};
let fontScale = 1.0;

async function renderTransparencyPortal() {
  document.title = 'Portal da Transparência · Município de Rio das Ostras';
  
  // Detect hash route if present
  const hash = location.hash.replace('#/', '').replace('#', '');
  if (hash && ['geral','despesas','receitas','pagamentos','diarias','licitacoes','contratos','pessoal','concursos','patrimonio','estoque','frotas','divida_ativa','emendas','covid','sic','faq'].includes(hash)) {
    currentPortalTab = hash;
  }

  // Fetch summary
  let summary = portalDataCache.summary;
  if (!summary) {
    summary = await api('/public/transparency/summary');
    portalDataCache.summary = summary;
  }

  const app = $('#app');
  if (!app) return;

  app.innerHTML = `
    <div class="transparency-container" id="transparency-root">
      <!-- Barra de Acessibilidade -->
      <div class="accessibility-bar">
        <div class="access-links">
          <span>Acessibilidade:</span>
          <button type="button" data-action="toggle-contrast" title="Alternar Alto Contraste">
            ${icon('sun')} Alto Contraste
          </button>
          <button type="button" data-action="font-increase" title="Aumentar Fonte">A +</button>
          <button type="button" data-action="font-reset" title="Tamanho Padrão">A</button>
          <button type="button" data-action="font-decrease" title="Diminuir Fonte">A -</button>
        </div>
        <div class="access-links">
          <a href="#/sic">${icon('help')} e-SIC / Ouvidoria</a>
          <button type="button" data-action="portal-theme" title="Alternar Tema Claro/Escuro">
            ${icon(theme === 'dark' ? 'sun' : 'moon')} Modo ${theme === 'dark' ? 'Claro' : 'Escuro'}
          </button>
          <a class="button small" href="/">${icon('lock')} Área Administrativa</a>
        </div>
      </div>

      <!-- Cabeçalho Oficial do Portal -->
      <header class="transparency-header">
        <a class="portal-brand" href="/portal#/geral" data-tab="geral">
          <img src="/static/logo.png" alt="SKYX Tecnologia" style="max-width:145px;height:auto">
          <div>
            <h1>Portal da Transparência</h1>
            <span>Prefeitura Municipal de Rio das Ostras · RJ</span>
          </div>
        </a>
        <div style="text-align:right">
          <div style="font-size:12px;color:var(--muted)">Exercício Financeiro: <strong>${summary.fiscal_year}</strong></div>
          <div style="font-size:11px;color:var(--muted);margin-top:2px">Lei de Acesso à Informação nº 12.527/2011</div>
        </div>
      </header>

      <!-- Breadcrumbs de Navegação -->
      <div class="transparency-breadcrumb" id="transp-breadcrumb">
        <a href="/portal#/geral" data-tab="geral">Início</a>
        <span>/</span>
        <strong id="breadcrumb-current-label">${getTabLabel(currentPortalTab)}</strong>
      </div>

      <!-- Banner de Destaque COVID-19 / Calamidade Pública -->
      ${summary.covid_enabled ? `
        <div class="covid-highlight-banner">
          <div>
            <h3>${icon('shield')} COVID-19 & Calamidade Pública</h3>
            <p>Acesse o painel consolidado de contratos, compras emergenciais, despesas orçamentárias e restos a pagar.</p>
          </div>
          <button class="button small" data-tab="covid" style="background:#dc2626;color:#ffffff;border:none;">
            ${icon('arrow')} Acessar Painel COVID
          </button>
        </div>
      ` : ''}

      <!-- Abas de Navegação do Portal -->
      <nav class="transparency-tabs">
        <button class="transp-tab ${currentPortalTab==='geral'?'active':''}" data-tab="geral">${icon('grid')} Visão Geral</button>
        <button class="transp-tab ${currentPortalTab==='despesas'?'active':''}" data-tab="despesas">${icon('wallet')} Despesas</button>
        <button class="transp-tab ${currentPortalTab==='receitas'?'active':''}" data-tab="receitas">${icon('wallet')} Receitas</button>
        <button class="transp-tab ${currentPortalTab==='pagamentos'?'active':''}" data-tab="pagamentos">${icon('clock')} Ordem Cronológica</button>
        <button class="transp-tab ${currentPortalTab==='diarias'?'active':''}" data-tab="diarias">${icon('file')} Diárias e Viagens</button>
        <button class="transp-tab ${currentPortalTab==='licitacoes'?'active':''}" data-tab="licitacoes">${icon('file')} Licitações & SRP</button>
        <button class="transp-tab ${currentPortalTab==='contratos'?'active':''}" data-tab="contratos">${icon('shield')} Contratos</button>
        <button class="transp-tab ${currentPortalTab==='pessoal'?'active':''}" data-tab="pessoal">${icon('users')} Pessoal & Folha</button>
        <button class="transp-tab ${currentPortalTab==='concursos'?'active':''}" data-tab="concursos">${icon('book')} Concursos</button>
        <button class="transp-tab ${currentPortalTab==='patrimonio'?'active':''}" data-tab="patrimonio">${icon('database')} Patrimônio & Frotas</button>
        <button class="transp-tab ${currentPortalTab==='divida_ativa'?'active':''}" data-tab="divida_ativa">${icon('wallet')} Dívida Ativa</button>
        <button class="transp-tab ${currentPortalTab==='emendas'?'active':''}" data-tab="emendas">${icon('wallet')} Emendas Impositivas</button>
        ${summary.covid_enabled ? `<button class="transp-tab covid-tab ${currentPortalTab==='covid'?'active':''}" data-tab="covid">${icon('shield')} COVID-19</button>` : ''}
        <button class="transp-tab ${currentPortalTab==='sic'?'active':''}" data-tab="sic">${icon('help')} e-SIC / Ouvidoria</button>
        <button class="transp-tab ${currentPortalTab==='faq'?'active':''}" data-tab="faq">${icon('help')} Perguntas Frequentes</button>
      </nav>

      <!-- Conteúdo Dinâmico da Aba -->
      <main id="transparency-content">
        <div style="padding:40px;text-align:center"><div class="spinner"></div> Carregando dados da transparência…</div>
      </main>

      <footer class="app-footer" style="margin-top:40px;padding-top:20px;border-top:1px solid var(--line);">
        <div><strong>Prefeitura Municipal de Rio das Ostras</strong> · Gestão Pública Transparente</div>
        <div style="margin-top:4px;color:var(--muted);font-size:11px">
          Desenvolvido em conformidade com a Lei Federal nº 12.527/2011, LC nº 101/2000 e Lei nº 14.133/2021.
        </div>
      </footer>
    </div>
  `;

  // Bind tab switching
  $$('[data-tab]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const tab = btn.getAttribute('data-tab');
      switchPortalTab(tab);
    });
  });

  // Bind accessibility buttons
  $('[data-action="toggle-contrast"]')?.addEventListener('click', () => {
    document.body.classList.toggle('high-contrast');
  });
  $('[data-action="font-increase"]')?.addEventListener('click', () => {
    fontScale = Math.min(fontScale + 0.1, 1.4);
    $('#transparency-root').style.fontSize = `${fontScale * 100}%`;
  });
  $('[data-action="font-decrease"]')?.addEventListener('click', () => {
    fontScale = Math.max(fontScale - 0.1, 0.85);
    $('#transparency-root').style.fontSize = `${fontScale * 100}%`;
  });
  $('[data-action="font-reset"]')?.addEventListener('click', () => {
    fontScale = 1.0;
    $('#transparency-root').style.fontSize = '100%';
  });
  $('[data-action="portal-theme"]')?.addEventListener('click', () => {
    theme = theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('rio-theme', theme);
    renderTransparencyPortal();
  });

  // Load the current tab content
  loadPortalTabContent(currentPortalTab);
}

function getTabLabel(tab) {
  const labels = {
    geral: 'Visão Geral',
    despesas: 'Despesas Públicas',
    receitas: 'Arrecadação e Receitas',
    pagamentos: 'Ordem Cronológica de Pagamentos',
    diarias: 'Diárias, Passagens e Adiantamentos',
    licitacoes: 'Licitações e Atas de Registro de Preços',
    contratos: 'Contratos Administrativos',
    pessoal: 'Quadro de Pessoal e Folha de Pagamento',
    concursos: 'Concursos Públicos e Vagas',
    patrimonio: 'Bens Patrimoniais, Estoque e Frotas',
    divida_ativa: 'Devedores Inscritos em Dívida Ativa',
    emendas: 'Emendas Parlamentares Impositivas',
    covid: 'Painel COVID-19 & Calamidade Pública',
    sic: 'Serviço de Informações ao Cidadão (e-SIC)',
    faq: 'Perguntas Frequentes (FAQ)'
  };
  return labels[tab] || 'Consulta';
}

function switchPortalTab(tab) {
  currentPortalTab = tab;
  location.hash = `#/${tab}`;
  $$('.transp-tab').forEach(b => {
    b.classList.toggle('active', b.getAttribute('data-tab') === tab);
  });
  const lbl = $('#breadcrumb-current-label');
  if (lbl) lbl.textContent = getTabLabel(tab);
  loadPortalTabContent(tab);
}

async function loadPortalTabContent(tab) {
  const container = $('#transparency-content');
  if (!container) return;

  if (tab === 'geral') {
    await renderOverview(container);
  } else if (tab === 'despesas') {
    await renderExpensesTab(container);
  } else if (tab === 'receitas') {
    await renderRevenuesTab(container);
  } else if (tab === 'pagamentos') {
    await renderChronologicalPaymentsTab(container);
  } else if (tab === 'diarias') {
    await renderTravelsTab(container);
  } else if (tab === 'licitacoes') {
    await renderProcurementTab(container);
  } else if (tab === 'contratos') {
    await renderContractsTab(container);
  } else if (tab === 'pessoal') {
    await renderPersonnelTab(container);
  } else if (tab === 'concursos') {
    await renderCompetitionsTab(container);
  } else if (tab === 'patrimonio') {
    await renderAssetsTab(container);
  } else if (tab === 'divida_ativa') {
    await renderActiveDebtTab(container);
  } else if (tab === 'emendas') {
    await renderAmendmentsTab(container);
  } else if (tab === 'covid') {
    await renderCovidTab(container);
  } else if (tab === 'sic') {
    await renderSicTab(container);
  } else if (tab === 'faq') {
    await renderFaqTab(container);
  }
}

// ----------------------------------------------------------------------------
// 1. VISÃO GERAL
// ----------------------------------------------------------------------------
async function renderOverview(container) {
  const summary = await api('/public/transparency/summary');
  const k = summary.kpis;

  container.innerHTML = `
    <div class="kpi-row">
      <div class="kpi-card">
        <h4>Receita Total Prevista</h4>
        <div class="val">${money(k.total_revenue)}</div>
        <small>Arrecadação municipal acumulada</small>
      </div>
      <div class="kpi-card">
        <h4>Despesa Total Empenhada</h4>
        <div class="val">${money(k.total_expense)}</div>
        <small>Execução orçamentária vigente</small>
      </div>
      <div class="kpi-card">
        <h4>Contratos Vigentes</h4>
        <div class="val">${k.total_contracts}</div>
        <small>Contratos administrativos ativos</small>
      </div>
      <div class="kpi-card">
        <h4>Processos Licitatórios</h4>
        <div class="val">${k.total_processes}</div>
        <small>Dispensas e licitações Lei 14.133</small>
      </div>
    </div>

    <div class="consultation-meta">
      <div class="update-stamp">
        ${icon('clock')} Última atualização do Portal: <strong>${summary.last_update}</strong>
      </div>
      <div class="consultation-actions">
        <button class="button small" onclick="window.print()">${icon('print')} Imprimir Resumo</button>
      </div>
    </div>

    <section class="panel" style="margin-bottom:24px">
      <div class="panel-head">
        <h2>${icon('grid')} Consultas Rápidas da Gestão Pública</h2>
      </div>
      <div class="panel-body">
        <p class="muted" style="margin-bottom:20px">Selecione uma área para consultar relatórios analíticos, gráficos e detalhes completos:</p>
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(260px, 1fr));gap:16px;">
          <a href="#/despesas" class="card" data-tab="despesas" style="text-decoration:none;padding:16px;border:1px solid var(--line);border-radius:8px;background:var(--panel);">
            <strong style="color:var(--accent);display:flex;align-items:center;gap:8px;">${icon('wallet')} Despesas Orçamentárias</strong>
            <small style="color:var(--muted);display:block;margin-top:6px;">Empenhos, liquidações, pagamentos e restos a pagar.</small>
          </a>
          <a href="#/receitas" class="card" data-tab="receitas" style="text-decoration:none;padding:16px;border:1px solid var(--line);border-radius:8px;background:var(--panel);">
            <strong style="color:var(--accent);display:flex;align-items:center;gap:8px;">${icon('wallet')} Receitas e Arrecadação</strong>
            <small style="color:var(--muted);display:block;margin-top:6px;">Previsão, arrecadação diária e transferências constitucionais.</small>
          </a>
          <a href="#/licitacoes" class="card" data-tab="licitacoes" style="text-decoration:none;padding:16px;border:1px solid var(--line);border-radius:8px;background:var(--panel);">
            <strong style="color:var(--accent);display:flex;align-items:center;gap:8px;">${icon('file')} Licitações e Atas SRP</strong>
            <small style="color:var(--muted);display:block;margin-top:6px;">Pregões, concorrências, dispensas e vencedores adjudicados.</small>
          </a>
          <a href="#/pessoal" class="card" data-tab="pessoal" style="text-decoration:none;padding:16px;border:1px solid var(--line);border-radius:8px;background:var(--panel);">
            <strong style="color:var(--accent);display:flex;align-items:center;gap:8px;">${icon('users')} Servidores e Folha</strong>
            <small style="color:var(--muted);display:block;margin-top:6px;">Quadro funcional, remunerações, cargos e vencimentos.</small>
          </a>
          <a href="#/divida_ativa" class="card" data-tab="divida_ativa" style="text-decoration:none;padding:16px;border:1px solid var(--line);border-radius:8px;background:var(--panel);">
            <strong style="color:var(--accent);display:flex;align-items:center;gap:8px;">${icon('wallet')} Dívida Ativa Municipal</strong>
            <small style="color:var(--muted);display:block;margin-top:6px;">Devedores inscritos na Fazenda Pública e certidões CDA.</small>
          </a>
          <a href="#/emendas" class="card" data-tab="emendas" style="text-decoration:none;padding:16px;border:1px solid var(--line);border-radius:8px;background:var(--panel);">
            <strong style="color:var(--accent);display:flex;align-items:center;gap:8px;">${icon('wallet')} Emendas Parlamentares</strong>
            <small style="color:var(--muted);display:block;margin-top:6px;">Execução financeira de emendas federais, estaduais e municipais.</small>
          </a>
        </div>
      </div>
    </section>
  `;

  container.querySelectorAll('[data-tab]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      switchPortalTab(btn.getAttribute('data-tab'));
    });
  });
}

// ----------------------------------------------------------------------------
// 2. DESPESAS PÚBLICAS (Drilldown até o empenho)
// ----------------------------------------------------------------------------
async function renderExpensesTab(container) {
  const res = await api('/public/transparency/expenses');
  const items = res.items;

  container.innerHTML = `
    ${renderConsultationMeta(res.last_update, 'expenses')}
    <div class="transparency-explanation">${esc(res.summary_text)}</div>

    <section class="panel">
      <div class="toolbar">
        <div class="input-search">
          ${icon('search')}
          <input id="expense-search" placeholder="Buscar por número do empenho, credor, unidade ou processo…" oninput="filterExpensesTable()">
        </div>
        <select id="expense-type-filter" class="control" onchange="filterExpensesTable()">
          <option value="">Todos os tipos</option>
          <option value="Orçamentário">Orçamentário</option>
          <option value="Restos a Pagar">Restos a Pagar</option>
        </select>
        <span class="count" id="expense-count">${items.length} empenhos</span>
      </div>

      <div class="table-wrap">
        <table id="expenses-table">
          <thead>
            <tr>
              <th>EMPENHO / DATA</th>
              <th>UNIDADE GESTORA</th>
              <th>CREDOR</th>
              <th>TIPO</th>
              <th style="text-align:right">EMPENHADO</th>
              <th style="text-align:right">LIQUIDADO</th>
              <th style="text-align:right">PAGO</th>
              <th style="text-align:center">AÇÕES</th>
            </tr>
          </thead>
          <tbody>
            ${items.map(r => `
              <tr data-search="${esc((r.empenho_number + ' ' + r.credor + ' ' + r.managing_unit + ' ' + r.process_number).toLowerCase())}" data-type="${esc(r.expense_type)}">
                <td>
                  <strong>${esc(r.empenho_number)}</strong>
                  <small>${date(r.emission_date)}</small>
                </td>
                <td>${esc(r.managing_unit)}</td>
                <td>
                  <strong>${esc(r.credor)}</strong>
                  <small>${esc(r.credor_document)}</small>
                </td>
                <td><span class="badge ${r.expense_type==='Restos a Pagar'?'warning':'info'}">${esc(r.expense_type)}</span></td>
                <td style="text-align:right" class="mono">${money(r.committed_amount)}</td>
                <td style="text-align:right" class="mono">${money(r.liquidated_amount)}</td>
                <td style="text-align:right" class="mono"><strong>${money(r.paid_amount)}</strong></td>
                <td style="text-align:center">
                  <button class="button small" onclick="openExpenseDrilldown(${r.id})">${icon('eye')} Detalhar</button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function filterExpensesTable() {
  const q = ($('#expense-search')?.value || '').toLowerCase();
  const type = $('#expense-type-filter')?.value || '';
  let count = 0;
  $$('#expenses-table tbody tr').forEach(tr => {
    const s = tr.getAttribute('data-search') || '';
    const t = tr.getAttribute('data-type') || '';
    const match = (!q || s.includes(q)) && (!type || t === type);
    tr.style.display = match ? '' : 'none';
    if (match) count++;
  });
  const cntEl = $('#expense-count');
  if (cntEl) cntEl.textContent = `${count} empenhos`;
}

async function openExpenseDrilldown(id) {
  const exp = await api(`/public/transparency/expenses/${id}`);
  const content = `
    <div class="drilldown-modal-content">
      <div class="data-field-grid">
        <div class="data-field-box">
          <label>Número do Empenho</label>
          <span>${esc(exp.empenho_number)}</span>
        </div>
        <div class="data-field-box">
          <label>Data de Emissão</label>
          <span>${date(exp.emission_date)}</span>
        </div>
        <div class="data-field-box">
          <label>Unidade Gestora</label>
          <span>${esc(exp.managing_unit)}</span>
        </div>
        <div class="data-field-box">
          <label>Credor / Fornecedor</label>
          <span>${esc(exp.creditor)} (${esc(exp.creditor_document)})</span>
        </div>
        <div class="data-field-box">
          <label>Funcional Programática</label>
          <span>${esc(exp.functional)}</span>
        </div>
        <div class="data-field-box">
          <label>Natureza da Despesa</label>
          <span>${esc(exp.economic_category)}</span>
        </div>
        <div class="data-field-box">
          <label>Fonte de Recursos</label>
          <span>${esc(exp.resource_source)}</span>
        </div>
        <div class="data-field-box">
          <label>Processo Licitatório Vinculado</label>
          <span><a href="#/licitacoes" style="color:var(--accent)">${esc(exp.process_number)} ${icon('external')}</a></span>
        </div>
      </div>

      <h3 style="margin:20px 0 10px;font-size:14px">Itens do Empenho</h3>
      <table style="width:100%;margin-bottom:20px">
        <thead>
          <tr>
            <th>ITEM</th>
            <th>DESCRIÇÃO</th>
            <th style="text-align:right">QUANTIDADE</th>
            <th style="text-align:right">UNITÁRIO</th>
            <th style="text-align:right">TOTAL</th>
          </tr>
        </thead>
        <tbody>
          ${exp.items.map(it => `
            <tr>
              <td>${it.item}</td>
              <td>${esc(it.description)}</td>
              <td style="text-align:right">${it.quantity} ${esc(it.unit)}</td>
              <td style="text-align:right">${money(it.unit_value)}</td>
              <td style="text-align:right"><strong>${money(it.total_value)}</strong></td>
            </tr>
          `).join('')}
        </tbody>
      </table>

      <h3 style="margin:20px 0 10px;font-size:14px">Histórico de Liquidações e Pagamentos</h3>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
        <div class="panel" style="padding:12px">
          <strong>Liquidações Realizadas</strong>
          ${exp.liquidations.map(l => `
            <div style="font-size:12px;margin-top:8px;padding-top:6px;border-top:1px solid var(--line)">
              Liquidação nº ${l.number} em ${date(l.date)}: <strong>${money(l.amount)}</strong>
              <div style="font-size:11px;color:var(--muted)">${esc(l.historic)}</div>
            </div>
          `).join('')}
        </div>
        <div class="panel" style="padding:12px">
          <strong>Pagamentos Efetuados</strong>
          ${exp.payments.map(p => `
            <div style="font-size:12px;margin-top:8px;padding-top:6px;border-top:1px solid var(--line)">
              Ordem de Pagamento nº ${p.number} em ${date(p.date)}: <strong>${money(p.amount)}</strong>
              <div style="font-size:11px;color:var(--muted)">${esc(p.historic)}</div>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;
  openModal(`Detalhes do Empenho ${exp.empenho_number}`, content, 'Demonstrativo oficial de execução da despesa');
}

// ----------------------------------------------------------------------------
// 3. RECEITAS PÚBLICAS
// ----------------------------------------------------------------------------
async function renderRevenuesTab(container) {
  const res = await api('/public/transparency/revenues');
  const items = res.items;

  container.innerHTML = `
    ${renderConsultationMeta(res.last_update, 'revenues')}
    <div class="transparency-explanation">${esc(res.summary_text)}</div>

    <section class="panel">
      <div class="toolbar">
        <div class="input-search">
          ${icon('search')}
          <input id="revenue-search" placeholder="Buscar receita por descrição, código ou categoria…" oninput="filterRevenuesTable()">
        </div>
        <span class="count" id="revenue-count">${items.length} receitas</span>
      </div>

      <div class="table-wrap">
        <table id="revenues-table">
          <thead>
            <tr>
              <th>CÓDIGO / NATUREZA</th>
              <th>CATEGORIA ECONÔMICA</th>
              <th>DATA REPASSE</th>
              <th style="text-align:right">PREVISÃO LÍQUIDA</th>
              <th style="text-align:right">ARRECADAÇÃO BRUTA</th>
              <th style="text-align:right">ARRECADAÇÃO LÍQUIDA</th>
            </tr>
          </thead>
          <tbody>
            ${items.map(r => `
              <tr data-search="${esc((r.nature_code + ' ' + r.title + ' ' + r.economic_category).toLowerCase())}">
                <td>
                  <strong>${esc(r.title)}</strong>
                  <small>${esc(r.nature_code)} · ${esc(r.source)}</small>
                </td>
                <td>${esc(r.economic_category)}</td>
                <td>${date(r.transfer_date)}</td>
                <td style="text-align:right" class="mono">${money(r.updated_net_forecast)}</td>
                <td style="text-align:right" class="mono">${money(r.gross_collected)}</td>
                <td style="text-align:right" class="mono"><strong>${money(r.net_collected)}</strong></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function filterRevenuesTable() {
  const q = ($('#revenue-search')?.value || '').toLowerCase();
  let count = 0;
  $$('#revenues-table tbody tr').forEach(tr => {
    const s = tr.getAttribute('data-search') || '';
    const match = !q || s.includes(q);
    tr.style.display = match ? '' : 'none';
    if (match) count++;
  });
  const cntEl = $('#revenue-count');
  if (cntEl) cntEl.textContent = `${count} receitas`;
}

// ----------------------------------------------------------------------------
// 4. ORDEM CRONOLÓGICA DE PAGAMENTOS (transparency.35, 117, 118)
// ----------------------------------------------------------------------------
async function renderChronologicalPaymentsTab(container) {
  const res = await api('/public/transparency/chronological-payments');
  const items = res.items;

  container.innerHTML = `
    ${renderConsultationMeta(res.last_update, 'expenses')}
    <div class="transparency-explanation">
      Ordem cronológica de exigibilidade para pagamento de obrigações da Administração Municipal, em conformidade com o Art. 141 da Lei nº 14.133/2021.
    </div>

    <section class="panel">
      <div class="toolbar">
        <div class="input-search">
          ${icon('search')}
          <input id="payment-search" placeholder="Buscar credor, documento ou empenho…" oninput="filterPaymentsTable()">
        </div>
        <span class="count">${items.length} registros</span>
      </div>

      <div class="table-wrap">
        <table id="payments-table">
          <thead>
            <tr>
              ${res.show_order ? '<th style="text-align:center">ORDEM</th>' : ''}
              <th>EMPENHO</th>
              <th>CREDOR</th>
              <th>FONTE</th>
              <th>LIQUIDAÇÃO</th>
              <th style="text-align:right">VALOR</th>
              <th>SITUAÇÃO</th>
              ${res.show_justification ? '<th>JUSTIFICATIVA</th>' : ''}
            </tr>
          </thead>
          <tbody>
            ${items.map(p => `
              <tr data-search="${esc((p.credor + ' ' + p.empenho_number + ' ' + p.credor_document).toLowerCase())}">
                ${res.show_order ? `<td style="text-align:center"><strong>#${p.order_number}</strong></td>` : ''}
                <td>
                  <strong>${esc(p.empenho_number)}</strong>
                  <small>${esc(p.process_number)}</small>
                </td>
                <td>
                  <strong>${esc(p.credor)}</strong>
                  <small>${esc(p.credor_document)}</small>
                </td>
                <td><small>${esc(p.source)}</small></td>
                <td>${date(p.liquidation_date)}</td>
                <td style="text-align:right" class="mono"><strong>${money(p.amount)}</strong></td>
                <td><span class="badge ${p.status==='Pago'?'success':'info'}">${esc(p.status)}</span></td>
                ${res.show_justification ? `<td><small class="muted">${esc(p.justification)}</small></td>` : ''}
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function filterPaymentsTable() {
  const q = ($('#payment-search')?.value || '').toLowerCase();
  $$('#payments-table tbody tr').forEach(tr => {
    const s = tr.getAttribute('data-search') || '';
    tr.style.display = !q || s.includes(q) ? '' : 'none';
  });
}

// ----------------------------------------------------------------------------
// 5. DIÁRIAS E VIAGENS (transparency.24, 135, 137)
// ----------------------------------------------------------------------------
async function renderTravelsTab(container) {
  const res = await api('/public/transparency/travels');
  const items = res.items;

  container.innerHTML = `
    ${renderConsultationMeta(res.last_update, 'travels')}
    <div class="transparency-explanation">
      Relação das concessões de diárias, passagens e adiantamentos de viagens efetuadas a servidores municipais, com especificação de transporte e objetivos de serviço.
    </div>

    <section class="panel">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>BENEFICIÁRIO / CARGO</th>
              <th>DESTINO / PERÍODO</th>
              <th>TRANSPORTE / CUSTO</th>
              <th>OBJETIVO</th>
              <th style="text-align:right">DIÁRIAS / TOTAL</th>
            </tr>
          </thead>
          <tbody>
            ${items.map(t => `
              <tr>
                <td>
                  <strong>${esc(t.employee_name)}</strong>
                  <small>${esc(t.role)} · ${esc(t.registration)} · ${esc(t.department)}</small>
                </td>
                <td>
                  <strong>${esc(t.destination)}</strong>
                  <small>${date(t.start_date)} a ${date(t.end_date)}</small>
                </td>
                <td>
                  <span class="badge info">${esc(t.transport_type)}</span>
                  <small>Custo: ${money(t.transport_cost)}</small>
                </td>
                <td><small>${esc(t.objective)}</small></td>
                <td style="text-align:right" class="mono">
                  ${t.daily_allowance_qty} diária(s)
                  <strong style="display:block">${money(t.total_amount)}</strong>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

// ----------------------------------------------------------------------------
// 6. LICITAÇÕES E ATAS SRP (Lei 14.133/2021)
// ----------------------------------------------------------------------------
async function renderProcurementTab(container) {
  const res = await api('/public/transparency/procurement');
  const items = res.items;

  container.innerHTML = `
    ${renderConsultationMeta(res.last_update, 'procurement')}
    <div class="transparency-explanation">
      Processos de contratações públicas regidos pela Lei nº 14.133/2021, incluindo dispensas, inexigibilidades, pregões, concorrências e Atas de Registro de Preços (SRP).
    </div>

    <section class="panel">
      <div class="toolbar">
        <div class="input-search">
          ${icon('search')}
          <input id="lic-search" placeholder="Buscar por objeto, número, modalidade ou fornecedor…" oninput="filterLicTable()">
        </div>
        <select id="lic-srp-filter" class="control" onchange="filterLicTable()">
          <option value="">Todas as compras</option>
          <option value="srp">Apenas Registro de Preços (SRP)</option>
        </select>
        <span class="count">${items.length} processos</span>
      </div>

      <div class="table-wrap">
        <table id="lic-table">
          <thead>
            <tr>
              <th>PROCESSO / MODALIDADE</th>
              <th>OBJETO DA CONTRATAÇÃO</th>
              <th>SECRETARIA</th>
              <th>FUNDAMENTAÇÃO LEGAL</th>
              <th>VENCEDORES HOMOLOGADOS</th>
              <th style="text-align:right">VALOR</th>
              <th>SITUAÇÃO</th>
            </tr>
          </thead>
          <tbody>
            ${items.map(p => `
              <tr data-search="${esc((p.process_number + ' ' + p.title + ' ' + p.object + ' ' + p.modality + ' ' + (p.winners[0]?.supplier_name||'')).toLowerCase())}" data-srp="${p.is_srp ? '1' : '0'}">
                <td>
                  <strong>${esc(p.process_number)}</strong>
                  <small>${esc(p.modality)} ${p.is_srp ? '<span class="badge info">SRP</span>' : ''}</small>
                  <small class="muted">${esc(p.administrative_process)}</small>
                </td>
                <td>
                  <strong>${esc(p.title)}</strong>
                  <small>${esc(p.object)}</small>
                </td>
                <td>${esc(p.department)}</td>
                <td><small>${esc(p.legal_basis)}</small></td>
                <td>
                  ${p.winners.length ? p.winners.map(w => `
                    <div style="font-size:11px">
                      <strong>${esc(w.supplier_name)}</strong>
                      <small class="muted">${esc(w.supplier_document)}</small>
                    </div>
                  `).join('') : '<small class="muted">Em andamento</small>'}
                </td>
                <td style="text-align:right" class="mono"><strong>${money(p.homologated_value || p.estimated_value)}</strong></td>
                <td><span class="badge ${p.status==='Homologado'?'success':'info'}">${esc(p.status)}</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function filterLicTable() {
  const q = ($('#lic-search')?.value || '').toLowerCase();
  const srpOnly = $('#lic-srp-filter')?.value === 'srp';
  $$('#lic-table tbody tr').forEach(tr => {
    const s = tr.getAttribute('data-search') || '';
    const isSrp = tr.getAttribute('data-srp') === '1';
    const match = (!q || s.includes(q)) && (!srpOnly || isSrp);
    tr.style.display = match ? '' : 'none';
  });
}

// ----------------------------------------------------------------------------
// 7. CONTRATOS ADMINISTRATIVOS (transparency.102, 106, 136)
// ----------------------------------------------------------------------------
async function renderContractsTab(container) {
  const res = await api('/public/transparency/contracts');
  const items = res.items;

  container.innerHTML = `
    ${renderConsultationMeta(res.last_update, 'contracts')}
    <div class="transparency-explanation">
      Contratos administrativos celebrados pela Prefeitura Municipal de Rio das Ostras, com histórico de aditivos, vigência e reajustes.
    </div>

    <section class="panel">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>NÚMERO / PROCESSO</th>
              <th>FORNECEDOR CONTRATADO</th>
              <th>OBJETO</th>
              <th>VIGÊNCIA</th>
              <th>ADITIVOS</th>
              <th style="text-align:right">VALOR ATUAL</th>
              <th>SITUAÇÃO</th>
            </tr>
          </thead>
          <tbody>
            ${items.map(c => `
              <tr>
                <td>
                  <strong>${esc(c.contract_number)}</strong>
                  <small>${esc(c.administrative_process)}</small>
                </td>
                <td>
                  <strong>${esc(c.supplier_name)}</strong>
                  <small>${esc(c.supplier_document)}</small>
                </td>
                <td><small>${esc(c.object)}</small></td>
                <td><small>${date(c.start_date)} a ${date(c.end_date)}</small></td>
                <td>
                  ${c.amendments.length ? `
                    <span class="badge warning">${c.amendments.length} aditivo(s)</span>
                  ` : '<span class="muted" style="font-size:11px">Sem aditivos</span>'}
                </td>
                <td style="text-align:right" class="mono"><strong>${money(c.current_value)}</strong></td>
                <td><span class="badge success">${esc(c.status)}</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

// ----------------------------------------------------------------------------
// 8. PESSOAL E REMUNERAÇÃO (transparency.45 a 59)
// ----------------------------------------------------------------------------
async function renderPersonnelTab(container) {
  const res = await api('/public/transparency/personnel');
  const items = res.items;

  container.innerHTML = `
    ${renderConsultationMeta(res.last_update, 'personnel')}
    <div class="transparency-explanation">
      Quadro de servidores municipais ativos e inativos, com remunerações, cargos, lotação e folha analítica transparente.
    </div>

    <section class="panel">
      <div class="toolbar">
        <div class="input-search">
          ${icon('search')}
          <input id="staff-search" placeholder="Buscar por servidor, cargo ou secretaria…" oninput="filterStaffTable()">
        </div>
        <select id="staff-bond-filter" class="control" onchange="filterStaffTable()">
          <option value="">Todos os vínculos</option>
          <option value="Efetivo">Efetivo</option>
          <option value="Comissionado">Comissionado</option>
          <option value="Temporário">Temporário</option>
          <option value="Estagiário">Estagiário</option>
          <option value="Inativo">Inativo</option>
        </select>
        <span class="count">${items.length} servidores</span>
      </div>

      <div class="table-wrap">
        <table id="staff-table">
          <thead>
            <tr>
              <th>SERVIDOR / MATRÍCULA</th>
              <th>CARGO / LOTAÇÃO</th>
              <th>VÍNCULO</th>
              <th style="text-align:right">SALÁRIO BASE</th>
              <th style="text-align:right">BRUTO</th>
              <th style="text-align:right">DESCONTOS</th>
              <th style="text-align:right">LÍQUIDO</th>
            </tr>
          </thead>
          <tbody>
            ${items.map(s => `
              <tr data-search="${esc((s.name + ' ' + s.role + ' ' + s.department).toLowerCase())}" data-bond="${esc(s.bond_type)}">
                <td>
                  <strong>${esc(s.name)}</strong>
                  <small>${esc(s.registration)} · CPF: ${esc(s.cpf_masked)}</small>
                </td>
                <td>
                  <strong>${esc(s.role)}</strong>
                  <small>${esc(s.department)}</small>
                </td>
                <td><span class="badge info">${esc(s.bond_type)}</span></td>
                <td style="text-align:right" class="mono">${money(s.base_salary)}</td>
                <td style="text-align:right" class="mono">${money(s.gross_salary)}</td>
                <td style="text-align:right" class="mono" style="color:#dc2626">${money(s.discounts)}</td>
                <td style="text-align:right" class="mono"><strong>${money(s.net_salary)}</strong></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function filterStaffTable() {
  const q = ($('#staff-search')?.value || '').toLowerCase();
  const bond = $('#staff-bond-filter')?.value || '';
  $$('#staff-table tbody tr').forEach(tr => {
    const s = tr.getAttribute('data-search') || '';
    const b = tr.getAttribute('data-bond') || '';
    const match = (!q || s.includes(q)) && (!bond || b === bond);
    tr.style.display = match ? '' : 'none';
  });
}

// ----------------------------------------------------------------------------
// 9. CONCURSOS PÚBLICOS E VAGAS (transparency.60 a 64)
// ----------------------------------------------------------------------------
async function renderCompetitionsTab(container) {
  const res = await api('/public/transparency/competitions');
  const items = res.items;

  container.innerHTML = `
    ${renderConsultationMeta(res.last_update, 'competitions')}
    <div class="transparency-explanation">
      Concursos públicos e processos seletivos simplificados do Município, com acompanhamento de editais, homologações e quantitativo de vagas preenchidas e disponíveis.
    </div>

    <section class="panel">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>EDITAL / TIPO</th>
              <th>ÓRGÃO DESTINATÁRIO</th>
              <th>PUBLICAÇÃO / HOMOLOGAÇÃO</th>
              <th style="text-align:center">VAGAS CRIADAS</th>
              <th style="text-align:center">PREENCHIDAS</th>
              <th style="text-align:center">DISPONÍVEIS</th>
              <th>SITUAÇÃO</th>
            </tr>
          </thead>
          <tbody>
            ${items.map(c => `
              <tr>
                <td>
                  <strong>${esc(c.competition_type)} nº ${esc(c.number_year)}</strong>
                  <small>${esc(c.edict_law)}</small>
                </td>
                <td>${esc(c.department)}</td>
                <td>
                  Publicado em: ${date(c.publication_date)}
                  ${c.homologation_date ? `<small>Homologado: ${date(c.homologation_date)}</small>` : ''}
                </td>
                <td style="text-align:center"><strong>${c.vacancies_created}</strong></td>
                <td style="text-align:center"><span class="badge success">${c.vacancies_filled}</span></td>
                <td style="text-align:center"><span class="badge warning">${c.vacancies_available}</span></td>
                <td><span class="badge ${c.status==='Homologado'?'success':c.status==='Em andamento'?'info':'muted'}">${esc(c.status)}</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

// ----------------------------------------------------------------------------
// 10. PATRIMÔNIO, ESTOQUE E FROTAS (transparency.80 a 88, 132, 133, 134)
// ----------------------------------------------------------------------------
async function renderAssetsTab(container) {
  const [assetsRes, invRes, fleetRes] = await Promise.all([
    api('/public/transparency/assets'),
    api('/public/transparency/inventory'),
    api('/public/transparency/fleet')
  ]);

  container.innerHTML = `
    ${renderConsultationMeta(assetsRes.last_update, 'assets')}
    <div class="transparency-explanation">
      Gestão integrada de bens patrimoniais municipais (tombamento e anexos), estoque de almoxarifado com fornecedores e frotas públicas.
    </div>

    <section class="panel" style="margin-bottom:24px">
      <div class="panel-head">
        <h2>${icon('database')} Bens Patrimoniais Tombados (com fotos e anexos)</h2>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>CÓDIGO / PLACA</th>
              <th>DESCRIÇÃO DO BEM</th>
              <th>UNIDADE GESTORA</th>
              <th>FORNECEDOR / NF</th>
              <th style="text-align:right">VALOR AQUISIÇÃO</th>
              <th style="text-align:right">VALOR ATUAL</th>
              <th>SITUAÇÃO</th>
            </tr>
          </thead>
          <tbody>
            ${assetsRes.items.map(a => `
              <tr>
                <td>
                  <strong>${esc(a.asset_code)}</strong>
                  <small>${esc(a.plate_number)}</small>
                </td>
                <td>
                  <strong>${esc(a.description)}</strong>
                  <small>Série: ${esc(a.serial_number)} · Ingresso: ${esc(a.entry_type)}</small>
                </td>
                <td>${esc(a.managing_unit)}</td>
                <td>
                  <strong>${esc(a.supplier_name)}</strong>
                  <small>${esc(a.invoice_number)} · Proc: ${esc(a.bidding_process)}</small>
                </td>
                <td style="text-align:right" class="mono">${money(a.acquisition_value)}</td>
                <td style="text-align:right" class="mono"><strong>${money(a.current_value)}</strong></td>
                <td><span class="badge success">${esc(a.status)}</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </section>

    <section class="panel" style="margin-bottom:24px">
      <div class="panel-head">
        <h2>${icon('database')} Almoxarifado Central (com indicação do Fornecedor)</h2>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>CÓDIGO</th>
              <th>MATERIAL</th>
              <th>FORNECEDOR VINCULADO</th>
              <th>UNIDADE</th>
              <th style="text-align:center">SALDO ANTERIOR</th>
              <th style="text-align:center">ENTRADAS / SAÍDAS</th>
              <th style="text-align:center">SALDO ATUAL</th>
            </tr>
          </thead>
          <tbody>
            ${invRes.items.map(it => `
              <tr>
                <td><strong>${esc(it.item_code)}</strong></td>
                <td>${esc(it.description)}</td>
                <td>
                  <strong>${esc(it.supplier_name)}</strong>
                  <small class="muted">${esc(it.supplier_document)}</small>
                </td>
                <td>${esc(it.unit)}</td>
                <td style="text-align:center">${it.previous_balance}</td>
                <td style="text-align:center">+${it.entries} / -${it.exits}</td>
                <td style="text-align:center"><strong>${it.current_balance}</strong></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <h2>${icon('car')} Veículos Oficiais da Frota Municipal</h2>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>PLACA / VEÍCULO</th>
              <th>SECRETARIA</th>
              <th>COMBUSTÍVEL</th>
              <th>RENAVAM</th>
              <th>SITUAÇÃO</th>
            </tr>
          </thead>
          <tbody>
            ${fleetRes.items.map(v => `
              <tr>
                <td>
                  <strong>${esc(v.plate)}</strong>
                  <small>${esc(v.description)} (${v.year})</small>
                </td>
                <td>${esc(v.department)}</td>
                <td><span class="badge info">${esc(v.fuel_type)}</span></td>
                <td>${esc(v.renavam)}</td>
                <td><span class="badge success">${esc(v.status)}</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

// ----------------------------------------------------------------------------
// 11. DÍVIDA ATIVA MUNICIPAL (transparency.146)
// ----------------------------------------------------------------------------
async function renderActiveDebtTab(container) {
  const res = await api('/public/transparency/active-debt');
  const items = res.items;

  container.innerHTML = `
    ${renderConsultationMeta(res.last_update, 'active-debt')}
    <div class="transparency-explanation">
      Relação de devedores inscritos em Dívida Ativa junto à Fazenda Pública Municipal de Rio das Ostras, em cumprimento à transparência fiscal ativa e publicidade das contas.
    </div>

    <section class="panel">
      <div class="toolbar">
        <div class="input-search">
          ${icon('search')}
          <input id="debt-search" placeholder="Buscar por devedor, CPF/CNPJ, CDA ou processo…" oninput="filterDebtTable()">
        </div>
        <span class="count">${items.length} inscrições</span>
      </div>

      <div class="table-wrap">
        <table id="debt-table">
          <thead>
            <tr>
              <th>DEVEDOR / DOCUMENTO</th>
              <th>INSCRIÇÃO / CDA</th>
              <th>NATUREZA DA DÍVIDA</th>
              <th>EXERCÍCIO</th>
              <th style="text-align:right">VALOR ORIGINÁRIO</th>
              <th style="text-align:right">VALOR ATUALIZADO</th>
              <th>SITUAÇÃO</th>
            </tr>
          </thead>
          <tbody>
            ${items.map(d => `
              <tr data-search="${esc((d.debtor_name + ' ' + d.document + ' ' + d.cda_number).toLowerCase())}">
                <td>
                  <strong>${esc(d.debtor_name)}</strong>
                  <small>Documento: ${esc(d.document)}</small>
                </td>
                <td>
                  <strong>${esc(d.cda_number)}</strong>
                  <small>${esc(d.municipal_registration)} · ${esc(d.process_number)}</small>
                </td>
                <td>${esc(d.debt_nature)}</td>
                <td>${d.fiscal_year}</td>
                <td style="text-align:right" class="mono">${money(d.original_amount)}</td>
                <td style="text-align:right" class="mono"><strong>${money(d.updated_amount)}</strong></td>
                <td><span class="badge ${d.status==='Ajuizado'?'danger':d.status==='Parcelado'?'warning':'info'}">${esc(d.status)}</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function filterDebtTable() {
  const q = ($('#debt-search')?.value || '').toLowerCase();
  $$('#debt-table tbody tr').forEach(tr => {
    const s = tr.getAttribute('data-search') || '';
    tr.style.display = !q || s.includes(q) ? '' : 'none';
  });
}

// ----------------------------------------------------------------------------
// 12. EMENDAS PARLAMENTARES IMPOSITIVAS (transparency.147)
// ----------------------------------------------------------------------------
async function renderAmendmentsTab(container) {
  const res = await api('/public/transparency/parliamentary-amendments');
  const items = res.items;

  container.innerHTML = `
    ${renderConsultationMeta(res.last_update, 'amendments')}
    <div class="transparency-explanation">
      Acompanhamento da execução orçamentária e financeira de Emendas Impositivas de Parlamentares Federais, Estaduais e Municipais destinadas a Rio das Ostras.
    </div>

    <section class="panel">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>PARLAMENTAR / ESFERA</th>
              <th>EMENDA / EXERCÍCIO</th>
              <th>OBJETO DESTINADO</th>
              <th>BENEFICIÁRIO</th>
              <th style="text-align:right">INDICADO</th>
              <th style="text-align:right">EMPENHADO / PAGO</th>
              <th>SITUAÇÃO</th>
            </tr>
          </thead>
          <tbody>
            ${items.map(a => `
              <tr>
                <td>
                  <strong>${esc(a.author)}</strong>
                  <small><span class="badge info">${esc(a.sphere)}</span> · ${esc(a.amendment_type)}</small>
                </td>
                <td>
                  <strong>${esc(a.amendment_number)}</strong>
                  <small>Exercício ${a.fiscal_year}</small>
                </td>
                <td><small>${esc(a.object)}</small></td>
                <td>${esc(a.beneficiary)}</td>
                <td style="text-align:right" class="mono">${money(a.indicated_amount)}</td>
                <td style="text-align:right" class="mono">
                  ${money(a.committed_amount)}
                  <strong style="display:block">${money(a.paid_amount)}</strong>
                </td>
                <td><span class="badge ${a.status==='Concluída'?'success':'info'}">${esc(a.status)}</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

// ----------------------------------------------------------------------------
// 13. PAINEL COVID-19 / CALAMIDADE PÚBLICA (transparency.108 a 125, 140)
// ----------------------------------------------------------------------------
async function renderCovidTab(container) {
  const res = await api('/public/transparency/covid');

  container.innerHTML = `
    ${renderConsultationMeta(res.last_update, 'expenses')}
    <div class="covid-highlight-banner" style="margin-top:0">
      <div>
        <h3>${icon('shield')} Painel Especial COVID-19 & Calamidade Pública</h3>
        <p>Demonstrativo consolidado de ações, contratos, aquisições e gastos no enfrentamento de emergências e calamidades públicas.</p>
      </div>
    </div>

    <section class="panel" style="margin-bottom:24px">
      <div class="panel-head">
        <h2>${icon('grid')} Temas e Publicações Oficiais (Ordem Alfabética)</h2>
      </div>
      <div class="panel-body">
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:12px;">
          ${res.themes.map(t => `
            <a href="${esc(t.link_url)}" class="card" style="padding:14px;border:1px solid var(--line);border-radius:6px;text-decoration:none;background:var(--panel);">
              <strong style="color:var(--ink);display:flex;align-items:center;gap:6px;">
                ${t.is_calamity ? icon('shield') : icon('file')} ${esc(t.theme_name)}
              </strong>
              <small style="color:var(--muted);display:block;margin-top:4px;">${esc(t.description)}</small>
            </a>
          `).join('')}
        </div>
      </div>
    </section>

    <section class="panel" style="margin-bottom:24px">
      <div class="panel-head">
        <h2>${icon('shield')} Contratos Emergenciais COVID-19</h2>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>CONTRATO</th>
              <th>FORNECEDOR</th>
              <th>OBJETO</th>
              <th style="text-align:right">VALOR CONTRATADO</th>
              <th>SITUAÇÃO</th>
            </tr>
          </thead>
          <tbody>
            ${res.contracts.length ? res.contracts.map(c => `
              <tr>
                <td><strong>${esc(c.contract_number)}</strong></td>
                <td>${esc(c.supplier_name)}</td>
                <td><small>${esc(c.object)}</small></td>
                <td style="text-align:right" class="mono"><strong>${money(c.current_value)}</strong></td>
                <td><span class="badge success">${esc(c.status)}</span></td>
              </tr>
            `).join('') : '<tr><td colspan="5" class="muted" style="text-align:center;padding:16px">Nenhum contrato emergencial ativo registrado no período.</td></tr>'}
          </tbody>
        </table>
      </div>
    </section>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
      <section class="panel">
        <div class="panel-head">
          <h2>Despesas Orçamentárias COVID-19</h2>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>EMPENHO</th>
                <th>CREDOR</th>
                <th style="text-align:right">PAGO</th>
              </tr>
            </thead>
            <tbody>
              ${res.expenses_budgetary.slice(0, 5).map(e => `
                <tr>
                  <td><strong>${esc(e.empenho_number)}</strong></td>
                  <td>${esc(e.credor)}</td>
                  <td style="text-align:right" class="mono">${money(e.paid_amount)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h2>Restos a Pagar COVID-19</h2>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>EMPENHO</th>
                <th>CREDOR</th>
                <th style="text-align:right">SALDO</th>
              </tr>
            </thead>
            <tbody>
              ${res.expenses_restos_a_pagar.slice(0, 5).map(e => `
                <tr>
                  <td><strong>${esc(e.empenho_number)}</strong></td>
                  <td>${esc(e.credor)}</td>
                  <td style="text-align:right" class="mono">${money(e.committed_amount)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  `;
}

// ----------------------------------------------------------------------------
// 14. e-SIC / OUVIDORIA (transparency.94, 95)
// ----------------------------------------------------------------------------
async function renderSicTab(container) {
  const res = await api('/public/transparency/sic');
  const info = res.info;

  container.innerHTML = `
    <div class="transparency-explanation">
      Serviço de Informações ao Cidadão (e-SIC) do Município de Rio das Ostras. Envie seu pedido de acesso à informação com base na Lei Federal nº 12.527/2011 ou consulte pedidos anteriores.
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:24px;">
      <section class="panel" style="padding:20px">
        <h2 style="font-size:16px;margin-bottom:14px">${icon('help')} Novo Pedido de Informação</h2>
        <form id="sic-form">
          <div class="form-grid">
            <div class="field" data-full>
              <label>Nome Completo *</label>
              <input name="requester_name" required minlength="3" placeholder="Seu nome completo">
            </div>
            <div class="field">
              <label>CPF / CNPJ *</label>
              <input name="requester_document" required placeholder="000.000.000-00">
            </div>
            <div class="field">
              <label>E-mail para resposta *</label>
              <input type="email" name="requester_email" required placeholder="seuemail@exemplo.com">
            </div>
            <div class="field" data-full>
              <label>Assunto do Pedido *</label>
              <input name="subject" required placeholder="Ex: Cópia de edital, relatório de despesa, etc.">
            </div>
            <div class="field" data-full>
              <label>Detalhamento da Informação Solicitada *</label>
              <textarea name="description" rows="4" required minlength="10" placeholder="Descreva de forma clara e detalhada as informações desejadas…"></textarea>
            </div>
          </div>
          <div style="margin-top:16px">
            <button type="submit" class="button primary">${icon('arrow')} Enviar Pedido e-SIC</button>
          </div>
        </form>
      </section>

      <section class="panel" style="padding:20px">
        <h2 style="font-size:16px;margin-bottom:14px">${icon('search')} Consultar Pedido por Protocolo</h2>
        <form id="sic-consult-form" style="display:flex;gap:10px;margin-bottom:20px;">
          <input id="sic-protocol-input" placeholder="Ex: SIC-2026/00001" required style="flex:1">
          <button type="submit" class="button">${icon('search')} Consultar</button>
        </form>
        <div id="sic-protocol-result"></div>

        <div style="margin-top:30px;padding-top:20px;border-top:1px solid var(--line);">
          <h3 style="font-size:13px;margin-bottom:8px">Atendimento Presencial</h3>
          <p style="font-size:12px;margin:0 0 4px"><strong>Local:</strong> ${esc(info.physical_location)}</p>
          <p style="font-size:12px;margin:0 0 4px"><strong>Responsável:</strong> ${esc(info.responsible)}</p>
          <p style="font-size:12px;margin:0 0 4px"><strong>Horário:</strong> ${esc(info.office_hours)}</p>
          <p style="font-size:12px;margin:0"><strong>Telefone:</strong> ${esc(info.phone)}</p>
        </div>
      </section>
    </div>
  `;

  $('#sic-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const payload = Object.fromEntries(fd.entries());
    try {
      const resp = await api('/public/transparency/sic', { method: 'POST', body: payload });
      openModal('Pedido Registrado com Sucesso!', `
        <div style="text-align:center;padding:20px">
          <div style="font-size:24px;font-weight:700;color:var(--accent);margin-bottom:8px">${esc(resp.protocol)}</div>
          <p>Seu pedido foi registrado no e-SIC. O prazo regulamentar de resposta é de até 20 dias (Art. 11 da Lei nº 12.527/2011).</p>
          <p class="muted" style="font-size:12px">Prazo limite para resposta: <strong>${date(resp.due_date)}</strong></p>
        </div>
      `, 'Protocolo de Acesso à Informação');
      e.target.reset();
    } catch (err) {
      alert(err.message);
    }
  });

  $('#sic-consult-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prot = $('#sic-protocol-input')?.value.trim();
    if (!prot) return;
    try {
      const item = await api(`/public/transparency/sic?protocol=${encodeURIComponent(prot)}`);
      $('#sic-protocol-result').innerHTML = `
        <div class="panel" style="padding:14px;background:var(--paper);border:1px solid var(--line);border-radius:6px">
          <div style="font-size:13px;font-weight:600;margin-bottom:4px">${esc(item.protocol)} · <span class="badge ${item.status==='Respondido'?'success':'info'}">${esc(item.status)}</span></div>
          <div style="font-size:12px;margin-bottom:8px"><strong>Assunto:</strong> ${esc(item.subject)}</div>
          <div style="font-size:11px;color:var(--muted)">Aberto em: ${date(item.opening_date)} | Prazo legal: ${date(item.due_date)}</div>
          ${item.response ? `
            <div style="margin-top:12px;padding-top:8px;border-top:1px solid var(--line);font-size:12px">
              <strong>Resposta do Órgão:</strong>
              <p style="margin-top:4px">${esc(item.response)}</p>
            </div>
          ` : '<p style="margin-top:10px;font-size:11px;color:var(--muted)">O pedido encontra-se em análise pelo setor competente.</p>'}
        </div>
      `;
    } catch (err) {
      $('#sic-protocol-result').innerHTML = `<p style="color:#dc2626;font-size:12px">${esc(err.message)}</p>`;
    }
  });
}

// ----------------------------------------------------------------------------
// 15. PERGUNTAS FREQUENTES (FAQ) (transparency.91)
// ----------------------------------------------------------------------------
async function renderFaqTab(container) {
  const res = await api('/public/transparency/faq');
  const items = res.items;

  container.innerHTML = `
    <div class="transparency-explanation">
      Respostas às perguntas frequentes que facilitam o entendimento sobre o funcionamento, a legislação e as consultas do Portal da Transparência.
    </div>

    <section class="panel">
      <div class="toolbar">
        <div class="input-search">
          ${icon('search')}
          <input id="faq-search" placeholder="Pesquisar nas perguntas frequentes…" oninput="filterFaq()">
        </div>
        <span class="count">${items.length} perguntas</span>
      </div>

      <div class="panel-body" id="faq-list">
        ${items.map(f => `
          <details class="faq-item" style="padding:12px 0;border-bottom:1px solid var(--line);" data-search="${esc((f.question + ' ' + f.answer).toLowerCase())}">
            <summary style="font-weight:600;font-size:14px;cursor:pointer;color:var(--ink)">${esc(f.question)}</summary>
            <p style="margin:10px 0 0;font-size:13px;color:var(--ink);line-height:1.6">${esc(f.answer)}</p>
          </details>
        `).join('')}
      </div>
    </section>
  `;
}

function filterFaq() {
  const q = ($('#faq-search')?.value || '').toLowerCase();
  $$('#faq-list details').forEach(d => {
    const s = d.getAttribute('data-search') || '';
    d.style.display = !q || s.includes(q) ? '' : 'none';
  });
}

// ----------------------------------------------------------------------------
// HELPER: BARRA DE AÇÕES COM EXPORTAÇÃO E IMPRESSÃO
// ----------------------------------------------------------------------------
function renderConsultationMeta(lastUpdate, entity) {
  return `
    <div class="consultation-meta">
      <div class="update-stamp">
        ${icon('clock')} Última atualização desta área: <strong>${esc(lastUpdate)}</strong>
      </div>
      <div class="consultation-actions">
        <button class="button small" onclick="window.print()">${icon('print')} Imprimir Consulta</button>
        <button class="button small" onclick="triggerOpenDataExport('${entity}', 'csv')">${icon('download')} CSV</button>
        <button class="button small" onclick="triggerOpenDataExport('${entity}', 'xml')">${icon('download')} XML</button>
        <button class="button small" onclick="triggerOpenDataExport('${entity}', 'json')">${icon('download')} JSON</button>
      </div>
    </div>
  `;
}

function triggerOpenDataExport(entity, format) {
  window.open(`/api/public/transparency/export?entity=${encodeURIComponent(entity)}&format=${encodeURIComponent(format)}`, '_blank');
}
