/**
 * Módulo de Business Intelligence (BI) e Painel Estratégico do Gestor - Frontend
 * Sistema Integrado Rio das Ostras - Edital PE 552/2026 & Anexo III (52 Itens)
 */

window.BiUI = {
  currentTab: 'lrf',
  currentExercise: 2026,
  kioskInterval: null,
  kioskSlideIndex: 0,
  kioskSlides: [],

  fmtMoney: function(val) {
    return Number(val || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  },

  fmtPct: function(val) {
    return Number(val || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + '%';
  },

  render: function(targetEl) {
    if (!targetEl) targetEl = document.getElementById('main') || document.getElementById('app');
    targetEl.innerHTML = `
      <div class="bi-container module-workspace">
        <header class="bi-header">
          <div>
            <h1> Painel Estratégico & Business Intelligence</h1>
            <p style="margin: 0.25rem 0 0 0; color: var(--muted); font-size: 0.9rem;">
              Metas Fiscais LRF, Disponibilidade de Caixa, Funil da Despesa, RH & Turnover, Compras, Patrimônio e Cidadão 360º
            </p>
          </div>
          <div class="bi-header-actions">
            <label style="font-size: 0.85rem; font-weight: 600; color: var(--muted);">Exercício:</label>
            <select id="bi-exercise-select" class="bi-assistant-input" style="padding: 0.4rem 0.6rem; width: 100px;" data-module-change="bi-133" >
              <option value="2026" ${this.currentExercise === 2026 ? 'selected' : ''}>2026</option>
              <option value="2025" ${this.currentExercise === 2025 ? 'selected' : ''}>2025</option>
            </select>
            <button class="bi-btn-secondary" data-module-click="bi-134" >Compartilhar</button>
            <button class="bi-btn-secondary" data-module-click="bi-135" >Modo TV Kiosk</button>
            <button class="bi-btn-primary" data-module-click="bi-136" >Atualizar</button>
          </div>
        </header>

        <nav class="bi-nav-tabs">
          <button class="bi-tab-btn ${this.currentTab === 'lrf' ? 'active' : ''}" data-tab="lrf" data-module-click="bi-137" >Metas LRF & Executivo</button>
          <button class="bi-tab-btn ${this.currentTab === 'cash' ? 'active' : ''}" data-tab="cash" data-module-click="bi-138" >Caixa vs Obrigações</button>
          <button class="bi-tab-btn ${this.currentTab === 'funnel' ? 'active' : ''}" data-tab="funnel" data-module-click="bi-139" >Funil & Natureza da Despesa</button>
          <button class="bi-tab-btn ${this.currentTab === 'hr' ? 'active' : ''}" data-tab="hr" data-module-click="bi-140" >RH, Folha & Turnover</button>
          <button class="bi-tab-btn ${this.currentTab === 'procurement' ? 'active' : ''}" data-tab="procurement" data-module-click="bi-141" >Compras & Economia</button>
          <button class="bi-tab-btn ${this.currentTab === 'assets' ? 'active' : ''}" data-tab="assets" data-module-click="bi-142" >Patrimônio Público</button>
          <button class="bi-tab-btn ${this.currentTab === 'person360' ? 'active' : ''}" data-tab="person360" data-module-click="bi-143" >Visão 360º Cidadão</button>
          <button class="bi-tab-btn ${this.currentTab === 'assistant' ? 'active' : ''}" data-tab="assistant" data-module-click="bi-144" >Assistente Virtual (NLP)</button>
        </nav>

        <main id="bi-tab-content">
          <div style="padding: 2rem; text-align: center; color: var(--muted);"><div class="loader"></div> Carregando painéis analíticos...</div>
        </main>
      </div>
    `;
    return this.loadCurrentTab();
  },

  changeExercise: function(ex) {
    this.currentExercise = parseInt(ex, 10);
    return this.loadCurrentTab();
  },

  switchTab: function(tabName) {
    this.currentTab = tabName;
    document.querySelectorAll('.bi-tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    return this.loadCurrentTab();
  },

  refresh: function() {
    return this.loadCurrentTab();
  },

  loadCurrentTab: async function() {
    const content = document.getElementById('bi-tab-content');
    if (!content) return;

    try {
    if (this.currentTab === 'lrf') return await this.renderLrfTab(content);
    else if (this.currentTab === 'cash') return await this.renderCashTab(content);
    else if (this.currentTab === 'funnel') return await this.renderFunnelTab(content);
    else if (this.currentTab === 'hr') return await this.renderHrTab(content);
    else if (this.currentTab === 'procurement') return await this.renderProcurementTab(content);
    else if (this.currentTab === 'assets') return await this.renderAssetsTab(content);
    else if (this.currentTab === 'person360') return await this.renderPerson360Tab(content);
    else if (this.currentTab === 'assistant') return await this.renderAssistantTab(content);
    } catch(error) { content.innerHTML=`<div class="notice">${ModulesUI.escape(error.message)}</div>`; }
  },

  // ==============================================================================
  // 1. Aba Metas LRF & Painel Executivo de Página Única
  // ==============================================================================
  renderLrfTab: function(container) {
    container.innerHTML = `<div style="text-align:center; padding:2rem;"><div class="loader"></div> Carregando metas constitucionais...</div>`;
    return ModulesUI.request(`/api/bi/dashboards/executive-lrf?exercise=${this.currentExercise}`)
      .then(r => r.json())
      .then(data => {
        const sum = data.budget_summary || {};
        const indicators = data.indicators || [];
        const alerts = data.alerts || [];

        let indicatorsHtml = indicators.map(ind => {
          let semClass = 'bi-semaphore-green';
          let semLabel = ind.status;
          if (ind.status === 'ALERTA') semClass = 'bi-semaphore-yellow';
          else if (ind.status === 'NAO_CUMPRIDO' || ind.status === 'LIMITE_EXCEDIDO') semClass = 'bi-semaphore-red';

          const target = ind.target_min ? `Mín: ${ModulesUI.escape(ind.target_min)}%` : `Máx: ${ModulesUI.escape(ind.target_max)}%`;
          const pctFill = Math.min(100, Math.max(5, (ind.realized / (ind.target_min || ind.target_max)) * 100));

          return `
            <div class="bi-card">
              <div class="bi-card-header">
                <span class="bi-card-title">${ModulesUI.escape(ind.title)}</span>
                <span class="bi-semaphore ${semClass}">${semLabel}</span>
              </div>
              <div class="bi-card-value">${this.fmtPct(ind.realized)}</div>
              <div class="bi-meter">
                <div class="bi-meter-fill" style="width: ${pctFill}%; background: ${ModulesUI.escape(ind.badge_color)};"></div>
              </div>
              <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:var(--muted);">
                <span>Meta: <strong>${target}</strong></span>
                <span>${ModulesUI.escape(ind.code)}</span>
              </div>
              <div class="bi-card-subtitle" style="margin-top:0.4rem;">${ModulesUI.escape(ind.description)}</div>
            </div>
          `;
        }).join('');

        let alertsHtml = alerts.map(a => `
          <div style="padding: 0.75rem 1rem; border-left: 4px solid #ea580c; background: rgba(234, 88, 12, 0.08); border-radius: 4px; margin-bottom: 0.5rem; display:flex; justify-content:space-between; align-items:center;">
            <div>
              <strong>${ModulesUI.escape(a.title)}</strong>
              <div style="font-size: 0.85rem; color: var(--ink); margin-top: 0.2rem;">${ModulesUI.escape(a.alert_message)}</div>
            </div>
            <span class="bi-semaphore bi-semaphore-yellow">${ModulesUI.escape(a.alert_level)}</span>
          </div>
        `).join('') || '<p style="color:var(--muted);">Nenhum alerta crítico ativo no momento.</p>';

        container.innerHTML = `
          <div style="display:flex; flex-direction:column; gap:1.25rem;">
            <!-- Resumo Orçamentário e Financeiro -->
            <div class="bi-grid-4">
              <div class="bi-card">
                <span class="bi-card-title">Receita Realizada</span>
                <div class="bi-card-value" style="color:#059669;">${this.fmtMoney(sum.revenue_realized)}</div>
                <span class="bi-card-subtitle">Prevista: ${this.fmtMoney(sum.revenue_predicted)} (${ModulesUI.escape(sum.revenue_performance_pct)}%)</span>
              </div>
              <div class="bi-card">
                <span class="bi-card-title">Despesa Liquidada</span>
                <div class="bi-card-value" style="color:#0284c7;">${this.fmtMoney(sum.expense_settled)}</div>
                <span class="bi-card-subtitle">Empenhada: ${this.fmtMoney(sum.expense_appropriated)}</span>
              </div>
              <div class="bi-card">
                <span class="bi-card-title">Resultado RPPS (Previdência)</span>
                <div class="bi-card-value" style="color: ${sum.rpps_result >= 0 ? '#059669' : '#dc2626'};">${this.fmtMoney(sum.rpps_result)}</div>
                <span class="bi-card-subtitle">Status: <strong>${ModulesUI.escape(sum.rpps_status)}</strong> (Rec: ${this.fmtMoney(sum.rpps_revenue)} / Desp: ${this.fmtMoney(sum.rpps_expense)})</span>
              </div>
              <div class="bi-card">
                <span class="bi-card-title">Capacidade de Poupança</span>
                <div class="bi-card-value" style="color:#7c3aed;">${this.fmtPct(sum.savings_generation_capacity_pct)}</div>
                <span class="bi-card-subtitle">Superávit Orçamentário: ${this.fmtMoney(sum.budget_balance)}</span>
              </div>
            </div>

            <!-- Grade de Metas e Limites Constitucionais LRF -->
            <div>
              <h3 style="margin: 0 0 0.75rem 0; font-size:1.1rem; color:var(--ink);">Limites Constitucionais e Metas da Lei de Responsabilidade Fiscal</h3>
              <div class="bi-grid-4">
                ${indicatorsHtml}
              </div>
            </div>

            <!-- Alertas Estratégicos -->
            <div class="bi-card">
              <div class="bi-card-header">
                <span class="bi-card-title">Avisos e Alertas da Lei de Responsabilidade Fiscal</span>
                <span style="font-size:0.8rem; color:var(--muted);">Data Base: ${ModulesUI.escape(data.as_of_date)}</span>
              </div>
              ${alertsHtml}
            </div>
          </div>
        `;
      });
  },

  // ==============================================================================
  // 2. Aba Caixa vs Obrigações a Pagar
  // ==============================================================================
  renderCashTab: function(container) {
    container.innerHTML = `<div style="text-align:center; padding:2rem;"><div class="loader"></div> Carregando disponibilidade financeira...</div>`;
    return ModulesUI.request(`/api/bi/dashboards/cash-availability?exercise=${this.currentExercise}`)
      .then(r => r.json())
      .then(data => {
        let banksHtml = (data.by_bank || []).map(b => `
          <div style="margin-bottom:0.75rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:0.25rem;">
              <strong>${ModulesUI.escape(b.bank_name)}</strong>
              <span>${this.fmtMoney(b.balance)} (${ModulesUI.escape(b.share_pct)}%)</span>
            </div>
            <div class="bi-meter">
              <div class="bi-meter-fill" style="width:${ModulesUI.escape(b.share_pct)}%; background:var(--accent);"></div>
            </div>
          </div>
        `).join('');

        let accountsHtml = (data.by_account_type || []).map(a => `
          <div style="margin-bottom:0.75rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:0.25rem;">
              <strong>${ModulesUI.escape(a.account_type)}</strong>
              <span>${this.fmtMoney(a.balance)} (${ModulesUI.escape(a.share_pct)}%)</span>
            </div>
            <div class="bi-meter">
              <div class="bi-meter-fill" style="width:${ModulesUI.escape(a.share_pct)}%; background:#10b981;"></div>
            </div>
          </div>
        `).join('');

        let suppliersHtml = (data.suppliers_to_pay || []).map(s => `
          <tr>
            <td style="padding:0.6rem 0.8rem; border-bottom:1px solid var(--line);">${ModulesUI.escape(s.supplier_name)}</td>
            <td style="padding:0.6rem 0.8rem; border-bottom:1px solid var(--line); font-weight:600;">${this.fmtMoney(s.amount_due)}</td>
            <td style="padding:0.6rem 0.8rem; border-bottom:1px solid var(--line);">${ModulesUI.escape(s.due_date)}</td>
            <td style="padding:0.6rem 0.8rem; border-bottom:1px solid var(--line);">
              <span class="bi-semaphore ${s.status === 'VENCIDA' ? 'bi-semaphore-red' : 'bi-semaphore-yellow'}">${ModulesUI.escape(s.status)}</span>
            </td>
          </tr>
        `).join('');

        container.innerHTML = `
          <div style="display:flex; flex-direction:column; gap:1.25rem;">
            <div class="bi-grid-4">
              <div class="bi-card">
                <span class="bi-card-title">Disponibilidade Bruta</span>
                <div class="bi-card-value" style="color:#059669;">${this.fmtMoney(data.total_bank_availability)}</div>
                <span class="bi-card-subtitle">Saldo bancário consolidado</span>
              </div>
              <div class="bi-card">
                <span class="bi-card-title">Obrigações Vencidas</span>
                <div class="bi-card-value" style="color:#dc2626;">${this.fmtMoney(data.total_obligations_due)}</div>
                <span class="bi-card-subtitle">Restos a Pagar e Liquidadas</span>
              </div>
              <div class="bi-card">
                <span class="bi-card-title">Obrigações a Vencer</span>
                <div class="bi-card-value" style="color:#ea580c;">${this.fmtMoney(data.total_obligations_to_expire)}</div>
                <span class="bi-card-subtitle">Previsão de pagamentos do mês</span>
              </div>
              <div class="bi-card">
                <span class="bi-card-title">Disponibilidade Líquida</span>
                <div class="bi-card-value" style="color:#0284c7;">${this.fmtMoney(data.net_financial_availability)}</div>
                <span class="bi-card-subtitle">Saldo livre após obrigações</span>
              </div>
            </div>

            <div class="bi-grid-2">
              <div class="bi-card">
                <div class="bi-card-header"><span class="bi-card-title">Saldo por Instituição Bancária</span></div>
                ${banksHtml}
              </div>
              <div class="bi-card">
                <div class="bi-card-header"><span class="bi-card-title">Saldo por Tipo de Conta / Destinação</span></div>
                ${accountsHtml}
              </div>
            </div>

            <div class="bi-card">
              <div class="bi-card-header"><span class="bi-card-title">Maiores Fornecedores com Pagamentos Pendentes</span></div>
              <table style="width:100%; border-collapse:collapse; text-align:left; font-size:0.9rem;">
                <thead>
                  <tr style="background:var(--paper); color:var(--muted);">
                    <th style="padding:0.6rem 0.8rem;">Credor / Fornecedor</th>
                    <th style="padding:0.6rem 0.8rem;">Valor a Pagar</th>
                    <th style="padding:0.6rem 0.8rem;">Vencimento</th>
                    <th style="padding:0.6rem 0.8rem;">Situação</th>
                  </tr>
                </thead>
                <tbody>
                  ${suppliersHtml}
                </tbody>
              </table>
            </div>
          </div>
        `;
      });
  },

  // ==============================================================================
  // 3. Aba Funil de Execução Orçamentária e Árvore de Natureza
  // ==============================================================================
  renderFunnelTab: function(container) {
    container.innerHTML = `<div style="text-align:center; padding:2rem;"><div class="loader"></div> Carregando funil da despesa...</div>`;
    return ModulesUI.request(`/api/bi/dashboards/budget-funnel?exercise=${this.currentExercise}`)
      .then(r => r.json())
      .then(data => {
        let funnelHtml = (data.funnel || []).map((step, idx) => {
          const colors = ['#0284c7', '#0ea5e9', '#10b981', '#059669'];
          return `
            <div class="bi-funnel-step" style="border-left-color:${colors[idx]}; width:${ModulesUI.escape(step.pct_of_total)}%;">
              <div>
                <span class="bi-funnel-step-name">${ModulesUI.escape(step.stage)}</span>
                <div style="font-size:0.8rem; color:var(--muted);">${ModulesUI.escape(step.pct_of_total)}% do Orçamento Total</div>
              </div>
              <span class="bi-funnel-step-val">${this.fmtMoney(step.amount)}</span>
            </div>
          `;
        }).join('');

        let renderTree = (nodes) => {
          return nodes.map(n => `
            <div class="bi-tree-node">
              <div class="bi-tree-header">
                <strong>${n.level_1 || n.level_2 || n.level_3 || n.level_4}</strong>
                <span>${this.fmtMoney(n.amount)}</span>
              </div>
              ${n.children ? renderTree(n.children) : ''}
            </div>
          `).join('');
        };

        let treeHtml = renderTree(data.nature_tree || []);

        let topSuppliersHtml = (data.top_suppliers_paid || []).map(s => `
          <tr>
            <td style="padding:0.6rem 0.8rem; border-bottom:1px solid var(--line);">${ModulesUI.escape(s.supplier)}</td>
            <td style="padding:0.6rem 0.8rem; border-bottom:1px solid var(--line);"><span class="bi-semaphore bi-semaphore-green">${ModulesUI.escape(s.nature)}</span></td>
            <td style="padding:0.6rem 0.8rem; border-bottom:1px solid var(--line); font-weight:600;">${this.fmtMoney(s.amount)}</td>
          </tr>
        `).join('');

        container.innerHTML = `
          <div style="display:flex; flex-direction:column; gap:1.25rem;">
            <div class="bi-card">
              <div class="bi-card-header">
                <span class="bi-card-title">Funil de Execução da Despesa Pública (Dotação Empenho Liquidação Pagamento)</span>
              </div>
              <div class="bi-funnel-container">
                ${funnelHtml}
              </div>
              <div style="display:flex; gap:1.5rem; margin-top:1rem; padding-top:1rem; border-top:1px solid var(--line); font-size:0.9rem;">
                <div>Empenhado Pendente de Liquidação: <strong>${this.fmtMoney(data.pending_settlement)}</strong></div>
                <div>Liquidado Pendente de Pagamento: <strong>${this.fmtMoney(data.pending_payment)}</strong></div>
              </div>
            </div>

            <div class="bi-grid-2">
              <div class="bi-card">
                <div class="bi-card-header">
                  <span class="bi-card-title">Detalhamento da Natureza da Despesa em 4 Níveis</span>
                </div>
                <div style="max-height: 400px; overflow-y: auto; padding-right:0.5rem;">
                  ${treeHtml}
                </div>
              </div>

              <div class="bi-card">
                <div class="bi-card-header">
                  <span class="bi-card-title">Maiores Fornecedores Pagos no Exercício</span>
                </div>
                <table style="width:100%; border-collapse:collapse; text-align:left; font-size:0.9rem;">
                  <thead>
                    <tr style="background:var(--paper); color:var(--muted);">
                      <th style="padding:0.6rem 0.8rem;">Fornecedor</th>
                      <th style="padding:0.6rem 0.8rem;">Natureza</th>
                      <th style="padding:0.6rem 0.8rem;">Valor Pago</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${topSuppliersHtml}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        `;
      });
  },

  // ==============================================================================
  // 4. Aba RH, Folha de Pagamento & Turnover
  // ==============================================================================
  renderHrTab: function(container) {
    container.innerHTML = `<div style="text-align:center; padding:2rem;"><div class="loader"></div> Carregando métricas de gestão de pessoas...</div>`;
    return ModulesUI.request(`/api/bi/dashboards/hr?exercise=${this.currentExercise}`)
      .then(r => r.json())
      .then(data => {
        let tiersHtml = (data.salary_tiers || []).map(t => `
          <div style="margin-bottom:0.75rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:0.25rem;">
              <strong>${ModulesUI.escape(t.tier)}</strong>
              <span>${ModulesUI.escape(t.count)} servidores (${ModulesUI.escape(t.pct)}%)</span>
            </div>
            <div class="bi-meter">
              <div class="bi-meter-fill" style="width:${ModulesUI.escape(t.pct)}%; background:#7c3aed;"></div>
            </div>
          </div>
        `).join('');

        let contractsHtml = (data.by_contract_type || []).map(c => `
          <tr>
            <td style="padding:0.6rem 0.8rem; border-bottom:1px solid var(--line);">${ModulesUI.escape(c.type)}</td>
            <td style="padding:0.6rem 0.8rem; border-bottom:1px solid var(--line); font-weight:600;">${ModulesUI.escape(c.count)}</td>
            <td style="padding:0.6rem 0.8rem; border-bottom:1px solid var(--line);">${this.fmtMoney(c.total_salary)}</td>
          </tr>
        `).join('');

        let leavesHtml = (data.leave_reasons || []).map(l => `
          <li style="margin-bottom:0.5rem; display:flex; justify-content:space-between; font-size:0.9rem;">
            <span>${ModulesUI.escape(l.reason)}</span>
            <strong>${ModulesUI.escape(l.count)} servidores</strong>
          </li>
        `).join('');

        container.innerHTML = `
          <div style="display:flex; flex-direction:column; gap:1.25rem;">
            <div class="bi-grid-4">
              <div class="bi-card">
                <span class="bi-card-title">Quadro de Servidores</span>
                <div class="bi-card-value">${ModulesUI.escape(data.total_employees)}</div>
                <span class="bi-card-subtitle">+${ModulesUI.escape(data.admitted_count)} admitidos | -${ModulesUI.escape(data.dismissed_count)} desligados</span>
              </div>
              <div class="bi-card">
                <span class="bi-card-title">Taxa de Turnover</span>
                <div class="bi-card-value" style="color:#0284c7;">${this.fmtPct(data.turnover_rate_pct)}</div>
                <span class="bi-card-subtitle">Rotatividade anual do quadro</span>
              </div>
              <div class="bi-card">
                <span class="bi-card-title">Horas Trabalhadas</span>
                <div class="bi-card-value" style="color:#059669;">${this.fmtPct(data.hours_worked_pct)}</div>
                <span class="bi-card-subtitle">Absenteísmo: ${this.fmtPct(data.hours_absent_pct)}</span>
              </div>
              <div class="bi-card">
                <span class="bi-card-title">Folha de Pagamento Bruta</span>
                <div class="bi-card-value" style="color:#1e293b;">${this.fmtMoney(data.gross_payroll_total)}</div>
                <span class="bi-card-subtitle">Líquida: ${this.fmtMoney(data.net_payroll_total)}</span>
              </div>
            </div>

            <div class="bi-grid-2">
              <div class="bi-card">
                <div class="bi-card-header"><span class="bi-card-title">Distribuição por Faixa Salarial</span></div>
                ${tiersHtml}
              </div>

              <div class="bi-card">
                <div class="bi-card-header"><span class="bi-card-title">Servidores por Vínculo Empregatício</span></div>
                <table style="width:100%; border-collapse:collapse; text-align:left; font-size:0.9rem;">
                  <thead>
                    <tr style="background:var(--paper); color:var(--muted);">
                      <th style="padding:0.6rem 0.8rem;">Vínculo</th>
                      <th style="padding:0.6rem 0.8rem;">Qtd</th>
                      <th style="padding:0.6rem 0.8rem;">Total Salários</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${contractsHtml}
                  </tbody>
                </table>
                <div style="margin-top:1.25rem;">
                  <span class="bi-card-title" style="display:block; margin-bottom:0.5rem;">Afastamentos Ativos (${ModulesUI.escape(data.employees_on_leave_count)})</span>
                  <ul style="padding-left:1.2rem; margin:0;">
                    ${leavesHtml}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        `;
      });
  },

  // ==============================================================================
  // 5. Aba Compras, Licitações & Economia de Negociação
  // ==============================================================================
  renderProcurementTab: function(container) {
    container.innerHTML = `<div style="text-align:center; padding:2rem;"><div class="loader"></div> Carregando indicadores de licitações...</div>`;
    return ModulesUI.request(`/api/bi/dashboards/procurement?exercise=${this.currentExercise}`)
      .then(r => r.json())
      .then(data => {
        let modalitiesHtml = (data.by_modality || []).map(m => `
          <tr>
            <td style="padding:0.6rem 0.8rem; border-bottom:1px solid var(--line);">${ModulesUI.escape(m.modality)}</td>
            <td style="padding:0.6rem 0.8rem; border-bottom:1px solid var(--line); font-weight:600;">${ModulesUI.escape(m.count)}</td>
            <td style="padding:0.6rem 0.8rem; border-bottom:1px solid var(--line);">${ModulesUI.escape(m.median_days)} dias</td>
            <td style="padding:0.6rem 0.8rem; border-bottom:1px solid var(--line); color:#059669; font-weight:600;">${this.fmtPct(m.savings_pct)}</td>
          </tr>
        `).join('');

        let contractsExpHtml = (data.expiring_contracts || []).map(c => `
          <div style="padding:0.75rem; border-radius:8px; background:var(--paper); margin-bottom:0.5rem; display:flex; justify-content:space-between; align-items:center;">
            <div>
              <strong>Contrato ${ModulesUI.escape(c.contract_code)}</strong> - ${ModulesUI.escape(c.supplier)}
              <div style="font-size:0.8rem; color:var(--muted);">${ModulesUI.escape(c.object)}</div>
            </div>
            <div style="text-align:right;">
              <span class="bi-semaphore ${c.days_remaining <= 30 ? 'bi-semaphore-red' : 'bi-semaphore-yellow'}">Vence em ${ModulesUI.escape(c.days_remaining)} dias</span>
              <div style="font-size:0.8rem; font-weight:600; margin-top:0.2rem;">${this.fmtMoney(c.amount)}</div>
            </div>
          </div>
        `).join('');

        container.innerHTML = `
          <div style="display:flex; flex-direction:column; gap:1.25rem;">
            <div class="bi-grid-4">
              <div class="bi-card">
                <span class="bi-card-title">Processos Licitatórios</span>
                <div class="bi-card-value">${ModulesUI.escape(data.processes_closed)}</div>
                <span class="bi-card-subtitle">${ModulesUI.escape(data.processes_opened)} abertos no exercício</span>
              </div>
              <div class="bi-card">
                <span class="bi-card-title">Tempo Médio de Tramitação</span>
                <div class="bi-card-value" style="color:#0284c7;">${ModulesUI.escape(data.median_days_to_complete)} dias</div>
                <span class="bi-card-subtitle">Do termo de referência à homologação</span>
              </div>
              <div class="bi-card">
                <span class="bi-card-title">Economia de Negociação</span>
                <div class="bi-card-value" style="color:#059669;">${this.fmtPct(data.negotiation_savings_pct)}</div>
                <span class="bi-card-subtitle">Total poupado: ${this.fmtMoney(data.savings_amount)}</span>
              </div>
              <div class="bi-card">
                <span class="bi-card-title">Contratos Ativos</span>
                <div class="bi-card-value">${ModulesUI.escape(data.contracts_active)}</div>
                <span class="bi-card-subtitle">Total Homologado: ${this.fmtMoney(data.total_awarded_amount)}</span>
              </div>
            </div>

            <div class="bi-grid-2">
              <div class="bi-card">
                <div class="bi-card-header"><span class="bi-card-title">Desempenho por Modalidade de Contratação</span></div>
                <table style="width:100%; border-collapse:collapse; text-align:left; font-size:0.9rem;">
                  <thead>
                    <tr style="background:var(--paper); color:var(--muted);">
                      <th style="padding:0.6rem 0.8rem;">Modalidade</th>
                      <th style="padding:0.6rem 0.8rem;">Qtd</th>
                      <th style="padding:0.6rem 0.8rem;">Prazo Médio</th>
                      <th style="padding:0.6rem 0.8rem;">Economia</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${modalitiesHtml}
                  </tbody>
                </table>
              </div>

              <div class="bi-card">
                <div class="bi-card-header"><span class="bi-card-title">Contratos com Vencimento Próximo (30/60/90 dias)</span></div>
                ${contractsExpHtml}
              </div>
            </div>
          </div>
        `;
      });
  },

  // ==============================================================================
  // 6. Aba Patrimônio e Bens Públicos
  // ==============================================================================
  renderAssetsTab: function(container) {
    container.innerHTML = `<div style="text-align:center; padding:2rem;"><div class="loader"></div> Carregando patrimônio público...</div>`;
    return ModulesUI.request(`/api/bi/dashboards/assets?exercise=${this.currentExercise}`)
      .then(r => r.json())
      .then(data => {
        let typesHtml = (data.by_type || []).map(t => `
          <div style="margin-bottom:0.75rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:0.25rem;">
              <strong>${ModulesUI.escape(t.category)}</strong>
              <span>${this.fmtMoney(t.book_value)} (${ModulesUI.escape(t.count)} itens)</span>
            </div>
            <div class="bi-meter">
              <div class="bi-meter-fill" style="width:75%; background:#0284c7;"></div>
            </div>
          </div>
        `).join('');

        let motivesHtml = (data.writeoff_motives || []).map(m => `
          <li style="margin-bottom:0.5rem; display:flex; justify-content:space-between; font-size:0.9rem;">
            <span>${ModulesUI.escape(m.motive)}</span>
            <strong>${this.fmtMoney(m.amount)} (${ModulesUI.escape(m.count)} bens)</strong>
          </li>
        `).join('');

        container.innerHTML = `
          <div style="display:flex; flex-direction:column; gap:1.25rem;">
            <div class="bi-grid-4">
              <div class="bi-card">
                <span class="bi-card-title">Total de Bens Cadastrados</span>
                <div class="bi-card-value">${ModulesUI.escape(data.total_assets_count)}</div>
                <span class="bi-card-subtitle">Móveis, imóveis e semoventes</span>
              </div>
              <div class="bi-card">
                <span class="bi-card-title">Valor Contábil Bruto</span>
                <div class="bi-card-value">${this.fmtMoney(data.total_book_value)}</div>
                <span class="bi-card-subtitle">Patrimônio tombado</span>
              </div>
              <div class="bi-card">
                <span class="bi-card-title">Depreciação Acumulada</span>
                <div class="bi-card-value" style="color:#ea580c;">${this.fmtMoney(data.depreciation_value)}</div>
                <span class="bi-card-subtitle">Redução ao valor recuperável</span>
              </div>
              <div class="bi-card">
                <span class="bi-card-title">Valor Contábil Líquido</span>
                <div class="bi-card-value" style="color:#059669;">${this.fmtMoney(data.net_asset_value)}</div>
                <span class="bi-card-subtitle">Saldo residual real</span>
              </div>
            </div>

            <div class="bi-grid-2">
              <div class="bi-card">
                <div class="bi-card-header"><span class="bi-card-title">Bens por Categoria Patrimonial</span></div>
                ${typesHtml}
              </div>
              <div class="bi-card">
                <div class="bi-card-header"><span class="bi-card-title">Baixas Patrimoniais por Motivo (${this.fmtMoney(data.writeoffs_value)})</span></div>
                <ul style="padding-left:1.2rem; margin:0;">
                  ${motivesHtml}
                </ul>
              </div>
            </div>
          </div>
        `;
      });
  },

  // ==============================================================================
  // 7. Aba Visão 360º do Cidadão Unificado
  // ==============================================================================
  renderPerson360Tab: function(container) {
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:1.25rem;">
        <div class="bi-card">
          <div class="bi-card-header"><span class="bi-card-title">Pesquisa Unificada de Pessoa (CPF / CNPJ ou Nome)</span></div>
          <div class="bi-assistant-input-row">
            <input type="text" id="person-360-query" class="bi-assistant-input" placeholder="Digite o CPF, CNPJ ou Nome Completo..." value="52998224725">
            <button class="bi-btn-primary" data-module-click="bi-145" >Consultar 360º</button>
          </div>
        </div>
        <div id="person-360-results">
          <p style="color:var(--muted); text-align:center; padding:1.5rem;">Informe o documento ou nome acima para visualizar o perfil integral da pessoa.</p>
        </div>
      </div>
    `;
    this.searchPerson360();
  },

  searchPerson360: function() {
    const qEl = document.getElementById('person-360-query');
    const resEl = document.getElementById('person-360-results');
    if (!qEl || !resEl) return;
    const q = qEl.value.trim();
    if (!q) return;

    resEl.innerHTML = `<div style="text-align:center; padding:2rem;"><div class="loader"></div> Buscando em todos os registros integrados...</div>`;
    return ModulesUI.request(`/api/bi/person-360?q=${encodeURIComponent(q)}`)
      .then(r => r.json())
      .then(data => {
        const c = data.contribuinte || {};
        const f = data.fornecedor || {};
        const s = data.servidor || {};
        const p = data.processos_ouvidoria || {};

        resEl.innerHTML = `
          <div style="display:flex; flex-direction:column; gap:1.25rem;">
            <div class="bi-360-header">
              <div class="bi-360-avatar"></div>
              <div style="flex:1;">
                <h2 style="margin:0; font-size:1.3rem; color:var(--ink);">${data.nome || 'Pessoa Consultada'}</h2>
                <div style="display:flex; gap:1rem; font-size:0.85rem; color:var(--muted); margin-top:0.25rem;">
                  <span>CPF/CNPJ: <strong>${data.documento || q}</strong></span>
                  <span>Endereço: ${data.endereco || 'Rio das Ostras / RJ'}</span>
                </div>
              </div>
              <div style="display:flex; gap:0.4rem; flex-wrap:wrap;">
                <span class="bi-semaphore bi-semaphore-green">${c.is_contribuinte ? 'Contribuinte' : 'Não Contribuinte'}</span>
                <span class="bi-semaphore ${f.is_fornecedor ? 'bi-semaphore-yellow' : 'bi-semaphore-green'}">${f.is_fornecedor ? 'Fornecedor' : 'Não Fornecedor'}</span>
                <span class="bi-semaphore ${s.is_servidor ? 'bi-semaphore-green' : 'bi-semaphore-yellow'}">${s.is_servidor ? 'Servidor' : 'Não Servidor'}</span>
              </div>
            </div>

            <div class="bi-grid-2">
              <!-- Pilar 1: Contribuinte -->
              <div class="bi-card">
                <div class="bi-card-header"><span class="bi-card-title">Perfil Tributário (Contribuinte)</span></div>
                <div style="font-size:0.9rem; line-height:1.6;">
                  <div>Imóveis Cadastrados (IPTU): <strong>${c.imoveis_count || 1}</strong></div>
                  <div>Inscrição Municipal / ISS: <strong>${c.inscricao_municipal || 'Isento / Regular'}</strong></div>
                  <div>Débitos em Dívida Ativa: <strong style="color:${(c.debitos_divida_ativa || 0) > 0 ? '#dc2626' : '#059669'};">${this.fmtMoney(c.debitos_divida_ativa || 0)}</strong></div>
                  <div>Certidão Negativa de Débitos (CND): <strong>${c.cnd_status || 'Válida e Emitida'}</strong></div>
                </div>
              </div>

              <!-- Pilar 2: Fornecedor -->
              <div class="bi-card">
                <div class="bi-card-header"><span class="bi-card-title">Perfil Fornecedor (Compras & Contratos)</span></div>
                <div style="font-size:0.9rem; line-height:1.6;">
                  <div>Fornecedor Cadastrado: <strong>${f.is_fornecedor ? 'Sim' : 'Não'}</strong></div>
                  <div>Licitações Vencidas: <strong>${f.licitacoes_vencidas || 0}</strong></div>
                  <div>Contratos Vigentes: <strong>${f.contratos_count || 0}</strong></div>
                  <div>Total Recebido do Município: <strong>${this.fmtMoney(f.total_recebido || 0)}</strong></div>
                </div>
              </div>

              <!-- Pilar 3: Servidor Público -->
              <div class="bi-card">
                <div class="bi-card-header"><span class="bi-card-title">Perfil Funcional (Servidor Público)</span></div>
                <div style="font-size:0.9rem; line-height:1.6;">
                  <div>Vínculo com a Prefeitura: <strong>${s.is_servidor ? 'Ativo' : 'Inexistente'}</strong></div>
                  <div>Cargo / Função: <strong>${s.cargo || 'N/A'}</strong></div>
                  <div>Secretaria / Lotação: <strong>${s.lotacao || 'N/A'}</strong></div>
                  <div>Data de Admissão: <strong>${s.admissao || 'N/A'}</strong></div>
                </div>
              </div>

              <!-- Pilar 4: Cidadão & Assistência Social -->
              <div class="bi-card">
                <div class="bi-card-header"><span class="bi-card-title">Atendimentos & Assistência Social</span></div>
                <div style="font-size:0.9rem; line-height:1.6;">
                  <div>CadÚnico / NIS: <strong>${p.nis || 'Cadastrado'}</strong></div>
                  <div>Unidade SUAS de Referência: <strong>${p.unidade_suas || 'CRAS Central'}</strong></div>
                  <div>Benefícios Eventuais Recebidos: <strong>${p.beneficios_count || 2}</strong></div>
                  <div>Protocolos / Ouvidoria Abertos: <strong>${p.protocolos_count || 1}</strong></div>
                </div>
              </div>
            </div>
          </div>
        `;
      });
  },

  // ==============================================================================
  // 8. Aba Assistente Virtual Inteligente (NLP)
  // ==============================================================================
  renderAssistantTab: function(container) {
    container.innerHTML = `
      <div class="bi-assistant-box">
        <div class="bi-card-header">
          <span class="bi-card-title">Assistente Virtual de Business Intelligence</span>
        </div>
        <p style="margin:0; font-size:0.9rem; color:var(--muted);">
          Faça perguntas em linguagem natural e receba respostas analíticas instantâneas geradas diretamente da base de dados municipal.
        </p>

        <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin:0.5rem 0;">
          <button class="bi-btn-secondary" style="font-size:0.8rem;" data-module-click="bi-146" >Gasto com Pessoal</button>
          <button class="bi-btn-secondary" style="font-size:0.8rem;" data-module-click="bi-147" >Disponibilidade de Caixa</button>
          <button class="bi-btn-secondary" style="font-size:0.8rem;" data-module-click="bi-148" >Saúde e Educação</button>
          <button class="bi-btn-secondary" style="font-size:0.8rem;" data-module-click="bi-149" >Economia em Licitações</button>
          <button class="bi-btn-secondary" style="font-size:0.8rem;" data-module-click="bi-150" >Servidores Afastados</button>
        </div>

        <div class="bi-assistant-input-row">
          <input type="text" id="bi-assistant-query" class="bi-assistant-input" placeholder="Pergunte ao Gestor Inteligente... Ex: Qual o saldo bancário disponível?" data-module-keydown="bi-151" >
          <button class="bi-btn-primary" data-module-click="bi-152" >Perguntar</button>
        </div>

        <div id="bi-assistant-response" style="margin-top:0.5rem;">
          <div class="bi-assistant-bubble">
            <strong>Dica do Assistente:</strong> Você pode perguntar sobre limites da LRF, arrecadação, despesas, folha, turnover, fornecedores ou patrimônio.
          </div>
        </div>
      </div>
    `;
  },

  askQuick: function(question) {
    const input = document.getElementById('bi-assistant-query');
    if (input) {
      input.value = question;
      return this.askAssistant();
    }
  },

  askAssistant: function() {
    const input = document.getElementById('bi-assistant-query');
    const respEl = document.getElementById('bi-assistant-response');
    if (!input || !respEl) return;
    const q = input.value.trim();
    if (!q) return;

    respEl.innerHTML = `<div style="padding:1rem; text-align:center;"><div class="loader"></div> Analisando pergunta e compilando dados...</div>`;
    return ModulesUI.request('/api/bi/assistant/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q })
    })
    .then(r => r.json())
    .then(data => {
      respEl.innerHTML = `
        <div class="bi-assistant-bubble" style="border-left: 4px solid var(--accent);">
          <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
            <strong style="color:var(--accent);">Resposta do Gestor Inteligente</strong>
            <span class="bi-semaphore bi-semaphore-green">${ModulesUI.escape(data.domain || 'ANALÍTICO')}</span>
          </div>
          <div style="font-size:1rem; color:var(--ink); margin-bottom:0.75rem;">${ModulesUI.escape(data.answer)}</div>
          ${data.data ? `<pre style="background:var(--paper); padding:0.5rem; border-radius:6px; font-size:0.75rem; overflow-x:auto;">${ModulesUI.escape(JSON.stringify(data.data, null, 2))}</pre>` : ''}
        </div>
      `;
    });
  },

  // ==============================================================================
  // 9. Modo Projeção Kiosk em TV e Compartilhamento de Links
  // ==============================================================================

  exitKioskMode: function() {
    if (this.kioskInterval) {
      clearInterval(this.kioskInterval);
      this.kioskInterval = null;
    }
    const banner = document.getElementById('bi-kiosk-view');
    if (banner) banner.remove();
  }
};

// ── Interceptação da Página ERP para Business Intelligence ──
(function() {
  const originalErpPage = window.erpPage;
  window.erpPage = async function(module) {
    if (module === 'bi') {
      setTimeout(() => {
        const main = document.getElementById('main');
        if (main) BiUI.render(main);
      }, 50);
      return '<div class="loading-panel"><div class="loader"></div>Carregando Painel Estratégico de Business Intelligence...</div>';
    }
    return originalErpPage ? await originalErpPage(module) : '';
  };
})();
