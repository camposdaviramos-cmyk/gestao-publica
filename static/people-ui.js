/* ── Gestão de Pessoas, Folha, RPPS, eSocial e SST · Rio Gestão ──────── */
(function() {
    'use strict';

    let currentPeopleTab = 'employees';

    function esc(s) {
        if (!s) return '';
        return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    }

    function fmtMoney(val) {
        if (!val && val !== 0) return 'R$ 0,00';
        return Number(val).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    }

    async function apiCall(endpoint, method = 'GET', body = null) {
        return api(endpoint.replace(/^\/api/, ''), method, body);
    }

    window.switchPeopleTab = function(tabName) {
        currentPeopleTab = tabName;
        document.querySelectorAll('.people-tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        const container = document.getElementById('people-tab-content');
        if (!container) return;

        container.innerHTML = '<div style="padding:40px;text-align:center;color:var(--muted);"><div class="loader"></div> Carregando dados...</div>';

        if (tabName === 'employees') return renderEmployeesTab(container);
        else if (tabName === 'payroll') return renderPayrollTab(container);
        else if (tabName === 'consignments') return renderConsignmentsTab(container);
        else if (tabName === 'rpps_sisobi') return renderRppsSisobiTab(container);
        else if (tabName === 'portal') return renderPortalTab(container);
        else if (tabName === 'esocial_sst') return renderEsocialSstTab(container);
    };

    // ── Aba 1: Servidores e Quadro de Vagas ──────────────────────────────
    async function renderEmployeesTab(container) {
        try {
            const [empData, vacData] = await Promise.all([
                apiCall('/api/people/employees'),
                apiCall('/api/people/positions/vacancies?position_id=1&location=LOC-ADM')
            ]);
            const employees = empData.items || [];
            const vac = vacData.vacancies || {};

            container.innerHTML = `
                <div class="people-kpis">
                    <div class="people-kpi-card">
                        <div class="kpi-label">Servidores Ativos</div>
                        <div class="kpi-value">${employees.length}</div>
                        <div class="kpi-sub">Cadastro Municipal Homologado</div>
                    </div>
                    <div class="people-kpi-card">
                        <div class="kpi-label">Vagas Previstas</div>
                        <div class="kpi-value">${vac.budgeted || 10}</div>
                        <div class="kpi-sub">Lotação Sede Administrativa</div>
                    </div>
                    <div class="people-kpi-card">
                        <div class="kpi-label">Vagas Disponíveis</div>
                        <div class="kpi-value">${vac.available || 0}</div>
                        <div class="kpi-sub">Restrição: ${esc(vac.restriction_mode)}</div>
                    </div>
                </div>

                <div class="people-card" style="margin-bottom:20px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:10px;">
                        <h3 style="margin:0;">Quadro Funcional e Vínculos Empregatícios</h3>
                        <div style="display:flex;gap:8px;">
                            <button class="people-btn" data-module-click="people-78" >Cópia de Registro</button>
                            <button class="people-btn secondary" data-module-click="people-79" >Substituto Eventual</button>
                            <button class="people-btn secondary" data-module-click="people-80" >Reintegração Judicial</button>
                        </div>
                    </div>
                    <div class="people-table-wrapper">
                        <table class="people-table">
                            <thead>
                                <tr>
                                    <th>Matrícula</th>
                                    <th>Nome Completo</th>
                                    <th>CPF</th>
                                    <th>Cargo</th>
                                    <th>Lotação</th>
                                    <th>Regime</th>
                                    <th>Vencimento Base</th>
                                    <th>Status</th>
                                    <th>Ações</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${employees.map(e => `
                                    <tr>
                                        <td><strong>${esc(e.code)}</strong></td>
                                        <td>${esc(e.name)}</td>
                                        <td>${esc(e.cpf)}</td>
                                        <td>${esc(e.position)}</td>
                                        <td>${esc(e.department)}</td>
                                        <td><span class="people-badge ${e.regime === 'RPPS' ? 'info' : 'warning'}">${esc(e.regime)}</span></td>
                                        <td>${fmtMoney(e.salary)}</td>
                                        <td><span class="people-badge ${e.active ? 'success' : 'danger'}">${e.active ? 'ATIVO' : 'DESLIGADO'}</span></td>
                                        <td>
                                            <button class="people-btn secondary" style="padding:4px 8px;font-size:11px;" data-module-click="people-81" data-arg0="${ModulesUI.escape(e.id)}">Detalhes</button>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } catch (e) {
            container.innerHTML = `<div style="padding:20px;color:var(--danger);">Erro ao carregar servidores: ${esc(e.message)}</div>`;
        }
    }

    // ── Aba 2: Folha de Pagamento & Simulações ────────────────────────────
    async function renderPayrollTab(container) {
        container.innerHTML = `
            <div class="people-grid">
                <div class="people-card">
                    <h3>Simulação de Reajuste Salarial</h3>
                    <p style="font-size:12px;color:var(--muted);margin-bottom:14px;">Simule o impacto orçamentário do reajuste salarial linear ou por verba antes da aplicação efetiva.</p>
                    <div class="people-form-group">
                        <label>Título da Simulação</label>
                        <input type="text" id="sim-title" value="Reajuste Data-Base 2026" />
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                        <div class="people-form-group">
                            <label>Modalidade</label>
                            <select id="sim-mode">
                                <option value="PERCENTUAL">Percentual (%)</option>
                                <option value="VALOR_FIXO">Valor Fixo (R$)</option>
                            </select>
                        </div>
                        <div class="people-form-group">
                            <label>Valor / Percentual</label>
                            <input type="number" id="sim-value" step="0.1" value="5.0" />
                        </div>
                    </div>
                    <div style="display:flex;gap:10px;margin-top:10px;">
                        <button class="people-btn" data-module-click="people-82" >▶Simular Impacto</button>
                    </div>
                    <div id="sim-results" style="margin-top:16px;"></div>
                </div>

                <div class="people-card">
                    <h3>Fechamento e Bloqueio da Folha Mensal</h3>
                    <p style="font-size:12px;color:var(--muted);margin-bottom:14px;">Bloqueie as movimentações após o fechamento da competência para garantir a segurança dos cálculos.</p>
                    <div class="people-form-group">
                        <label>Competência de Referência</label>
                        <input type="month" id="lock-comp" value="2026-03" />
                    </div>
                    <div style="display:flex;gap:10px;">
                        <button class="people-btn danger" data-module-click="people-83" >Bloquear Folha</button>
                        <button class="people-btn secondary" data-module-click="people-84" >Desbloquear</button>
                    </div>
                    <div id="lock-status" style="margin-top:14px;"></div>

                    <hr style="margin:20px 0;border:none;border-top:1px solid var(--line);" />

                    <h3>Provisões Contábeis (13º e Férias)</h3>
                    <p style="font-size:12px;color:var(--muted);margin-bottom:14px;">Apuração mensal das provisões de 13º salário, férias constitucionais e encargos patronais.</p>
                    <button class="people-btn secondary" data-module-click="people-85" >Gerar Provisões da Competência</button>
                    <div id="provisions-results" style="margin-top:14px;"></div>
                </div>
            </div>
        `;
    }

    // ── Aba 3: Consignações & eConsignado ────────────────────────────────
    async function renderConsignmentsTab(container) {
        container.innerHTML = `
            <div class="people-grid">
                <div class="people-card">
                    <h3>Importação eConsignado (Caixa / Bancos)</h3>
                    <p style="font-size:12px;color:var(--muted);margin-bottom:14px;">Importe arquivos CSV, XLS ou JSON com validação automática da margem legal de 35% e cartão de 5%.</p>
                    <div class="people-form-group">
                        <label>Nome do Arquivo / Lote</label>
                        <input type="text" id="econ-file" value="remessa_consignado_2026_03.json" />
                    </div>
                    <div class="people-form-group">
                        <label>Formato</label>
                        <select id="econ-format">
                            <option value="JSON">JSON</option>
                            <option value="CSV">CSV</option>
                            <option value="XLS">XLS</option>
                        </select>
                    </div>
                    <button class="people-btn" data-module-click="people-86" >Processar Lote eConsignado</button>
                    <div id="econ-results" style="margin-top:16px;"></div>
                </div>

                <div class="people-card">
                    <h3>Plano de Saúde e Vale-Transporte</h3>
                    <div class="people-form-group">
                        <label>Simular Plano de Saúde (Faixa Etária)</label>
                        <button class="people-btn secondary" data-module-click="people-87" >Calcular Desconto Unimed</button>
                        <div id="hp-results" style="margin-top:10px;"></div>
                    </div>
                    <hr style="margin:16px 0;border:none;border-top:1px solid var(--line);" />
                    <div class="people-form-group">
                        <label>Simular Vale-Transporte (Teto Legal 6%)</label>
                        <button class="people-btn secondary" data-module-click="people-88" >Calcular Vale-Transporte</button>
                        <div id="trans-results" style="margin-top:10px;"></div>
                    </div>
                </div>
            </div>
        `;
    }

    // ── Aba 4: Previdência RPPS & Óbitos SISOBI ──────────────────────────
    async function renderRppsSisobiTab(container) {
        try {
            const rppsData = await apiCall('/api/people/rpps/funds');
            const funds = rppsData.funds || [];

            container.innerHTML = `
                <div class="people-grid">
                    <div class="people-card">
                        <h3>Fundos Previdenciários Municipais (RioPrevi)</h3>
                        <div class="people-table-wrapper" style="margin-bottom:16px;">
                            <table class="people-table">
                                <thead>
                                    <tr>
                                        <th>Código</th>
                                        <th>Nome do Fundo</th>
                                        <th>Servidor</th>
                                        <th>Patronal</th>
                                        <th>Suplementar</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${funds.map(f => `
                                        <tr>
                                            <td><strong>${esc(f.code)}</strong></td>
                                            <td>${esc(f.name)}</td>
                                            <td>${f.employee_rate}%</td>
                                            <td>${f.patronal_rate}%</td>
                                            <td><span class="people-badge warning">+${f.supplementary_rate}%</span></td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                        <button class="people-btn" data-module-click="people-89" >Emitir Guia de Recolhimento RPPS</button>
                        <div id="rpps-guide-result" style="margin-top:14px;"></div>
                    </div>

                    <div class="people-card">
                        <h3>Confronto com Base de Óbitos (SISOBI)</h3>
                        <p style="font-size:12px;color:var(--muted);margin-bottom:14px;">Leitura e confrontação de arquivos TXT do SISOBI para cancelamento automático e bloqueio de folha.</p>
                        <button class="people-btn danger" data-module-click="people-90" >Processar Arquivo SISOBI</button>
                        <div id="sisobi-results" style="margin-top:14px;"></div>
                    </div>
                </div>
            `;
        } catch (e) {
            container.innerHTML = `<div style="padding:20px;color:var(--danger);">Erro: ${esc(e.message)}</div>`;
        }
    }

    // ── Aba 5: Portal do Servidor Web ───────────────────────────────────
    async function renderPortalTab(container) {
        container.innerHTML = `
            <div class="people-grid">
                <div class="people-card">
                    <h3>Acesso ao Portal do Servidor (Web / Mobile)</h3>
                    <p style="font-size:12px;color:var(--muted);margin-bottom:14px;">Acesso mediante CPF e senha, com emissão de contracheque digital e informe de rendimentos RFB.</p>
                    <div class="people-form-group">
                        <label>CPF do Servidor</label>
                        <input type="text" id="portal-cpf" value="123.456.789-00" />
                    </div>
                    <div class="people-form-group">
                        <label>Senha</label>
                        <input type="password" id="portal-pwd" value="MinhaSenhaSegura2026" />
                    </div>
                    <div style="display:flex;gap:10px;">
                        <button class="people-btn" data-module-click="people-91" >Testar Login</button>
                        <button class="people-btn secondary" data-module-click="people-92" >Gerar Contracheque com QR Code</button>
                    </div>
                    <div id="portal-auth-result" style="margin-top:14px;"></div>
                </div>

                <div class="people-card">
                    <h3>Triagem de Atualizações Cadastrais pelo RH</h3>
                    <p style="font-size:12px;color:var(--muted);margin-bottom:14px;">Validação ou rejeição de solicitações de alteração enviadas pelo servidor com comprovantes.</p>
                    <button class="people-btn secondary" data-module-click="people-93" >Atualizar Lista de Pendências</button>
                    <div id="portal-pending-list" style="margin-top:14px;">
                        <div style="font-size:13px;color:var(--muted);">Clique acima para carregar pendências.</div>
                    </div>
                </div>
            </div>
        `;
    }

    // ── Aba 6: eSocial S-1.3 & SST ──────────────────────────────────────
    async function renderEsocialSstTab(container) {
        container.innerHTML = `
            <div class="people-grid">
                <div class="people-card">
                    <h3>eSocial S-1.3 · Totalizadores & Qualificação</h3>
                    <p style="font-size:12px;color:var(--muted);margin-bottom:14px;">Diagnóstico de qualificação cadastral e totalizadores sintéticos de INSS, FGTS e IRRF.</p>
                    <div style="display:flex;gap:10px;margin-bottom:14px;">
                        <button class="people-btn secondary" data-module-click="people-94" >Diagnóstico Cadastral</button>
                        <button class="people-btn" data-module-click="people-95" >Totalizadores de Encargos</button>
                    </div>
                    <div id="esocial-diag-results"></div>
                </div>

                <div class="people-card">
                    <h3>Saúde e Segurança do Trabalho (SST & CAT)</h3>
                    <p style="font-size:12px;color:var(--muted);margin-bottom:14px;">Emissão de CAT (Acidente de Trabalho), Perfil Profissiográfico Previdenciário (PPP) e EPIs com CA.</p>
                    <div style="display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap;">
                        <button class="people-btn danger" data-module-click="people-96" >Emitir CAT</button>
                        <button class="people-btn secondary" data-module-click="people-97" >Emissão de PPP</button>
                        <button class="people-btn secondary" data-module-click="people-98" >Catálogo de EPIs (CA)</button>
                    </div>
                    <div id="sst-results"></div>
                </div>
            </div>
        `;
    }

    // ── Ações Globais e Handlers ─────────────────────────────────────────

    window.executeSalarySimulation = async function() {
        const title = document.getElementById('sim-title').value;
        const mode = document.getElementById('sim-mode').value;
        const value = parseFloat(document.getElementById('sim-value').value);
        const resEl = document.getElementById('sim-results');
        resEl.innerHTML = '<div class="loader"></div>';

        try {
            const data = await apiCall('/api/people/adjustments/simulate', 'POST', { title, mode, value });
            resEl.innerHTML = `
                <div class="people-card" style="background:var(--surface);border-color:var(--accent);">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <strong>${esc(data.title)}</strong>
                        <span class="people-badge success">SIMULADO</span>
                    </div>
                    <p style="margin:8px 0 4px 0;font-size:12px;">Servidores Impactados: <strong>${data.impacted_count}</strong></p>
                    <p style="margin:4px 0;font-size:12px;">Custo Anterior: <strong>${fmtMoney(data.total_old_cost)}</strong></p>
                    <p style="margin:4px 0;font-size:12px;">Novo Custo: <strong>${fmtMoney(data.total_new_cost)}</strong></p>
                    <p style="margin:4px 0;font-size:13px;color:var(--accent);font-weight:700;">Diferença Mensal: +${fmtMoney(data.difference)}</p>
                    <button class="people-btn" style="margin-top:10px;" data-module-click="people-99" data-arg0="${ModulesUI.escape(data.id)}">Efetivar Reajuste na Base</button>
                </div>
            `;
        } catch (e) {
            resEl.innerHTML = `<div style="color:var(--danger);font-size:12px;">Erro: ${esc(e.message)}</div>`;
        }
    };

    window.applySalaryAdjustment = async function(id) {
        if (!confirm('Deseja efetivar este reajuste salarial em definitivo em toda a base de servidores?')) return;
        try {
            await apiCall('/api/people/adjustments/apply', 'POST', { adjustment_id: id });
            alert('Reajuste salarial efetivado com sucesso!');
            switchPeopleTab('employees');
        } catch (e) {
            alert('Erro ao efetivar: ' + e.message);
        }
    };

    window.togglePayrollLock = async function(lock) {
        const comp = document.getElementById('lock-comp').value;
        const statusEl = document.getElementById('lock-status');
        try {
            const url = lock ? '/api/people/payroll/lock' : '/api/people/payroll/unlock';
            const data = await apiCall(url, 'POST', { competence: comp });
            statusEl.innerHTML = `
                <div class="people-badge ${data.is_locked ? 'danger' : 'success'}" style="padding:6px 12px;font-size:12px;">
                    ${data.is_locked ? 'Folha de ' + comp + ' BLOQUEADA para edições' : 'Folha de ' + comp + ' DESBLOQUEADA'}
                </div>
            `;
        } catch (e) {
            statusEl.innerHTML = `<div style="color:var(--danger);font-size:12px;">Erro: ${esc(e.message)}</div>`;
        }
    };

    window.calculateProvisions = async function() {
        const comp = document.getElementById('lock-comp').value || '2026-03';
        const resEl = document.getElementById('provisions-results');
        resEl.innerHTML = '<div class="loader"></div>';
        try {
            const data = await apiCall('/api/people/payroll/provisions', 'POST', { competence: comp });
            resEl.innerHTML = `
                <table class="people-table" style="margin-top:8px;">
                    <thead>
                        <tr><th>Provisão</th><th>Mensal</th><th>Encargos (22%)</th><th>Total</th></tr>
                    </thead>
                    <tbody>
                        ${data.provisions.map(p => `
                            <tr>
                                <td><strong>${esc(p.provision_type)}</strong></td>
                                <td>${fmtMoney(p.monthly_accrual)}</td>
                                <td>${fmtMoney(p.patronal_charges)}</td>
                                <td><strong>${fmtMoney(p.total_balance)}</strong></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } catch (e) {
            resEl.innerHTML = `<div style="color:var(--danger);font-size:12px;">Erro: ${esc(e.message)}</div>`;
        }
    };

    window.executeEconsignadoImport = async function() {
        const fname = document.getElementById('econ-file').value;
        const fmt = document.getElementById('econ-format').value;
        const resEl = document.getElementById('econ-results');
        resEl.innerHTML = '<div class="loader"></div>';

        const sampleRecords = [
            { matricula: 'EMP-01', cpf: '123.456.789-00', nome: 'Maria da Silva Pereira', valor: 250.00, evento: 'DESC-CONSIGNADO' },
            { matricula: 'EMP-02', cpf: '234.567.890-11', nome: 'João Carlos Oliveira', valor: 99999.00, evento: 'DESC-CONSIGNADO' }
        ];

        try {
            const data = await apiCall('/api/people/consignments/econsignado/import', 'POST', {
                file_name: fname,
                format: fmt,
                records: sampleRecords
            });
            resEl.innerHTML = `
                <div class="people-card" style="background:var(--surface);margin-top:10px;">
                    <div style="font-weight:700;margin-bottom:6px;">Lote ${esc(data.file_name)} Concluído</div>
                    <div style="font-size:12px;display:flex;gap:12px;margin-bottom:10px;">
                        <span>Total: <strong>${data.total_records}</strong></span>
                        <span style="color:#27ae60;">Importados: <strong>${data.imported_records}</strong></span>
                        <span style="color:#c0392b;">Rejeitados: <strong>${data.rejected_records}</strong></span>
                    </div>
                    <div style="font-size:11px;color:var(--muted);">Inconsistências registradas em relatório analítico de críticas.</div>
                </div>
            `;
        } catch (e) {
            resEl.innerHTML = `<div style="color:var(--danger);font-size:12px;">Erro: ${esc(e.message)}</div>`;
        }
    };

    window.simulateHealthPlan = async function() {
        const resEl = document.getElementById('hp-results');
        resEl.innerHTML = '<div class="loader"></div>';
        try {
            const data = await apiCall('/api/people/health-plans/calculate', 'POST', { employee_id: 1, operator_code: 'MED-UNIMED', age: 35 });
            resEl.innerHTML = `
                <div style="font-size:12px;background:var(--surface);padding:10px;border-radius:6px;border:1px solid var(--line);">
                    <div>Operadora: <strong>${esc(data.operator_name)}</strong></div>
                    <div>Mensalidade Total: <strong>${fmtMoney(data.monthly_total)}</strong></div>
                    <div>Participação Prefeitura (50%): <strong style="color:#27ae60;">${fmtMoney(data.entity_coparticipation)}</strong></div>
                    <div>Desconto Servidor: <strong style="color:#c0392b;">${fmtMoney(data.employee_discount)}</strong></div>
                </div>
            `;
        } catch (e) {
            resEl.innerHTML = `<div style="color:var(--danger);font-size:12px;">Erro: ${esc(e.message)}</div>`;
        }
    };

    window.simulateTransportVoucher = async function() {
        const resEl = document.getElementById('trans-results');
        resEl.innerHTML = '<div class="loader"></div>';
        try {
            const data = await apiCall('/api/people/transports/calculate', 'POST', { employee_id: 1, line_id: 1, daily_trips: 2, working_days: 22 });
            resEl.innerHTML = `
                <div style="font-size:12px;background:var(--surface);padding:10px;border-radius:6px;border:1px solid var(--line);">
                    <div>Linha: <strong>${esc(data.line_name)}</strong></div>
                    <div>Custo Total: <strong>${fmtMoney(data.monthly_total_cost)}</strong></div>
                    <div>Desconto Servidor (Teto 6%): <strong style="color:#c0392b;">${fmtMoney(data.employee_deduction_6pct_cap)}</strong></div>
                    <div>Subsídio Municipal: <strong style="color:#27ae60;">${fmtMoney(data.entity_burden)}</strong></div>
                </div>
            `;
        } catch (e) {
            resEl.innerHTML = `<div style="color:var(--danger);font-size:12px;">Erro: ${esc(e.message)}</div>`;
        }
    };

    window.emitRppsGuide = async function() {
        const resEl = document.getElementById('rpps-guide-result');
        resEl.innerHTML = '<div class="loader"></div>';
        try {
            const data = await apiCall('/api/people/rpps/guide', 'POST', { fund_code: 'RPPS-PREVI', competence: '2026-03' });
            resEl.innerHTML = `
                <div class="people-card" style="background:var(--surface);border-color:var(--accent);margin-top:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <strong>Guia de Recolhimento Previdenciário</strong>
                        <span class="people-badge success">EMITIDA</span>
                    </div>
                    <p style="margin:6px 0;font-size:12px;">Fundo: <strong>${esc(data.fund_name)}</strong></p>
                    <p style="margin:4px 0;font-size:12px;">Valor Total da Guia: <strong style="font-size:15px;color:var(--accent);">${fmtMoney(data.total_guide)}</strong></p>
                    <p style="margin:4px 0;font-size:12px;">Linha Digitável / Código de Barras:</p>
                    <code style="display:block;background:var(--panel);padding:6px;font-size:11px;border-radius:4px;border:1px solid var(--line);">${esc(data.barcode)}</code>
                </div>
            `;
        } catch (e) {
            resEl.innerHTML = `<div style="color:var(--danger);font-size:12px;">Erro: ${esc(e.message)}</div>`;
        }
    };

    window.executeSisobiConfront = async function() {
        const resEl = document.getElementById('sisobi-results');
        resEl.innerHTML = '<div class="loader"></div>';
        try {
            const data = await apiCall('/api/people/sisobi/confront', 'POST', {
                filename: 'SISOBI_2026_MARCO.TXT',
                records: [
                    { cpf: '123.456.789-00', nome: 'Servidor Teste', data_obito: '2026-03-01' }
                ]
            });
            resEl.innerHTML = `
                <div class="people-card" style="background:var(--surface);margin-top:10px;">
                    <div style="font-weight:700;color:var(--danger);margin-bottom:6px;">Cruzamento Concluído</div>
                    <div style="font-size:12px;">Registros Lidos: <strong>${data.total_imported}</strong></div>
                    <div style="font-size:12px;">Óbitos Localizados na Base: <strong>${data.deaths_detected}</strong></div>
                    <div style="font-size:12px;color:var(--danger);margin-top:4px;">Servidores Bloqueados Preventivamente: <strong>${data.active_employees_blocked}</strong></div>
                </div>
            `;
        } catch (e) {
            resEl.innerHTML = `<div style="color:var(--danger);font-size:12px;">Erro: ${esc(e.message)}</div>`;
        }
    };

    window.testPortalAuth = async function() {
        const cpf = document.getElementById('portal-cpf').value;
        const pwd = document.getElementById('portal-pwd').value;
        const resEl = document.getElementById('portal-auth-result');
        resEl.innerHTML = '<div class="loader"></div>';
        try {
            const data = await apiCall('/api/people/portal/auth', 'POST', { cpf, password: pwd });
            resEl.innerHTML = `
                <div class="people-badge success" style="padding:6px 12px;font-size:12px;">
                    Autenticado com Sucesso: ${esc(data.nome)} (Matrícula: ${esc(data.matricula)})
                </div>
            `;
        } catch (e) {
            resEl.innerHTML = `<div style="color:var(--danger);font-size:12px;">Erro: ${esc(e.message)}</div>`;
        }
    };

    window.generateQrPayslip = async function() {
        const resEl = document.getElementById('portal-auth-result');
        resEl.innerHTML = '<div class="loader"></div>';
        try {
            const data = await apiCall('/api/people/portal/payslip/qr', 'POST', { employee_id: 1, competence: '2026-03', net_value: 3680.50 });
            resEl.innerHTML = `
                <div class="people-qr-box">
                    <div style="font-size:32px;margin-bottom:6px;">[QR CODE]</div>
                    <strong>Autenticidade Digital Garantida</strong>
                    <div style="font-size:12px;color:var(--muted);margin-top:4px;">Chave HMAC:</div>
                    <code>${esc(data.token)}</code>
                    <a href="${esc(data.verify_url)}" target="_blank" style="display:inline-block;margin-top:8px;font-size:12px;color:var(--accent);">Validar Certificado Digitalmente</a>
                </div>
            `;
        } catch (e) {
            resEl.innerHTML = `<div style="color:var(--danger);font-size:12px;">Erro: ${esc(e.message)}</div>`;
        }
    };

    window.runEsocialDiagnosis = async function() {
        const resEl = document.getElementById('esocial-diag-results');
        resEl.innerHTML = '<div class="loader"></div>';
        try {
            const data = await apiCall('/api/people/esocial/diagnosis');
            resEl.innerHTML = `
                <div style="font-size:12px;background:var(--surface);padding:12px;border-radius:6px;border:1px solid var(--line);">
                    <div>Total de Servidores Avaliados: <strong>${data.total_avaliados}</strong></div>
                    <div>Conformes: <strong style="color:#27ae60;">${data.qualificados_ok}</strong></div>
                    <div>Taxa de Qualificação eSocial: <strong style="color:var(--accent);font-size:14px;">${data.taxa_conformidade_pct}%</strong></div>
                </div>
            `;
        } catch (e) {
            resEl.innerHTML = `<div style="color:var(--danger);font-size:12px;">Erro: ${esc(e.message)}</div>`;
        }
    };

    window.runEsocialTotalizers = async function() {
        const resEl = document.getElementById('esocial-diag-results');
        resEl.innerHTML = '<div class="loader"></div>';
        try {
            const data = await apiCall('/api/people/esocial/totalizers', 'POST', { competence: '2026-03' });
            resEl.innerHTML = `
                <div style="font-size:12px;background:var(--surface);padding:12px;border-radius:6px;border:1px solid var(--line);">
                    <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                        <strong>Conciliação Sintética eSocial S-1.3</strong>
                        <span class="people-badge success">100% CONCILIADO</span>
                    </div>
                    <div>INSS Sistema × Retorno eSocial: <strong>${fmtMoney(data.inss_apurado_sistema)}</strong></div>
                    <div>IRRF Sistema × Retorno eSocial: <strong>${fmtMoney(data.irrf_apurado_sistema)}</strong></div>
                    <div>Divergências Identificadas: <strong>${data.divergencias}</strong></div>
                </div>
            `;
        } catch (e) {
            resEl.innerHTML = `<div style="color:var(--danger);font-size:12px;">Erro: ${esc(e.message)}</div>`;
        }
    };

    // ── Interceptação da Página ERP ──────────────────────────────────────
    const originalErpPage = window.erpPage;
    window.erpPage = async function(module) {
        if (module !== 'people') {
            return await originalErpPage(module);
        }

        const peopleHtml = `
            <div class="people-container module-workspace">
                <div class="people-header">
                    <div class="people-title">
                        <h1>Gestão de Pessoas, Folha, Previdência e SST</h1>
                        <p>Plataforma integrada de RH, RPPS RioPrevi, eConsignado, Portal do Servidor, eSocial S-1.3 e Medicina do Trabalho.</p>
                    </div>
                </div>

                <div class="people-tabs">
                    <button class="people-tab-btn active" data-tab="employees" data-module-click="people-100" >Servidores & Vagas</button>
                    <button class="people-tab-btn" data-tab="payroll" data-module-click="people-101" >Folha & Simulações</button>
                    <button class="people-tab-btn" data-tab="consignments" data-module-click="people-102" >Consignações & Benefícios</button>
                    <button class="people-tab-btn" data-tab="rpps_sisobi" data-module-click="people-103" >RPPS & SISOBI</button>
                    <button class="people-tab-btn" data-tab="portal" data-module-click="people-104" >Portal do Servidor</button>
                    <button class="people-tab-btn" data-tab="esocial_sst" data-module-click="people-105" >eSocial S-1.3 & SST</button>
                </div>

                <div id="people-tab-content">
                    <div style="padding:40px;text-align:center;color:var(--muted);"><div class="loader"></div> Carregando Gestão de Pessoas...</div>
                </div>
            </div>
        `;

        setTimeout(async () => {
            const container = document.getElementById('people-tab-content');
            if (container) {
                await renderEmployeesTab(container);
            }
        }, 50);

        return peopleHtml;
    };

})();
