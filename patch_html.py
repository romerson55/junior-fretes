import os
import re

file_path = r"c:\Users\jorgin do grau\Desktop\projetos junior\sistema teste\index.html"
with open(file_path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Add agenda page back and history filters
page_agenda = """
        <!-- PAGE: AGENDA -->
        <div id="page-agenda" class="page">
            <div class="section-title" style="display: flex; justify-content: space-between; align-items: center;">
                <span><i class="fas fa-calendar-alt"></i> Agendamentos</span>
                <button onclick="openAgendaModal()" style="background: var(--primary); color: #000; border: none; padding: 5px 15px; border-radius: 8px; font-weight: bold; cursor: pointer;">+ Agendar</button>
            </div>
            <div class="activity-list" id="agendaList">
                <p style="text-align: center; color: var(--text-muted); padding: 20px;">Carregando...</p>
            </div>
        </div>

        <!-- PAGE: HISTORICO -->
"""
html = html.replace('<!-- PAGE: HISTORICO -->', page_agenda)

history_filters = """
        <!-- PAGE: HISTORICO -->
        <div id="page-history" class="page">
            <div class="section-title">
                <i class="fas fa-list-ul"></i> Histórico Completo
            </div>
            <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                <input type="date" id="historyDateStart" style="flex: 1; background: var(--card-bg); color: #fff; border: 1px solid var(--glass-border); padding: 10px; border-radius: 12px; outline: none;" onchange="renderHistory()">
                <input type="date" id="historyDateEnd" style="flex: 1; background: var(--card-bg); color: #fff; border: 1px solid var(--glass-border); padding: 10px; border-radius: 12px; outline: none;" onchange="renderHistory()">
            </div>
            <div class="activity-list" id="fullHistory">
"""
html = html.replace("""<!-- PAGE: HISTORICO -->
        <div id="page-history" class="page">
            <div class="section-title">
                <i class="fas fa-list-ul"></i> Histórico Completo
            </div>
            <div class="activity-list" id="fullHistory">""", history_filters)

# 2. Add agenda nav item back
nav_agenda = """
        <a href="#" class="nav-item" onclick="showPage('agenda')" id="nav-agenda">
            <i class="fas fa-calendar-check"></i>
            <span>Agenda</span>
        </a>
"""
html = html.replace("""        <a href="#" class="nav-item" onclick="showPage('config')" id="nav-config">""", nav_agenda + """        <a href="#" class="nav-item" onclick="showPage('config')" id="nav-config">""")

# 3. Add client selection to the Lançamento modal
client_select = """
                <div class="form-group" id="groupCliente" style="display: none;">
                    <label>Cliente Fixo (Opcional)</label>
                    <div style="display: flex; gap: 10px;">
                        <select id="entryCliente" style="flex: 1; background: rgba(255, 255, 255, 0.05); border: 1px solid var(--glass-border); padding: 15px; border-radius: 12px; color: #fff;">
                            <option style="background-color: #0f172a; color: #fff;" value="">Sem Cliente...</option>
                        </select>
                        <button type="button" onclick="novoCliente()" style="background: var(--glass); color: #fff; border: 1px solid var(--glass-border); border-radius: 12px; padding: 0 15px; font-weight: bold; font-size: 1.2rem;">+</button>
                    </div>
                </div>
"""
html = html.replace("""                <div class="form-group">
                    <label>Descrição</label>""", client_select + """                <div class="form-group">
                    <label>Descrição</label>""")

# 4. Add Agenda Modal content
modals = """
    <!-- Modal Agenda -->
    <div class="overlay" id="agendaOverlay">
        <div class="modal">
            <div class="modal-header">
                <h3>Novo Agendamento</h3>
                <button class="close-modal" onclick="closeAgendaModal()">&times;</button>
            </div>
            <form id="agendaForm">
                <div class="form-group">
                    <label>Data</label>
                    <input type="date" id="agendaData" required>
                </div>
                <div class="form-group">
                    <label>Hora</label>
                    <input type="time" id="agendaHora">
                </div>
                <div class="form-group">
                    <label>Cliente (Opcional)</label>
                    <div style="display: flex; gap: 10px;">
                        <select id="agendaClienteSelect" style="flex: 1; background: rgba(255, 255, 255, 0.05); border: 1px solid var(--glass-border); padding: 15px; border-radius: 12px; color: #fff;">
                            <option style="background-color: #0f172a; color: #fff;" value="">Selecione...</option>
                        </select>
                        <button type="button" onclick="novoCliente()" style="background: var(--glass); color: #fff; border: 1px solid var(--glass-border); border-radius: 12px; padding: 0 15px; font-weight: bold; font-size: 1.2rem;">+</button>
                    </div>
                </div>
                <div class="form-group">
                    <label>Detalhes (Destino / Mercadoria)</label>
                    <input type="text" id="agendaDetalhes" placeholder="Ex: Buscar cama no Centro">
                </div>
                <div class="form-group">
                    <label>Valor Combinado (R$)</label>
                    <input type="number" id="agendaValor" step="0.01" placeholder="0,00">
                </div>
                <button type="submit" class="submit-btn" style="width: 100%; background: var(--primary); color: #000; padding: 15px; border-radius: 12px; font-weight: bold; border: none; cursor: pointer;">Agendar</button>
            </form>
        </div>
    </div>
"""
html = html.replace("    <script>", modals + "    <script>")

# 5. Add UI logic for rendering clients, agenda, and handling state in JS
js_logic = """
        let API_URL = localStorage.getItem('junior_fretes_api') || "https://script.google.com/macros/s/AKfycbx9Wd6oifGtYFdKr8jLxDUjpURpgQBOwkpj2rLFmKGKlOxyDm_yean7eTbZJCP-_yEz/exec";

        let transacoes = [];
        let entradas = [];
        let saidas = [];
        let clientes = [];
        let agenda = [];
        let isLoading = false;

        document.addEventListener('DOMContentLoaded', () => {
            document.getElementById('apiUrlInput').value = API_URL;
            syncData();

            document.getElementById('entryForm').addEventListener('submit', handleEntrySubmit);
            document.getElementById('agendaForm').addEventListener('submit', handleAgendaSubmit);

            // Hook into entryCategory change to show/hide client
            document.getElementById('entryCategory').addEventListener('change', (e) => {
                const groupCliente = document.getElementById('groupCliente');
                groupCliente.style.display = (e.target.value === 'Frete' || e.target.value === 'Agendamento') ? 'block' : 'none';
            });

            // Interval setup for polling
            setInterval(syncData, 60000); // Sync every minute
            
            // Set today on history start date by default
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('historyDateStart').value = today;
            document.getElementById('historyDateEnd').value = today;
        });

        async function syncData() {
            if (isLoading) return;
            showLoader(true);
            try {
                const resp = await fetch(`${API_URL}?op=ler&t=${Date.now()}`);
                const data = await resp.json();

                if (data.sucesso) {
                    entradas = data.entradas || [];
                    saidas = data.saidas || [];
                    clientes = data.clientes || [];
                    agenda = data.agenda || [];
                    
                    renderDashboard();
                    renderHistory();
                    renderAgenda();
                    populateClientes();
                    
                    document.getElementById('systemStatus').textContent = "Atualizado: " + new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
                }
            } catch (e) {
                console.error(e);
                document.getElementById('systemStatus').textContent = "Erro na sincronização";
            } finally {
                showLoader(false);
            }
        }
        
        function populateClientes() {
            const entrySelect = document.getElementById('entryCliente');
            const agendaSelect = document.getElementById('agendaClienteSelect');
            
            let htmlOptions = '<option style="background-color: #0f172a; color: #fff;" value="">Sem Cliente...</option>';
            clientes.sort((a,b)=> a.nome.localeCompare(b.nome)).forEach(c => {
                htmlOptions += `<option style="background-color: #0f172a; color: #fff;" value="${c.nome}">${c.nome}</option>`;
            });
            
            if (entrySelect.options.length !== clientes.length + 1) {
                const prevEntry = entrySelect.value;
                const prevAgenda = agendaSelect.value;
                entrySelect.innerHTML = htmlOptions;
                agendaSelect.innerHTML = htmlOptions;
                if(prevEntry) entrySelect.value = prevEntry;
                if(prevAgenda) agendaSelect.value = prevAgenda;
            }
        }

        async function novoCliente() {
            const nome = prompt("Nome do Cliente:");
            if (!nome) return;
            
            showLoader(true);
            try {
                const resp = await fetch(API_URL, {
                    method: 'POST',
                    body: JSON.stringify({
                        op: 'criarCliente',
                        nome: nome
                    })
                });
                const result = await resp.json();
                if (result.sucesso) {
                    alert('Cliente salvo!');
                    syncData();
                }
            } catch (err) {
                alert('Erro ao salvar cliente');
            } finally {
                showLoader(false);
            }
        }

        function renderAgenda() {
            const list = document.getElementById('agendaList');
            if (!list) return;
            
            if (agenda.length === 0 || agenda.filter(a => a.status === 'PENDENTE').length === 0) {
                list.innerHTML = '<p style="text-align: center; color: var(--text-muted); padding: 20px;">Nenhum agendamento pendente.</p>';
                return;
            }
            
            list.innerHTML = '';
            
            // Sort by date/time
            agenda.filter(a => a.status === 'PENDENTE').sort((a, b) => {
                const dateA = a.data.split('/').reverse().join('-') + 'T' + (a.hora || '00:00');
                const dateB = b.data.split('/').reverse().join('-') + 'T' + (b.hora || '00:00');
                return dateA.localeCompare(dateB);
            }).forEach(item => {
                const div = document.createElement('div');
                div.className = 'activity-item';
                div.style.alignItems = 'flex-start';
                
                let isToday = false;
                try {
                    const parts = item.data.split('/');
                    if (parts.length >= 3) { // fix possible parsing bugs
                       const d = new Date(parts[2], parts[1]-1, parts[0]);
                       const t = new Date();
                       if(d.getDate() === t.getDate() && d.getMonth() === t.getMonth() && d.getFullYear() === t.getFullYear()) isToday = true;
                    }
                }catch(e){}

                div.innerHTML = `
                    <div class="activity-icon" style="background: ${isToday ? 'rgba(255,215,0,0.2)' : 'rgba(59, 130, 246, 0.1)'}; color: ${isToday ? 'var(--primary)' : 'var(--info)'}; flex-shrink: 0;">
                        <i class="fas fa-calendar-day"></i>
                    </div>
                    <div class="activity-info" style="flex: 1;">
                        <h4 style="color: ${isToday ? 'var(--primary)' : 'inherit'};">${isToday ? 'HOJE - ' : ''}${item.data} ${item.hora ? 'às '+item.hora : ''}</h4>
                        <p style="font-size: 0.9rem; color: #fff; margin: 4px 0;">${item.cliente || 'Sem cliente associado'}</p>
                        <p style="color: var(--text-muted); font-size: 0.8rem;">${item.endereco}</p>
                        <p style="color: var(--success); font-weight: bold; margin-top: 5px;">R$ ${parseFloat(item.valor||0).toFixed(2)}</p>
                    </div>
                    <div style="display:flex; flex-direction:column; gap:5px;">
                        <button onclick="concluirAgenda('${item.id}', '${item.cliente}', '${parseFloat(item.valor||0)}', '${item.endereco}')" style="background: var(--success); color: #fff; border: none; padding: 12px; border-radius: 8px; cursor: pointer;"><i class="fas fa-check"></i></button>
                        <button onclick="excluirAgenda('${item.id}')" style="background: var(--danger); color: #fff; border: none; padding: 12px; border-radius: 8px; cursor: pointer;"><i class="fas fa-trash"></i></button>
                    </div>
                `;
                list.appendChild(div);
            });
        }
        
        async function concluirAgenda(id, cliente, valor, detalhes) {
            if(!confirm("Marcar como Concluído e já lançar o valor no Caixa como Frete?")) return;
            showLoader(true);
            try {
                // First conclude
                await fetch(API_URL, {
                    method: 'POST',
                    body: JSON.stringify({ op: 'concluirAgendamento', id: id })
                });
                
                // Then launch
                await fetch(API_URL, {
                    method: 'POST',
                    body: JSON.stringify({
                        op: 'registrarFluxo',
                        tipo: 'entrada',
                        descricao: detalhes + (cliente !== 'null' ? ' - ' + cliente : ''),
                        valor: parseFloat(valor),
                        metodo: 'PIX', // default
                        categoria: 'Frete'
                    })
                });
                
                alert("Concluído e lançado com sucesso!");
                syncData();
            } catch(e) {
                alert("Erro ao concluir");
            } finally {
                showLoader(false);
            }
        }
        
        async function excluirAgenda(id) {
            if(!confirm("Excluir agendamento?")) return;
            showLoader(true);
            try {
                 await fetch(API_URL, {
                    method: 'POST',
                    body: JSON.stringify({ op: 'excluirAgendamento', id: id })
                });
                syncData();
            } catch(e) {
                alert("Erro ao excluir");
            } finally {
                showLoader(false);
            }
        }

        function openAgendaModal() {
            document.getElementById('agendaOverlay').style.display = 'flex';
            document.getElementById('agendaData').value = new Date().toISOString().split('T')[0];
            document.getElementById('agendaHora').value = '';
            document.getElementById('agendaDetalhes').value = '';
            document.getElementById('agendaValor').value = '';
            document.getElementById('agendaClienteSelect').value = '';
        }

        function closeAgendaModal() {
            document.getElementById('agendaOverlay').style.display = 'none';
        }

        async function handleAgendaSubmit(e) {
            e.preventDefault();
            const dataStr = document.getElementById('agendaData').value;
            const hora = document.getElementById('agendaHora').value;
            const det = document.getElementById('agendaDetalhes').value;
            const val = document.getElementById('agendaValor').value;
            const cliente = document.getElementById('agendaClienteSelect').value;

            if (!dataStr || !det) return alert('Preecha data e detalhes');

            // convert yyyy-mm-dd to dd/mm/yyyy
            const dParts = dataStr.split('-');
            const finalData = `${dParts[2]}/${dParts[1]}/${dParts[0]}`;

            showLoader(true);
            closeAgendaModal();

            try {
                const resp = await fetch(API_URL, {
                    method: 'POST',
                    body: JSON.stringify({
                        op: 'agendar',
                        data: finalData,
                        hora: hora,
                        cliente: cliente,
                        endereco: det,
                        valor: parseFloat(val||0)
                    })
                });
                const result = await resp.json();
                if (result.sucesso) {
                    syncData();
                }
            } catch (err) {
                alert('Erro ao agendar');
            } finally {
                showLoader(false);
            }
        }
"""
html = html.replace("""        let API_URL = localStorage.getItem('junior_fretes_api') || "https://script.google.com/macros/s/AKfycbx9Wd6oifGtYFdKr8jLxDUjpURpgQBOwkpj2rLFmKGKlOxyDm_yean7eTbZJCP-_yEz/exec";

        let transacoes = [];
        let entradas = [];
        let saidas = [];
        let isLoading = false;

        document.addEventListener('DOMContentLoaded', () => {
            document.getElementById('apiUrlInput').value = API_URL;
            syncData();

            document.getElementById('entryForm').addEventListener('submit', handleEntrySubmit);

            // Interval setup for polling
            setInterval(syncData, 60000); // Sync every minute
        });

        async function syncData() {
            if (isLoading) return;
            showLoader(true);
            try {
                const resp = await fetch(`${API_URL}?op=ler&t=${Date.now()}`);
                const data = await resp.json();

                if (data.sucesso) {
                    entradas = data.entradas || [];
                    saidas = data.saidas || [];
                    renderDashboard();
                    renderHistory();
                    document.getElementById('systemStatus').textContent = "Atualizado: " + new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
                }
            } catch (e) {
                console.error(e);
                document.getElementById('systemStatus').textContent = "Erro na sincronização";
            } finally {
                showLoader(false);
            }
        }""", js_logic)

# Update renderHistory for the date filters
render_history = """        function renderHistory() {
            const startStr = document.getElementById('historyDateStart').value; // yyyy-mm-dd
            const endStr = document.getElementById('historyDateEnd').value;

            let all = [
                ...entradas.map(e => ({ ...e, type: 'in' })),
                ...saidas.map(s => ({ ...s, type: 'out' }))
            ].sort((a, b) => parseDate(b.data) - parseDate(a.data));

            // Filtering
            if (startStr || endStr) {
                const sDate = startStr ? new Date(startStr + 'T00:00:00') : new Date(0);
                const eDate = endStr ? new Date(endStr + 'T23:59:59') : new Date(9999, 0, 1);
                
                all = all.filter(item => {
                    const d = parseDate(item.data);
                    return d >= sDate && d <= eDate;
                });
            }

            const list = document.getElementById('fullHistory');
            list.innerHTML = '';

            if(all.length === 0) {
                 list.innerHTML = '<p style="text-align: center; color: var(--text-muted); padding: 20px;">Nenhuma atividade no período selecionado.</p>';
            }

            all.forEach(item => {
                list.appendChild(createActivityItem(item));
            });
        }"""
html = html.replace("""        function renderHistory() {
            const all = [
                ...entradas.map(e => ({ ...e, type: 'in' })),
                ...saidas.map(s => ({ ...s, type: 'out' }))
            ].sort((a, b) => parseDate(b.data) - parseDate(a.data));

            const list = document.getElementById('fullHistory');
            list.innerHTML = '';

            all.forEach(item => {
                list.appendChild(createActivityItem(item));
            });
        }""", render_history)


# Expanding handleEntrySubmit 
handle_entry = """        async function handleEntrySubmit(e) {
            e.preventDefault();
            const type = document.getElementById('entryType').value;
            let desc = document.getElementById('entryDesc').value;
            const value = document.getElementById('entryValue').value;
            const category = document.getElementById('entryCategory').value;
            const method = document.getElementById('entryMethod').value;
            const cliente = document.getElementById('entryCliente').value;

            if (category === 'Frete' && cliente) {
                 desc = desc ? (desc + ' - ' + cliente) : ('Frete ' + cliente);
            }

            if (!desc || !value) return alert('Preecha os campos obrigatórios');

            showLoader(true);
"""
html = html.replace("""        async function handleEntrySubmit(e) {
            e.preventDefault();
            const type = document.getElementById('entryType').value;
            const desc = document.getElementById('entryDesc').value;
            const value = document.getElementById('entryValue').value;
            const category = document.getElementById('entryCategory').value;
            const method = document.getElementById('entryMethod').value;

            if (!desc || !value) return alert('Preecha os campos obrigatórios');

            showLoader(true);""", handle_entry)

# openModal helper change
open_mod = """        function openModal(type, category = '') {
            document.getElementById('entryType').value = type;
            document.getElementById('entryOverlay').style.display = 'flex';
            document.getElementById('modalTitle').textContent = type === 'entrada' ? 'Novo Ganho' : 'Novo Gasto';
            document.getElementById('groupMetodo').style.display = type === 'entrada' ? 'block' : 'none';

            if (category) {
                document.getElementById('entryCategory').value = category;
                document.getElementById('entryDesc').value = category + " " + new Date().toLocaleDateString('pt-BR');
            } else {
                document.getElementById('entryCategory').value = 'Outros';
                document.getElementById('entryDesc').value = '';
            }
            
            const groupCliente = document.getElementById('groupCliente');
            groupCliente.style.display = (document.getElementById('entryCategory').value === 'Frete') ? 'block' : 'none';

            document.getElementById('entryValue').value = '';
        }"""
html = html.replace("""        function openModal(type, category = '') {
            document.getElementById('entryType').value = type;
            document.getElementById('entryOverlay').style.display = 'flex';
            document.getElementById('modalTitle').textContent = type === 'entrada' ? 'Novo Ganho' : 'Novo Gasto';
            document.getElementById('groupMetodo').style.display = type === 'entrada' ? 'block' : 'none';

            if (category) {
                document.getElementById('entryCategory').value = category;
                document.getElementById('entryDesc').value = category + " " + new Date().toLocaleDateString('pt-BR');
            } else {
                document.getElementById('entryCategory').value = 'Outros';
                document.getElementById('entryDesc').value = '';
            }

            document.getElementById('entryValue').value = '';
        }""", open_mod)


# Fix Combustivel / Gasolina requests from user
html = html.replace("Gasolina", "Combustível")
html = html.replace("gasolina", "combustível")
html = html.replace("gas", "combustivel")
html = html.replace("fa-gas-pump", "fa-gas-pump")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(html)
