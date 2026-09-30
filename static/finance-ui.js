/**
 * Módulo Financeiro, Contábil, Orçamentário e Tesouraria - Frontend
 * Sistema Integrado Rio das Ostras - Edital PE 552/2026 & Anexo III (229 Itens)
 */

window.FinanceUI = {
  currentTab: 'contabilidade',

  render: function(targetEl) {
    if (!targetEl) targetEl = document.getElementById('main') || document.getElementById('app');
    targetEl.innerHTML = `
      <div class="finance-container module-workspace">
        <header class="finance-header">
          <div>
            <h1> Gestão Financeira, Orçamentária e Contabilidade</h1>
            <p style="margin: 0.25rem 0 0 0; color: var(--muted); font-size: 0.9rem;">
              SIAFIC (Dec. 10.540/20), PCASP, SICONFI MSC, EFD-Reinf, PPA/LDO/LOA, LRF, Tesouraria e Conciliação OFX
            </p>
          </div>
          <div style="display: flex; gap: 0.5rem;">
            <button class="finance-btn-secondary" data-module-click="finance-0" >Acesso SIAFIC (CPF)</button>
            <button class="finance-btn-primary" data-module-click="finance-1" >Atualizar</button>
          </div>
        </header>

        <nav class="finance-nav-tabs">
          <button class="finance-tab-btn ${this.currentTab === 'contabilidade' ? 'active' : ''}" data-tab="contabilidade" data-module-click="finance-2" >Contabilidade & SIAFIC</button>
          <button class="finance-tab-btn ${this.currentTab === 'reinf' ? 'active' : ''}" data-tab="reinf" data-module-click="finance-3" >EFD-Reinf (Fiscal)</button>
          <button class="finance-tab-btn ${this.currentTab === 'planejamento' ? 'active' : ''}" data-tab="planejamento" data-module-click="finance-4" >Planejamento & Orçamento</button>
          <button class="finance-tab-btn ${this.currentTab === 'lrf' ? 'active' : ''}" data-tab="lrf" data-module-click="finance-5" >LRF & Limites</button>
          <button class="finance-tab-btn ${this.currentTab === 'tesouraria' ? 'active' : ''}" data-tab="tesouraria" data-module-click="finance-6" >Tesouraria & Conciliação OFX</button>
        </nav>

        <main id="finance-tab-content">
          ${this.renderTabContent()}
        </main>
      </div>
    `;
    this.postRender();
  },

  switchTab: function(tabName) {
    this.currentTab = tabName;
    const contentEl = document.getElementById('finance-tab-content');
    if (contentEl) {
      contentEl.innerHTML = this.renderTabContent();
    }
    // Update active tab button style
    document.querySelectorAll('.finance-tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    return this.postRender();
  },

  refresh: function() {
    return this.switchTab(this.currentTab);
  },

  renderTabContent: function() {
    switch (this.currentTab) {
      case 'contabilidade':
        return this.renderContabilidadeTab();
      case 'reinf':
        return this.renderReinfTab();
      case 'planejamento':
        return this.renderPlanejamentoTab();
      case 'lrf':
        return this.renderLrfTab();
      case 'tesouraria':
        return this.renderTesourariaTab();
      default:
        return `<p>Aba não encontrada.</p>`;
    }
  },

  renderContabilidadeTab: function() {
    return `
      <div class="finance-grid module-kpis" style="margin-bottom: 1.5rem;">
        <div class="finance-card">
          <div class="finance-card-title">Orçamento Atualizado</div>
          <div class="finance-stat-value">R$ 865.000.000,00</div>
          <div class="finance-stat-label">Exercício Vigente: 2026</div>
        </div>
        <div class="finance-card">
          <div class="finance-card-title">Despesa Empenhada Líquida</div>
          <div class="finance-stat-value" style="color: #0284c7;">R$ 830.000.000,00</div>
          <div class="finance-stat-label">95,95% do orçamento fixado</div>
        </div>
        <div class="finance-card">
          <div class="finance-card-title">Despesa Liquidada</div>
          <div class="finance-stat-value" style="color: #059669;">R$ 808.000.000,00</div>
          <div class="finance-stat-label">Saldo a liquidar: R$ 22.000.000,00</div>
        </div>
        <div class="finance-card">
          <div class="finance-card-title">Superávit Financeiro Apurado</div>
          <div class="finance-stat-value" style="color: #10b981;">R$ 120.000.000,00</div>
          <div class="finance-stat-label">Ativo Financeiro - Passivo Financeiro</div>
        </div>
      </div>

      <div class="finance-grid">
        <div class="finance-card" style="grid-column: span 2;">
          <div class="finance-card-title">
            <span>Escrituração Contábil em Tempo Real (Livro Diário)</span>
            <button class="finance-btn-primary" data-module-click="finance-7" >+ Novo Lançamento</button>
          </div>
          <div style="overflow-x: auto;">
            <table class="finance-table" id="finance-journal-table">
              <thead>
                <tr>
                  <th>Nº</th>
                  <th>Data</th>
                  <th>Fato Contábil</th>
                  <th>Conta Débito</th>
                  <th>Conta Crédito</th>
                  <th>Valor (R$)</th>
                  <th>Atributo</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody id="finance-journal-body">
                <tr><td colspan="8" style="text-align: center;">Carregando lançamentos contábeis…</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="finance-card">
          <div class="finance-card-title">Demonstrações DCASP e Legais</div>
          <div style="display: flex; flex-direction: column; gap: 0.5rem;">
            <button class="finance-btn-secondary" data-module-click="finance-8" >Anexo 1 - Receita e Despesa (Lei 4.320/64)</button>
            <button class="finance-btn-secondary" data-module-click="finance-9" >Anexo 12 - Balanço Orçamentário</button>
            <button class="finance-btn-secondary" data-module-click="finance-10" >Anexo 13 - Balanço Financeiro</button>
            <button class="finance-btn-secondary" data-module-click="finance-11" >Anexo 14 - Balanço Patrimonial</button>
            <button class="finance-btn-secondary" data-module-click="finance-12" >Anexo 15 - DVP (Variações Patrimoniais)</button>
            <button class="finance-btn-secondary" data-module-click="finance-13" >Anexo 18 - DFC (Fluxos de Caixa)</button>
            <button class="finance-btn-secondary" data-module-click="finance-14" >Liberação de Recursos (Lei 9.452/97)</button>
            <button class="finance-btn-secondary" data-module-click="finance-15" >Duodécimo Câmara (Art. 29-A CF)</button>
            <button class="finance-btn-secondary" data-module-click="finance-16" >Gerar Matriz MSC SICONFI (XBRL/CSV)</button>
          </div>
        </div>
      </div>
    `;
  },

  renderReinfTab: function() {
    return `
      <div class="finance-grid module-kpis" style="margin-bottom: 1.5rem;">
        <div class="finance-card">
          <div class="finance-card-title">Contribuinte EFD-Reinf</div>
          <div style="font-size: 1.1rem; font-weight: 600;">Prefeitura Municipal de Rio das Ostras</div>
          <div style="color: var(--muted); font-size: 0.85rem; margin-top: 0.25rem;">CNPJ: 29.184.000/0001-00 · Classif. 99 (Órgão Público)</div>
          <span class="finance-badge finance-badge-success" style="margin-top: 0.5rem;">Certificado A1 Válido</span>
        </div>
        <div class="finance-card">
          <div class="finance-card-title">Retenções Apuradas no Mês</div>
          <div class="finance-stat-value">R$ 1.850.000,00</div>
          <div class="finance-stat-label">Competência Atual: 2026-01</div>
        </div>
        <div class="finance-card">
          <div class="finance-card-title">Eventos Transmitidos à RFB</div>
          <div class="finance-stat-value" style="color: #10b981;">100%</div>
          <div class="finance-stat-label">R-1000, R-2010 e R-4020 Processados</div>
        </div>
      </div>

      <div class="finance-card">
        <div class="finance-card-title">
          <span>Notas Fiscais e RPS ABRASF com Retenção na Fonte (Tabela 06)</span>
          <button class="finance-btn-primary" data-module-click="finance-17" >+ Registrar Nota Fiscal / RPS</button>
        </div>
        <table class="finance-table">
          <thead>
            <tr>
              <th>NF / RPS</th>
              <th>Credor</th>
              <th>Serviço (Tab 06)</th>
              <th>Valor Bruto (R$)</th>
              <th>Base Retenção (R$)</th>
              <th>Alíquota</th>
              <th>Retenção (R$)</th>
              <th>Status IPC 11</th>
            </tr>
          </thead>
          <tbody id="finance-reinf-body">
            <tr>
              <td>NF 4821</td>
              <td>Construtora Guanabara Ltda</td>
              <td>01.07 - Limpeza e Conservação</td>
              <td>R$ 450.000,00</td>
              <td>R$ 450.000,00</td>
              <td>11%</td>
              <td><strong>R$ 49.500,00</strong></td>
              <td><span class="finance-badge finance-badge-success">Extraorçamentário Gerado</span></td>
            </tr>
            <tr>
              <td>NF 9102</td>
              <td>Segurança Integrada Costa do Sol</td>
              <td>11.02 - Vigilância e Segurança</td>
              <td>R$ 128.000,00</td>
              <td>R$ 128.000,00</td>
              <td>11%</td>
              <td><strong>R$ 14.080,00</strong></td>
              <td><span class="finance-badge finance-badge-success">Extraorçamentário Gerado</span></td>
            </tr>
          </tbody>
        </table>
        <div class="finance-actions" style="margin-top: 1rem;">
          <button class="finance-btn-primary" data-module-click="finance-18" >Transmitir Lote R-2010 (Serviços Tomados)</button>
          <button class="finance-btn-secondary" data-module-click="finance-19" >Transmitir Lote R-4020 (Retenções PJ)</button>
          <button class="finance-btn-secondary" data-module-click="finance-20" >Fechamento da Competência (R-4099)</button>
        </div>
      </div>
    `;
  },

  renderPlanejamentoTab: function() {
    return `
      <div class="finance-grid module-kpis" style="margin-bottom: 1.5rem;">
        <div class="finance-card">
          <div class="finance-card-title">PPA Quadrienal</div>
          <div class="finance-stat-value">2026-2029</div>
          <div class="finance-stat-label">Planejamento Estratégico Municipal</div>
        </div>
        <div class="finance-card">
          <div class="finance-card-title">LDO Anual</div>
          <div class="finance-stat-value">2026</div>
          <div class="finance-stat-label">Diretrizes Orçamentárias e Metas Fiscais</div>
        </div>
        <div class="finance-card">
          <div class="finance-card-title">LOA Anual</div>
          <div class="finance-stat-value">R$ 865 M</div>
          <div class="finance-stat-label">Orçamento Geral do Município</div>
        </div>
      </div>

      <div class="finance-grid">
        <div class="finance-card">
          <div class="finance-card-title">Projeção Percentual das Estimativas (PPA / LDO)</div>
          <p style="font-size: 0.85rem; color: var(--muted);">Projeta estimativas de receita ou metas de ações antes de efetivar nas peças legais.</p>
          <div class="finance-form-group">
            <label>Peça Orçamentária</label>
            <select class="finance-select" id="proj-piece">
              <option value="PPA">Plano Plurianual (PPA)</option>
              <option value="LDO">Lei de Diretrizes Orçamentárias (LDO)</option>
            </select>
          </div>
          <div class="finance-form-group">
            <label>Percentual de Reajuste (%)</label>
            <input type="number" class="finance-input" id="proj-rate" value="5.5" step="0.1">
          </div>
          <button class="finance-btn-primary" data-module-click="finance-21" >Simular Projeção</button>
          <button class="finance-btn-secondary" data-module-click="finance-22"  style="margin-left: 0.5rem;">Importar LOA -> PPA</button>
          <div id="proj-results" style="margin-top: 1rem; font-size: 0.85rem;"></div>
        </div>

        <div class="finance-card">
          <div class="finance-card-title">Decretos de Alteração Orçamentária</div>
          <p style="font-size: 0.85rem; color: var(--muted);">Gera minutas formatadas de Decretos de Crédito Suplementar / Especial.</p>
          <div class="finance-form-group">
            <label>Número do Decreto</label>
            <input type="text" class="finance-input" id="decree-num" value="3.455/2026">
          </div>
          <div class="finance-form-group">
            <label>Tipo de Crédito</label>
            <select class="finance-select" id="decree-type">
              <option value="Suplementar">Suplementar</option>
              <option value="Especial">Especial</option>
              <option value="Extraordinario">Extraordinário</option>
            </select>
          </div>
          <div class="finance-form-group">
            <label>Valor (R$)</label>
            <input type="number" class="finance-input" id="decree-amt" value="2500000">
          </div>
          <div class="finance-form-group">
            <label>Justificativa Legal</label>
            <input type="text" class="finance-input" id="decree-just" value="Reforço de dotações orçamentárias da Secretaria Municipal de Saúde">
          </div>
          <button class="finance-btn-primary" data-module-click="finance-23" >Gerar Decreto Formatado</button>
        </div>
      </div>
    `;
  },

  renderLrfTab: function() {
    return `
      <div class="finance-grid module-kpis" style="margin-bottom: 1.5rem;">
        <div class="finance-card">
          <div class="finance-card-title">Educação Básica (MDE)</div>
          <div class="finance-stat-value" style="color: #10b981;">27,00%</div>
          <div class="finance-stat-label">Mínimo Constitucional: 25,00% (Cumprido)</div>
        </div>
        <div class="finance-card">
          <div class="finance-card-title">FUNDEB (Magistério)</div>
          <div class="finance-stat-value" style="color: #10b981;">75,00%</div>
          <div class="finance-stat-label">Mínimo Constitucional: 70,00% (Cumprido)</div>
        </div>
        <div class="finance-card">
          <div class="finance-card-title">Saúde (Ações e Serviços)</div>
          <div class="finance-stat-value" style="color: #10b981;">16,00%</div>
          <div class="finance-stat-label">Mínimo Constitucional: 15,00% (Cumprido)</div>
        </div>
        <div class="finance-card">
          <div class="finance-card-title">Despesa com Pessoal (LRF)</div>
          <div class="finance-stat-value" style="color: #d97706;">49,68%</div>
          <div class="finance-stat-label">Alerta: 48,6% | Máx: 54,0% (Em Alerta)</div>
        </div>
      </div>

      <div class="finance-card">
        <div class="finance-card-title">Demonstrativos Oficiais da LRF (MDF 14ª Edição STN)</div>
        <div class="finance-grid" style="grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));">
          <div>
            <h4 style="margin: 0 0 0.5rem 0; color: var(--ink);">RREO (Bimestral)</h4>
            <div style="display: flex; flex-direction: column; gap: 0.25rem;">
              <button class="finance-btn-secondary" data-module-click="finance-24" >Anexo 1 - Balanço Orçamentário</button>
              <button class="finance-btn-secondary" data-module-click="finance-25" >Anexo 2 - Despesa Função/Subfunção</button>
              <button class="finance-btn-secondary" data-module-click="finance-26" >Anexo 3 - Receita Corrente Líquida</button>
              <button class="finance-btn-secondary" data-module-click="finance-27" >Anexo 6 - Resultado Primário e Nominal</button>
              <button class="finance-btn-secondary" data-module-click="finance-28" >Anexo 8 - MDE (Educação)</button>
              <button class="finance-btn-secondary" data-module-click="finance-29" >Anexo 12 - ASPS (Saúde)</button>
            </div>
          </div>
          <div>
            <h4 style="margin: 0 0 0.5rem 0; color: var(--ink);">RGF (Quadrimestral)</h4>
            <div style="display: flex; flex-direction: column; gap: 0.25rem;">
              <button class="finance-btn-secondary" data-module-click="finance-30" >Anexo 1 - Despesa com Pessoal</button>
              <button class="finance-btn-secondary" data-module-click="finance-31" >Anexo 2 - Dívida Consolidada Líquida</button>
              <button class="finance-btn-secondary" data-module-click="finance-32" >Anexo 3 - Garantias e Contragarantias</button>
              <button class="finance-btn-secondary" data-module-click="finance-33" >Anexo 5 - Disponibilidade de Caixa / RP</button>
              <button class="finance-btn-secondary" data-module-click="finance-34" >Anexo 6 - Demonstrativo Simplificado</button>
            </div>
          </div>
          <div>
            <h4 style="margin: 0 0 0.5rem 0; color: var(--ink);">Exportações Externas</h4>
            <div style="display: flex; flex-direction: column; gap: 0.25rem;">
              <button class="finance-btn-secondary" data-module-click="finance-35" >Exportar MANAD Previdenciário</button>
              <button class="finance-btn-secondary" data-module-click="finance-36" >Exportar SIGFIS TCE-RJ</button>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  renderTesourariaTab: function() {
    return `
      <div class="finance-grid module-kpis" style="margin-bottom: 1.5rem;">
        <div class="finance-card">
          <div class="finance-card-title">Saldo Disponível em Bancos</div>
          <div class="finance-stat-value">R$ 140.000.000,00</div>
          <div class="finance-stat-label">Contas BB, Caixa, Santander, Bradesco</div>
        </div>
        <div class="finance-card">
          <div class="finance-card-title">Conciliação Bancária OFX</div>
          <div class="finance-stat-value" style="color: #10b981;">100%</div>
          <div class="finance-stat-label">Nenhum movimento pendente de ajuste</div>
        </div>
        <div class="finance-card">
          <div class="finance-card-title">Ordens Bancárias Eletrônicas</div>
          <div class="finance-stat-value" style="color: #0284c7;">CNAB 240 / PIX</div>
          <div class="finance-stat-label">Banco do Brasil S.A. Ativo</div>
        </div>
      </div>

      <div class="finance-grid">
        <div class="finance-card">
          <div class="finance-card-title">
            <span>Ordens Bancárias e Pagamentos (OBE / PIX BB)</span>
            <button class="finance-btn-primary" data-module-click="finance-37" >+ Gerar Lote OBE</button>
          </div>
          <p style="font-size: 0.85rem; color: var(--muted);">Emissão de remessas e estorno automático de pagamentos rejeitados pelo banco.</p>
          <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
            <button class="finance-btn-secondary" data-module-click="finance-38" >Importar Retorno Bancário (com Críticas)</button>
            <button class="finance-btn-secondary" data-module-click="finance-39" >Emitir Cheque</button>
          </div>
        </div>

        <div class="finance-card">
          <div class="finance-card-title">
            <span>Conciliação Bancária OFX Automática</span>
            <button class="finance-btn-primary" data-module-click="finance-40" >Importar Extrato OFX</button>
          </div>
          <p style="font-size: 0.85rem; color: var(--muted);">Leitura de arquivos OFX de qualquer banco com pareamento automático de datas e valores.</p>
          <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
            <button class="finance-btn-secondary" data-module-click="finance-41" >Conciliar Automaticamente</button>
            <button class="finance-btn-secondary" data-module-click="finance-42" >Bloquear Calendário do Mês</button>
          </div>
        </div>

        <div class="finance-card" style="grid-column: span 2;">
          <div class="finance-card-title">
            <span>Recursos Antecipados / Suprimento de Fundos</span>
            <button class="finance-btn-primary" data-module-click="finance-43" >+ Conceder Adiantamento</button>
          </div>
          <div class="table-wrap"><table class="finance-table">
            <thead>
              <tr>
                <th>Protocolo</th>
                <th>Servidor Responsável</th>
                <th>Tipo</th>
                <th>Empenho</th>
                <th>Valor (R$)</th>
                <th>Vencimento</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody id="finance-advance-body"><tr><td colspan="8">Carregando adiantamentos...</td></tr></tbody>
          </table></div>
        </div>
      </div>
    `;
  },

  postRender: function() {
    if (this.currentTab === 'tesouraria') return this.loadAdvanceFunds();
    if (this.currentTab === 'contabilidade') {
      return this.loadJournalEntries();
    }
  },

  loadJournalEntries: function() {
    return ModulesUI.request('/api/finance/journal/query?exercise=2026')
      .then(r => r.json())
      .then(d => {
        const body = document.getElementById('finance-journal-body');
        if (!body) return;
        if (!d.records || d.records.length === 0) {
          body.innerHTML = `<tr><td colspan="8" style="text-align: center;">Nenhum lançamento no período.</td></tr>`;
          return;
        }
        body.innerHTML = d.records.map(r => `
          <tr>
            <td><strong>#${r.entry_number}</strong></td>
            <td>${ModulesUI.escape(r.entry_date)}</td>
            <td>${ModulesUI.escape(r.fact_type)}</td>
            <td><code>${ModulesUI.escape(r.debit_account)}</code></td>
            <td><code>${ModulesUI.escape(r.credit_account)}</code></td>
            <td><strong>R$ ${(r.amount_cents / 100).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</strong></td>
            <td><span class="finance-badge finance-badge-info">${r.superavit_attribute === 'F' ? 'Financeiro' : 'Patrimonial'}</span></td>
            <td>
              ${r.is_reversal === 0
                ? `<button class="finance-btn-secondary" style="padding: 0.2rem 0.5rem; font-size: 0.8rem;" data-module-click="finance-45" data-arg0="${ModulesUI.escape(r.id)}">↩Estornar</button>`
                : `<span class="finance-badge finance-badge-danger">Estorno</span>`}
            </td>
          </tr>
        `).join('');
      })
      .catch(() => {
        const body = document.getElementById('finance-journal-body');
        if (body) body.innerHTML = `<tr><td colspan="8" style="text-align: center; color: red;">Erro ao carregar escrituração.</td></tr>`;
      });
  },


  reverseJournal: function(id) {
    if (!confirm("Deseja estornar o lançamento #" + id + "? O sistema manterá o registro original inalterado.")) return;
    return ModulesUI.request('/api/finance/journal/reverse', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({entry_id: id, reason: "Estorno solicitado pelo operador"})
    })
    .then(r => r.json())
    .then(res => {
      alert("Estorno realizado com sucesso! Lançamento de estorno Nº " + res.reversal_number);
      FinanceUI.loadJournalEntries();
    });
  },

  runProjectionPreview: function() {
    const p = document.getElementById('proj-piece').value;
    const r = parseFloat(document.getElementById('proj-rate').value);
    return ModulesUI.request('/api/finance/budget/project', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({piece_type: p, percentage_rate: r})
    })
    .then(r => r.json())
    .then(d => {
      const el = document.getElementById('proj-results');
      el.innerHTML = `<strong>Simulação Concluída:</strong> ${d.total_items} itens recalculados com projeção de +${r}%. Visualização prévia aprovada.`;
    });
  },


  generateDecree: function() {
    const num = document.getElementById('decree-num').value;
    const typ = document.getElementById('decree-type').value;
    const amt = parseFloat(document.getElementById('decree-amt').value);
    const just = document.getElementById('decree-just').value;

    return ModulesUI.request('/api/finance/budget/decrees', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({decree_number: num, decree_type: typ, amount_cents: Math.round(amt * 100), justification: just})
    })
    .then(r => r.json())
    .then(d => {
      alert("Decreto gerado e publicado com sucesso!\n\n" + d.document_text);
    });
  },

};

// ── Interceptação da Página ERP para Finanças & Contabilidade ──
(function() {
  const originalErpPage = window.erpPage;
  window.erpPage = async function(module) {
    if (module === 'finance') {
      setTimeout(() => {
        const main = document.getElementById('main');
        if (main) FinanceUI.render(main);
      }, 50);
      return '<div class="loading-panel"><div class="loader"></div>Carregando Contabilidade, Finanças e Tesouraria...</div>';
    }
    return originalErpPage ? await originalErpPage(module) : '';
  };
})();

