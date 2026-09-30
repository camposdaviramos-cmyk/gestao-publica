/**
 * Módulo de Assistência Social e Cidadania (SUAS / CRAS / CREAS / CadÚnico) - Frontend
 * Sistema Integrado Rio das Ostras - Edital PE 552/2026 & Anexo III (410 Itens)
 */

window.SocialUI = {
  currentTab: 'familias',
  selectedFamilyId: null,

  render: function(targetEl) {
    if (!targetEl) targetEl = document.getElementById('main') || document.getElementById('app');
    targetEl.innerHTML = `
      <div class="social-container module-workspace">
        <header class="social-header">
          <div>
            <h1> Assistência Social & Cidadania (SUAS)</h1>
            <p style="margin: 0.25rem 0 0 0; color: var(--muted); font-size: 0.9rem;">
              CRAS, CREAS, Centro POP, Prontuário SUAS 360º, RMA Oficial MDS, Benefícios Eventuais, IVS, Habitação e MROSC
            </p>
          </div>
          <div style="display: flex; gap: 0.5rem;">
            <button class="social-btn-secondary" data-module-click="social-106" >Nova Família</button>
            <button class="social-btn-primary" data-module-click="social-107" >Atualizar</button>
          </div>
        </header>

        <nav class="social-nav-tabs">
          <button class="social-tab-btn ${this.currentTab === 'familias' ? 'active' : ''}" data-tab="familias" data-module-click="social-108" >Famílias & Prontuário</button>
          <button class="social-tab-btn ${this.currentTab === 'rma' ? 'active' : ''}" data-tab="rma" data-module-click="social-109" >RMA Oficial (MDS)</button>
          <button class="social-tab-btn ${this.currentTab === 'beneficios' ? 'active' : ''}" data-tab="beneficios" data-module-click="social-110" >Benefícios & Estoque</button>
          <button class="social-tab-btn ${this.currentTab === 'acolhimento' ? 'active' : ''}" data-tab="acolhimento" data-module-click="social-111" >Acolhimento & Mulher (Sigilo)</button>
          <button class="social-tab-btn ${this.currentTab === 'habitacao' ? 'active' : ''}" data-tab="habitacao" data-module-click="social-112" >Habitação & IVS</button>
          <button class="social-tab-btn ${this.currentTab === 'mrosc' ? 'active' : ''}" data-tab="mrosc" data-module-click="social-113" >MROSC (OSCs Parceiras)</button>
          <button class="social-tab-btn ${this.currentTab === 'territorios' ? 'active' : ''}" data-tab="territorios" data-module-click="social-114" >Mapa de Calor & Diagnóstico</button>
        </nav>

        <main id="social-tab-content">
          ${this.renderTabContent()}
        </main>
      </div>
    `;
    this.postRender();
  },

  switchTab: function(tabName) {
    this.currentTab = tabName;
    const contentEl = document.getElementById('social-tab-content');
    if (contentEl) {
      contentEl.innerHTML = this.renderTabContent();
    }
    // Atualiza classes dos botões
    document.querySelectorAll('.social-tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    return this.postRender();
  },

  refresh: function() {
    return this.switchTab(this.currentTab);
  },

  renderTabContent: function() {
    switch (this.currentTab) {
      case 'familias': return this.renderFamiliasTab();
      case 'rma': return this.renderRmaTab();
      case 'beneficios': return this.renderBeneficiosTab();
      case 'acolhimento': return this.renderAcolhimentoTab();
      case 'habitacao': return this.renderHabitacaoTab();
      case 'mrosc': return this.renderMroscTab();
      case 'territorios': return this.renderTerritoriosTab();
      default: return '<div class="social-card">Aba em desenvolvimento.</div>';
    }
  },

  // ── 1. ABA FAMÍLIAS & PRONTUÁRIO SUAS ──
  renderFamiliasTab: function() {
    return `
      <div class="social-metrics-grid" id="social-family-metrics">
        <div class="social-metric-card">
          <span class="social-metric-title">Famílias Cadastradas</span>
          <span class="social-metric-value" id="metric-total-fam">...</span>
          <span class="social-metric-subtitle">Base Prontuário / CadÚnico</span>
        </div>
        <div class="social-metric-card">
          <span class="social-metric-title">Extrema Pobreza</span>
          <span class="social-metric-value" style="color: #dc2626;" id="metric-extrema-fam">...</span>
          <span class="social-metric-subtitle">Renda per capita ≤ R$ 109,00</span>
        </div>
        <div class="social-metric-card">
          <span class="social-metric-title">Famílias com PCD</span>
          <span class="social-metric-value" style="color: #0284c7;" id="metric-pcd-fam">...</span>
          <span class="social-metric-subtitle">Atenção Prioritária SUAS</span>
        </div>
        <div class="social-metric-card">
          <span class="social-metric-title">Área de Risco</span>
          <span class="social-metric-value" style="color: #ea580c;" id="metric-risco-fam">...</span>
          <span class="social-metric-subtitle">Vulnerabilidade Habitacional</span>
        </div>
      </div>

      <div class="social-card">
        <div class="social-card-header">
          <h3><span></span> Prontuário Eletrônico Familiar (SUAS 360º)</h3>
          <div style="display: flex; gap: 0.5rem;">
            <input type="text" id="social-family-search" placeholder="Buscar por Nome, NIS ou CPF..." style="padding: 0.4rem 0.75rem; border-radius: 6px; border: 1px solid var(--line); font-size: 0.9rem;" data-module-keyup="social-115" >
            <button class="social-btn-primary" data-module-click="social-116" >Filtrar</button>
          </div>
        </div>

        <div style="overflow-x: auto;">
          <table class="social-table">
            <thead>
              <tr>
                <th>Código / NIS</th>
                <th>Responsável Familiar</th>
                <th>Bairro / Território</th>
                <th>Renda Total / Per Capita</th>
                <th>Faixa / IVS</th>
                <th>Completude</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody id="social-families-tbody">
              <tr><td colspan="7" style="text-align: center;">Carregando prontuários familiares...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div id="social-family-drawer" style="display: none; margin-top: 1rem;"></div>
    `;
  },

  // ── 2. ABA RMA OFICIAL (CRAS / CREAS / CENTRO POP) ──
  renderRmaTab: function() {
    return `
      <div class="social-card">
        <div class="social-card-header">
          <h3><span></span> Registro Mensal de Atendimento Oficial (MDS / Censo SUAS)</h3>
          <div style="display: flex; gap: 0.5rem; align-items: center;">
            <select id="rma-unit-select" data-module-change="social-117"  style="padding: 0.4rem; border-radius: 6px; border: 1px solid var(--line);">
              <option value="1">CRAS Central - Jardim Campomar</option>
              <option value="2">CRAS Sul - Cidade Beiramar</option>
              <option value="4">CREAS Extensão do Bosque</option>
              <option value="5">Centro POP Âncora</option>
            </select>
            <select id="rma-month-select" data-module-change="social-118"  style="padding: 0.4rem; border-radius: 6px; border: 1px solid var(--line);">
              <option value="1">Janeiro / 2026</option>
              <option value="2">Fevereiro / 2026</option>
              <option value="3">Março / 2026</option>
            </select>
            <button class="social-btn-primary" data-module-click="social-119" >Baixar XML Oficial MDS</button>
          </div>
        </div>

        <div id="rma-content-display">
          <div style="text-align: center; padding: 2rem;">Carregando dados do RMA...</div>
        </div>
      </div>
    `;
  },

  // ── 3. ABA BENEFÍCIOS EVENTUAIS & ALMOXARIFADO ──
  renderBeneficiosTab: function() {
    return `
      <div class="social-card" style="margin-bottom: 1rem;">
        <div class="social-card-header">
          <h3><span></span> Estoque de Insumos & Benefícios Eventuais</h3>
          <button class="social-btn-primary" data-module-click="social-120" >Entrada de Estoque</button>
        </div>
        <div style="overflow-x: auto;">
          <table class="social-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Insumo / Benefício</th>
                <th>Categoria</th>
                <th>Estoque Atual</th>
                <th>Mínimo</th>
                <th>Lotes Ativos</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody id="social-supplies-tbody">
              <tr><td colspan="7" style="text-align: center;">Carregando almoxarifado socioassistencial...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="social-card">
        <div class="social-card-header">
          <h3><span></span> Histórico de Concessões de Benefícios Eventuais (LOAS)</h3>
          <button class="social-btn-primary" data-module-click="social-121" >Nova Concessão com Parecer CRESS</button>
        </div>
        <div style="overflow-x: auto;">
          <table class="social-table">
            <thead>
              <tr>
                <th>Data</th>
                <th>Família / NIS</th>
                <th>Tipo Benefício</th>
                <th>Insumo Fornecido</th>
                <th>Parecer Técnico</th>
                <th>Assistente Social (CRESS)</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody id="social-benefits-tbody">
              <tr><td colspan="7" style="text-align: center;">Carregando concessões...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  // ── 4. ABA ACOLHIMENTO & MULHER (SIGILO ESTRITO) ──
  renderAcolhimentoTab: function() {
    return `
      <div class="social-card" style="margin-bottom: 1rem;">
        <div class="social-card-header">
          <h3><span></span> Vagas de Acolhimento Institucional (Crianças, Idosos e Famílias)</h3>
          <button class="social-btn-primary" data-module-click="social-122" >Admissão em Acolhimento</button>
        </div>
        <div style="overflow-x: auto;">
          <table class="social-table">
            <thead>
              <tr>
                <th>Unidade</th>
                <th>Acolhido</th>
                <th>Data Admissão</th>
                <th>Motivo / Processo Judicial</th>
                <th>Leito</th>
                <th>Responsável Técnico</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody id="social-shelterings-tbody">
              <tr><td colspan="7" style="text-align: center;">Carregando acolhimentos...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="social-card">
        <div class="social-card-header">
          <h3><span></span> Atendimento com Sigilo Estrito a Mulheres em Situação de Violência (Lei Maria da Penha)</h3>
          <button class="social-btn-primary" data-module-click="social-123" >Registrar Atendimento Sigiloso</button>
        </div>
        <p style="font-size: 0.85rem; color: var(--muted); margin-bottom: 1rem;">
          Conforme Resolução CFESS nº 493/06 e Lei 11.340/06, os dados de identificação e endereços de mulheres abrigadas são criptografados sob sigilo funcional restrito aos profissionais CRESS/CRP.
        </p>
        <div style="background: var(--paper); border: 1px solid var(--line); border-radius: 8px; padding: 1rem;">
          <strong>Protocolo Ativo de Proteção Municipal:</strong> Casa Abrigo Viva Mulher com vaga e alimentação garantidas, botão de pânico integrado à Guarda Municipal e acompanhamento psicossocial contínuo.
        </div>
      </div>
    `;
  },

  // ── 5. ABA HABITAÇÃO DE INTERESSE SOCIAL & IVS ──
  renderHabitacaoTab: function() {
    return `
      <div class="social-card" style="margin-bottom: 1rem;">
        <div class="social-card-header">
          <h3><span></span> Conjuntos Habitacionais Municipais de Interesse Social</h3>
        </div>
        <div style="overflow-x: auto;">
          <table class="social-table">
            <thead>
              <tr>
                <th>Programa</th>
                <th>Conjunto Habitacional</th>
                <th>Bairro</th>
                <th>Total Unidades</th>
                <th>Disponíveis</th>
                <th>Cota Idoso (3%)</th>
                <th>Cota PCD (3%)</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody id="social-complexes-tbody">
              <tr><td colspan="8" style="text-align: center;">Carregando conjuntos habitacionais...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="social-card">
        <div class="social-card-header">
          <h3><span></span> Classificação Habitacional & Ranking de Contemplados</h3>
          <button class="social-btn-primary" data-module-click="social-124" >Nova Inscrição Habitacional</button>
        </div>
        <div id="housing-ranking-container">
          <p style="color: var(--muted);">Selecione um conjunto habitacional para visualizar a classificação com cotas aplicadas.</p>
        </div>
      </div>
    `;
  },

  // ── 6. ABA MROSC (OSCS PARCEIRAS LEI 13.019/14) ──
  renderMroscTab: function() {
    return `
      <div class="social-card" style="margin-bottom: 1rem;">
        <div class="social-card-header">
          <h3><span></span> Organizações da Sociedade Civil (MROSC - Lei 13.019/2014)</h3>
          <button class="social-btn-primary" data-module-click="social-125" >Cadastrar OSC</button>
        </div>
        <div style="overflow-x: auto;">
          <table class="social-table">
            <thead>
              <tr>
                <th>CNPJ</th>
                <th>Razão Social / Nome Fantasia</th>
                <th>Representante Legal</th>
                <th>Certidões</th>
                <th>Status Cadastral</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody id="social-oscs-tbody">
              <tr><td colspan="6" style="text-align: center;">Carregando OSCs parceiras...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="social-card">
        <div class="social-card-header">
          <h3><span></span> Termos de Parceria & Prestações de Contas Mensais</h3>
        </div>
        <div style="overflow-x: auto;">
          <table class="social-table">
            <thead>
              <tr>
                <th>Instrumento</th>
                <th>OSC Parceira</th>
                <th>Objeto</th>
                <th>Valor Global</th>
                <th>Conta Vinculada</th>
                <th>Vigência</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody id="social-mrosc-contracts-tbody">
              <tr><td colspan="7" style="text-align: center;">Carregando parcerias MROSC...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  // ── 7. ABA MAPA DE CALOR & DIAGNÓSTICO TERRITORIAL ──
  renderTerritoriosTab: function() {
    return `
      <div class="social-card" style="margin-bottom: 1rem;">
        <div class="social-card-header">
          <h3><span></span> Mapa de Calor Georreferenciado de Vulnerabilidades (IVS)</h3>
          <button class="social-btn-primary" data-module-click="social-126" >Recarregar Pontos</button>
        </div>
        <div class="social-heatmap-box" id="heatmap-container">
          <p style="font-weight: 600; color: var(--ink);">Diagnóstico Geográfico de Rio das Ostras - RJ</p>
          <p style="font-size: 0.85rem; color: var(--muted);">Densidade ponderada por extrema pobreza e Índice de Vulnerabilidade Social.</p>
          <div class="social-heatmap-grid" id="heatmap-neighborhoods-grid">
            <!-- Células geradas via JS -->
          </div>
        </div>
      </div>

      <div class="social-card">
        <div class="social-card-header">
          <h3><span></span> Abrangência dos Bairros e Cobertura CRAS</h3>
        </div>
        <div style="overflow-x: auto;">
          <table class="social-table">
            <thead>
              <tr>
                <th>Bairro / Distrito</th>
                <th>Unidade CRAS de Referência</th>
                <th>Área de Risco</th>
                <th>IVS Médio</th>
                <th>Famílias Cadastradas</th>
              </tr>
            </thead>
            <tbody id="social-territories-tbody">
              <tr><td colspan="5" style="text-align: center;">Carregando territórios...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  // ── PÓS-RENDERIZAÇÃO E CARGA DE DADOS VIA API ──
  postRender: async function() {
    const loaders={familias:['loadFamilies','loadFamilyMetrics'],rma:['loadRma'],beneficios:['loadSupplies','loadBenefits'],acolhimento:['loadShelterings'],habitacao:['loadComplexes'],mrosc:['loadOscs','loadOscContracts'],territorios:['loadHeatmap','loadTerritories']};
    try { await Promise.all((loaders[this.currentTab] || []).map(name => this[name]())); }
    catch(error) { toast(error.message,true); }
  },

  loadFamilyMetrics: function() {
    return ModulesUI.request('/api/social/diagnosis')
      .then(r => r.json())
      .then(d => {
        const setTxt = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        setTxt('metric-total-fam', d.total_families || 0);
        setTxt('metric-extrema-fam', d.extrema_pobreza || 0);
        setTxt('metric-pcd-fam', d.pcd_families || 0);
        setTxt('metric-risco-fam', d.risk_zone_families || 0);
      });
  },

  loadFamilies: function(q) {
    const url = q ? `/api/social/families?q=${encodeURIComponent(q)}` : '/api/social/families';
    return ModulesUI.request(url)
      .then(r => r.json())
      .then(data => {
        const tbody = document.getElementById('social-families-tbody');
        if (!tbody) return;
        if (!data || data.length === 0) {
          tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">Nenhuma família encontrada.</td></tr>';
          return;
        }
        tbody.innerHTML = data.map(f => `
          <tr>
            <td><strong>${ModulesUI.escape(f.family_code)}</strong><br><small style="color: var(--muted);">${ModulesUI.escape(f.head_nis)}</small></td>
            <td><strong>${ModulesUI.escape(f.head_name)}</strong><br><small>${f.head_cpf || 'CPF não informado'}</small></td>
            <td>${ModulesUI.escape(f.neighborhood)} (${f.cras_unit_name || 'CRAS'})</td>
            <td>R$ ${f.total_income.toFixed(2)}<br><small style="color: var(--muted);">R$ ${f.per_capita_income.toFixed(2)} / pessoa</small></td>
            <td>
              <span class="social-badge ${f.income_bracket === 'EXTREMA_POBREZA' ? 'extrema' : f.income_bracket === 'POBREZA' ? 'pobreza' : 'baixa'}">
                ${ModulesUI.escape(f.income_bracket)}
              </span>
              <br><small>IVS: ${f.ivs_score.toFixed(2)} (${ModulesUI.escape(f.ivs_level)})</small>
            </td>
            <td>
              <div style="background: var(--paper); border-radius: 4px; overflow: hidden; width: 60px; height: 8px;">
                <div style="background: #10b981; width: ${ModulesUI.escape(f.cadastral_completeness_pct)}%; height: 100%;"></div>
              </div>
              <small>${ModulesUI.escape(f.cadastral_completeness_pct)}%</small>
            </td>
            <td>
              <button class="social-btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;" data-module-click="social-127" data-arg0="${ModulesUI.escape(f.id)}">Prontuário</button>
            </td>
          </tr>
        `).join('');
      });
  },

  searchFamilies: function() {
    const q = document.getElementById('social-family-search')?.value;
    return this.loadFamilies(q);
  },

  viewFamily: function(fid) {
    return ModulesUI.request(`/api/social/families/${fid}`)
      .then(r => r.json())
      .then(d => {
        const drawer = document.getElementById('social-family-drawer');
        if (!drawer) return;
        const f = d.family;
        drawer.style.display = 'block';
        drawer.innerHTML = `
          <div class="social-card" style="border-left: 4px solid var(--accent);">
            <div class="social-card-header">
              <h3><span></span> Prontuário SUAS 360º — ${ModulesUI.escape(f.head_name)} (Código: ${ModulesUI.escape(f.family_code)})</h3>
              <button class="social-btn-secondary" data-module-click="social-128" >Fechar</button>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
              <div><strong>NIS Responsável:</strong> ${ModulesUI.escape(f.head_nis)}</div>
              <div><strong>CPF:</strong> ${f.head_cpf || 'Não informado'}</div>
              <div><strong>Endereço:</strong> ${ModulesUI.escape(f.address)}, ${ModulesUI.escape(f.neighborhood)}</div>
              <div><strong>Unidade de Referência:</strong> ${f.cras_unit_name || 'CRAS'}</div>
              <div><strong>Renda Familiar:</strong> R$ ${f.total_income.toFixed(2)}</div>
              <div><strong>Renda per capita:</strong> R$ ${f.per_capita_income.toFixed(2)}</div>
              <div><strong>Classificação IVS:</strong> ${ModulesUI.escape(f.ivs_score)} (${ModulesUI.escape(f.ivs_level)})</div>
              <div><strong>Completude Cadastral:</strong> ${ModulesUI.escape(f.cadastral_completeness_pct)}%</div>
            </div>

            <h4>Membros Familiares (${ModulesUI.escape(d.members.length)})</h4>
            <table class="social-table" style="margin-bottom: 1rem;">
              <thead>
                <tr><th>Nome</th><th>Parentesco</th><th>Nascimento</th><th>PCD</th><th>SCFV</th></tr>
              </thead>
              <tbody>
                ${d.members.map(m => `
                  <tr>
                    <td>${ModulesUI.escape(m.name)}</td>
                    <td>${ModulesUI.escape(m.kinship)}</td>
                    <td>${ModulesUI.escape(m.birth_date)}</td>
                    <td>${m.is_pcd ? 'Sim (PCD)' : 'Não'}</td>
                    <td>${m.scfv_enrolled ? 'Inscrito' : 'Não'}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>

            <h4>Histórico de Benefícios Eventuais Concedidos</h4>
            <table class="social-table">
              <thead>
                <tr><th>Data</th><th>Tipo</th><th>Parecer do Técnico</th><th>Assistente Social</th><th>Status</th></tr>
              </thead>
              <tbody>
                ${d.benefits.length ? d.benefits.map(b => `
                  <tr>
                    <td>${b.request_date ? b.request_date.slice(0, 10) : ''}</td>
                    <td>${ModulesUI.escape(b.benefit_type)}</td>
                    <td>${ModulesUI.escape(b.technical_opinion)}</td>
                    <td>${ModulesUI.escape(b.social_worker_name)} (CRESS ${ModulesUI.escape(b.social_worker_cress)})</td>
                    <td><span class="social-badge regular">${ModulesUI.escape(b.status)}</span></td>
                  </tr>
                `).join('') : '<tr><td colspan="5" style="text-align: center;">Nenhum benefício registrado.</td></tr>'}
              </tbody>
            </table>
          </div>
        `;
        drawer.scrollIntoView({ behavior: 'smooth' });
      });
  },

  // ── CARGA DO RMA ──
  loadRma: function() {
    const uid = document.getElementById('rma-unit-select')?.value || 1;
    const month = document.getElementById('rma-month-select')?.value || 1;
    return ModulesUI.request(`/api/social/rma/cras?unit_id=${uid}&year=2026&month=${month}`)
      .then(r => r.json())
      .then(rma => {
        const disp = document.getElementById('rma-content-display');
        if (!disp) return;
        disp.innerHTML = `
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; margin-top: 1rem;">
            <div style="background: var(--paper); border: 1px solid var(--line); border-radius: 8px; padding: 1rem;">
              <h4 style="margin: 0 0 0.5rem 0; color: var(--accent);">Bloco I: Acompanhamento PAIF</h4>
              <p>Famílias em Acompanhamento: <strong>${ModulesUI.escape(rma.paif_total_active)}</strong></p>
              <p>Novas Famílias no Mês: <strong>${ModulesUI.escape(rma.paif_new_inserted)}</strong></p>
              <p>Famílias em Extrema Pobreza: <strong>${ModulesUI.escape(rma.paif_extreme_poverty)}</strong></p>
              <p>Beneficiárias do Bolsa Família: <strong>${ModulesUI.escape(rma.paif_bolsa_familia)}</strong></p>
            </div>
            <div style="background: var(--paper); border: 1px solid var(--line); border-radius: 8px; padding: 1rem;">
              <h4 style="margin: 0 0 0.5rem 0; color: var(--accent);">Bloco II: Atendimentos & Ações</h4>
              <p>Atendimentos Individualizados: <strong>${ModulesUI.escape(rma.atendimentos_total)}</strong></p>
              <p>Visitas Domiciliares: <strong>${ModulesUI.escape(rma.visitas_domiciliares)}</strong></p>
              <p>Reuniões Coletivas PAIF: <strong>${ModulesUI.escape(rma.reunioes_coletivas_paif)}</strong></p>
            </div>
            <div style="background: var(--paper); border: 1px solid var(--line); border-radius: 8px; padding: 1rem;">
              <h4 style="margin: 0 0 0.5rem 0; color: var(--accent);">Bloco III: Benefícios Eventuais</h4>
              <p>Auxílio Natalidade: <strong>${ModulesUI.escape(rma.beneficios_natalidade)}</strong></p>
              <p>Auxílio Funeral: <strong>${ModulesUI.escape(rma.beneficios_funeral)}</strong></p>
              <p>Outros Benefícios (Cestas): <strong>${ModulesUI.escape(rma.beneficios_outros)}</strong></p>
            </div>
          </div>
          <div style="margin-top: 1.5rem; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--line); padding-top: 1rem;">
            <span>Status do Mês: <strong style="color: #059669;">${ModulesUI.escape(rma.status)}</strong></span>
            ${rma.status === 'ABERTO' ? `
              <button class="social-btn-primary" data-module-click="social-129" data-arg0="${ModulesUI.escape(uid)}" data-arg1="${ModulesUI.escape(month)}">Homologar e Fechar RMA</button>
            ` : '<span class="social-badge regular">Fechado e Pronto para o Censo SUAS</span>'}
          </div>
        `;
      });
  },

  exportRmaXml: function() {
    const uid = document.getElementById('rma-unit-select')?.value || 1;
    const month = document.getElementById('rma-month-select')?.value || 1;
    window.open(`/api/social/rma/cras/export-xml?unit_id=${uid}&year=2026&month=${month}`, '_blank');
  },

  closeRmaMonth: function(uid, year, month) {
    if (!confirm("Confirma o fechamento oficial do RMA para o Ministério do Desenvolvimento Social?")) return;
    return ModulesUI.request('/api/social/rma/cras/close', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ unit_id: uid, year: year, month: month })
    })
    .then(r => r.json())
    .then(() => {
      alert("RMA fechado e XML oficial gerado com sucesso!");
      SocialUI.loadRma();
    });
  },

  // ── ESTOQUE & BENEFÍCIOS ──
  loadSupplies: function() {
    return ModulesUI.request('/api/social/supplies')
      .then(r => r.json())
      .then(data => {
        const tbody = document.getElementById('social-supplies-tbody');
        if (!tbody) return;
        tbody.innerHTML = data.map(s => `
          <tr>
            <td><strong>${ModulesUI.escape(s.code)}</strong></td>
            <td>${ModulesUI.escape(s.name)}</td>
            <td>${ModulesUI.escape(s.category)}</td>
            <td><strong>${ModulesUI.escape(s.current_stock)} ${ModulesUI.escape(s.unit_of_measure)}</strong></td>
            <td>${ModulesUI.escape(s.minimum_stock)} ${ModulesUI.escape(s.unit_of_measure)}</td>
            <td><span class="social-badge regular">Ativo</span></td>
            <td>
              <span class="social-badge ${s.current_stock < s.minimum_stock ? 'extrema' : 'regular'}">
                ${s.current_stock < s.minimum_stock ? 'Estoque Baixo' : 'Normal'}
              </span>
            </td>
          </tr>
        `).join('');
      });
  },

  loadBenefits: function() {
    return ModulesUI.request('/api/social/benefits')
      .then(r => r.json())
      .then(data => {
        const tbody = document.getElementById('social-benefits-tbody');
        if (!tbody) return;
        tbody.innerHTML = data.map(b => `
          <tr>
            <td>${b.request_date ? b.request_date.slice(0, 10) : ''}</td>
            <td><strong>${ModulesUI.escape(b.head_name)}</strong><br><small>${ModulesUI.escape(b.family_code)}</small></td>
            <td>${ModulesUI.escape(b.benefit_type)}</td>
            <td>${b.supply_name || 'Auxílio Financeiro'}</td>
            <td>${ModulesUI.escape(b.technical_opinion)}</td>
            <td>${ModulesUI.escape(b.social_worker_name)} (CRESS ${ModulesUI.escape(b.social_worker_cress)})</td>
            <td><span class="social-badge regular">${ModulesUI.escape(b.status)}</span></td>
          </tr>
        `).join('');
      });
  },

  // ── ACOLHIMENTO ──
  loadShelterings: function() {
    return ModulesUI.request('/api/social/shelterings')
      .then(r => r.json())
      .then(data => {
        const tbody = document.getElementById('social-shelterings-tbody');
        if (!tbody) return;
        tbody.innerHTML = data.map(s => `
          <tr>
            <td><strong>${ModulesUI.escape(s.unit_name)}</strong></td>
            <td><strong>${ModulesUI.escape(s.resident_name)}</strong><br><small>${s.resident_cpf_nis || 'Não informado'}</small></td>
            <td>${ModulesUI.escape(s.admission_date)}</td>
            <td>${ModulesUI.escape(s.reason)}<br><small style="color: var(--muted);">${s.judicial_process_number || 'Sem determinação judicial'}</small></td>
            <td>${ModulesUI.escape(s.bed_number)}</td>
            <td>${ModulesUI.escape(s.responsible_technician)}</td>
            <td>
              <button class="social-btn-secondary" style="padding: 0.2rem 0.5rem; font-size: 0.8rem;" data-module-click="social-130" data-arg0="${ModulesUI.escape(s.id)}">Desligar</button>
            </td>
          </tr>
        `).join('');
      });
  },


  // ── HABITAÇÃO ──
  loadComplexes: function() {
    return ModulesUI.request('/api/social/housing/complexes')
      .then(r => r.json())
      .then(data => {
        const tbody = document.getElementById('social-complexes-tbody');
        if (!tbody) return;
        tbody.innerHTML = data.map(c => `
          <tr>
            <td><strong>${ModulesUI.escape(c.program_title)}</strong></td>
            <td>${ModulesUI.escape(c.name)}</td>
            <td>${ModulesUI.escape(c.neighborhood)}</td>
            <td>${ModulesUI.escape(c.total_units)}</td>
            <td><strong style="color: #059669;">${ModulesUI.escape(c.available_units)}</strong></td>
            <td>${ModulesUI.escape(c.reserved_elderly_quota)} vagas</td>
            <td>${ModulesUI.escape(c.reserved_pcd_quota)} vagas</td>
            <td>
              <button class="social-btn-primary" style="padding: 0.2rem 0.5rem; font-size: 0.8rem;" data-module-click="social-131" data-arg0="${ModulesUI.escape(c.program_id)}" data-arg1="${ModulesUI.escape(c.id)}">Ver Ranking</button>
            </td>
          </tr>
        `).join('');
      });
  },

  viewHousingRanking: function(pid, cid) {
    return ModulesUI.request(`/api/social/housing/ranking?program_id=${pid}&complex_id=${cid}`)
      .then(r => r.json())
      .then(d => {
        const container = document.getElementById('housing-ranking-container');
        if (!container) return;
        container.innerHTML = `
          <div style="margin-bottom: 1rem; display: flex; gap: 1rem;">
            <div>Unidades Ofertadas: <strong>${ModulesUI.escape(d.total_available)}</strong></div>
            <div>Contemplados: <strong style="color: #059669;">${ModulesUI.escape(d.contemplated_count)}</strong></div>
            <div>Cotas Atendidas: <strong>${ModulesUI.escape(d.elderly_quota_met)} Idosos</strong> / <strong>${ModulesUI.escape(d.pcd_quota_met)} PCDs</strong></div>
          </div>
          <table class="social-table">
            <thead>
              <tr><th>Posição</th><th>Nº Inscrição</th><th>Pontuação Final</th><th>Cota</th><th>Status</th></tr>
            </thead>
            <tbody>
              ${d.ranking.map(r => `
                <tr>
                  <td><strong>#${ModulesUI.escape(r.ranking_position)}</strong></td>
                  <td>${ModulesUI.escape(r.application_number)}</td>
                  <td><strong>${ModulesUI.escape(r.final_points)} pontos</strong></td>
                  <td><span class="social-badge ${r.special_quota === 'GERAL' ? 'baixa' : 'alerta'}">${ModulesUI.escape(r.special_quota)}</span></td>
                  <td><span class="social-badge ${r.status === 'CONTEMPLADO' ? 'regular' : 'baixa'}">${ModulesUI.escape(r.status)}</span></td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;
      });
  },

  // ── MROSC ──
  loadOscs: function() {
    return ModulesUI.request('/api/social/oscs')
      .then(r => r.json())
      .then(data => {
        const tbody = document.getElementById('social-oscs-tbody');
        if (!tbody) return;
        tbody.innerHTML = data.map(o => `
          <tr>
            <td><strong>${ModulesUI.escape(o.cnpj)}</strong></td>
            <td>${ModulesUI.escape(o.corporate_name)}<br><small style="color: var(--muted);">${o.trade_name || ''}</small></td>
            <td>${ModulesUI.escape(o.legal_representative)}</td>
            <td><span class="social-badge regular">CNDs Regulares</span></td>
            <td><span class="social-badge regular">${ModulesUI.escape(o.registration_status)}</span></td>
            <td>
              <button class="social-btn-secondary" style="padding: 0.2rem 0.5rem; font-size: 0.8rem;" data-module-click="social-132" data-arg0="${ModulesUI.escape(o.id)}" >Ver Certidões</button>
            </td>
          </tr>
        `).join('');
      });
  },

  loadOscContracts: function() {
    return ModulesUI.request('/api/social/oscs/contracts')
      .then(r => r.json())
      .then(data => {
        const tbody = document.getElementById('social-mrosc-contracts-tbody');
        if (!tbody) return;
        tbody.innerHTML = data.map(c => `
          <tr>
            <td><strong>${ModulesUI.escape(c.contract_number)}</strong><br><small>${ModulesUI.escape(c.partnership_type)}</small></td>
            <td>${ModulesUI.escape(c.corporate_name)}</td>
            <td>${ModulesUI.escape(c.plan_title)}</td>
            <td><strong>R$ ${c.global_value.toFixed(2)}</strong></td>
            <td><small>${ModulesUI.escape(c.dedicated_bank_account)}</small></td>
            <td>${ModulesUI.escape(c.start_date)} até ${ModulesUI.escape(c.end_date)}</td>
            <td><span class="social-badge regular">${ModulesUI.escape(c.status)}</span></td>
          </tr>
        `).join('');
      });
  },

  // ── MAPA DE CALOR & TERRITÓRIOS ──
  loadHeatmap: function() {
    return ModulesUI.request('/api/social/heatmap')
      .then(r => r.json())
      .then(data => {
        const grid = document.getElementById('heatmap-neighborhoods-grid');
        if (!grid) return;
        const neighMap = {};
        data.points.forEach(p => {
          if (!neighMap[p.neighborhood]) neighMap[p.neighborhood] = { count: 0, sumWeight: 0, level: p.level };
          neighMap[p.neighborhood].count++;
          neighMap[p.neighborhood].sumWeight += p.weight;
        });

        grid.innerHTML = Object.keys(neighMap).map(n => {
          const item = neighMap[n];
          const avg = (item.sumWeight / item.count).toFixed(2);
          const cls = avg > 0.6 ? 'alta' : avg > 0.35 ? 'media' : 'baixa';
          return `
            <div class="social-heatmap-cell ${cls}">
              <strong>${n}</strong><br>
              <small>Famílias: ${ModulesUI.escape(item.count)}</small><br>
              <small>IVS Médio: ${avg}</small>
            </div>
          `;
        }).join('');
      });
  },

  loadTerritories: function() {
    return ModulesUI.request('/api/social/territories')
      .then(r => r.json())
      .then(data => {
        const tbody = document.getElementById('social-territories-tbody');
        if (!tbody) return;
        tbody.innerHTML = data.map(t => `
          <tr>
            <td><strong>${ModulesUI.escape(t.name)}</strong> (${ModulesUI.escape(t.district)})</td>
            <td>${t.cras_unit_name || 'CRAS Central'}</td>
            <td>${t.high_risk_zone ? '<span class="social-badge extrema">Sim</span>' : 'Não'}</td>
            <td>${ModulesUI.escape(t.vulnerability_index_avg)}</td>
            <td><strong>${ModulesUI.escape(t.families_count)}</strong></td>
          </tr>
        `).join('');
      });
  },

  // ── MODAIS DE CADASTRO ──

};

// ── Interceptação da Página ERP para Assistência Social ──
(function() {
  const originalErpPage = window.erpPage;
  window.erpPage = async function(module) {
    if (module === 'social') {
      setTimeout(() => {
        const main = document.getElementById('main');
        if (main) SocialUI.render(main);
      }, 50);
      return '<div class="loading-panel"><div class="loader"></div>Carregando Assistência Social, CRAS, CREAS e CadÚnico...</div>';
    }
    return originalErpPage ? await originalErpPage(module) : '';
  };
})();
