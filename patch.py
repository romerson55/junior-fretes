import json
import os

file_path = r"c:\Users\jorgin do grau\Desktop\projetos junior\sistema teste\index.html"
with open(file_path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Replace "Atividade Recente" on home with "Clientes"
home_recent_act = """            <!-- Recent activity -->
            <div class="section-title">
                <i class="fas fa-history"></i> Atividade Recente
            </div>
            <div class="activity-list" id="recentActivity">
                <!-- Items injected via JS -->
                <p style="text-align: center; color: var(--text-muted); padding: 20px;">Carregando dados...</p>
            </div>"""
home_clients = """            <!-- Clientes -->
            <div class="section-title" style="display: flex; justify-content: space-between; align-items: center;">
                <span><i class="fas fa-users"></i> Meus Clientes</span>
                <button onclick="openClienteModal()" style="background: var(--primary); color: #000; border: none; padding: 5px 15px; border-radius: 8px; font-weight: bold; cursor: pointer;">+ Cliente</button>
            </div>
            <div class="activity-list" id="homeClientList">
                <p style="text-align: center; color: var(--text-muted); padding: 20px;">Carregando...</p>
            </div>"""
html = html.replace(home_recent_act, home_clients)

# 2. Add Modal Cliente
modal_agenda = """    <!-- Modal Agenda -->"""
modal_cliente = """
    <!-- Modal Cliente -->
    <div class="overlay" id="clienteOverlay">
        <div class="modal">
            <div class="modal-header">
                <h3>Novo Cliente</h3>
                <button class="close-modal" onclick="closeClienteModal()">&times;</button>
            </div>
            <form id="clienteForm">
                <div class="form-group">
                    <label>Nome Completo (ou Empresa)</label>
                    <input type="text" id="clienteNome" required placeholder="Ex: Maria do Bolo">
                </div>
                <div class="form-group">
                    <label>WhatsApp</label>
                    <input type="text" id="clienteWhatsapp" placeholder="Ex: 11999999999" required>
                </div>
                <div class="form-group">
                    <label>CPF / CNPJ (Opcional)</label>
                    <input type="text" id="clienteCpf" placeholder="Apenas números">
                </div>
                <button type="submit" class="submit-btn" style="width: 100%; background: var(--primary); color: #000; padding: 15px; border-radius: 12px; font-weight: bold; border: none; cursor: pointer;">Salvar Cliente</button>
            </form>
        </div>
    </div>

    <!-- Modal Agenda -->"""
html = html.replace(modal_agenda, modal_cliente)

# 3. Handle novoCliente / renderDashboard updates
JS_DASHBOARD_OLD = """        function renderDashboard() {
            const totalIn = entradas.reduce((acc, curr) => acc + (parseFloat(curr.valor) || 0), 0);
            const totalOut = saidas.reduce((acc, curr) => acc + (parseFloat(curr.valor) || 0), 0);
            const balance = totalIn - totalOut;

            document.getElementById('currentBalance').textContent = formatCurrency(balance);
            document.getElementById('currentBalance').style.color = balance >= 0 ? 'var(--text)' : 'var(--danger)';
            document.getElementById('totalIn').textContent = formatCurrency(totalIn);
            document.getElementById('totalOut').textContent = formatCurrency(totalOut);

            // Recent Activity (combine and sort)
            const all = [
                ...entradas.map(e => ({ ...e, type: 'in' })),
                ...saidas.map(s => ({ ...s, type: 'out' }))
            ].sort((a, b) => parseDate(b.data) - parseDate(a.data)).slice(0, 10);

            const list = document.getElementById('recentActivity');
            if (list) {
                list.innerHTML = all.length ? '' : '<p style="text-align: center; color: var(--text-muted); padding: 20px;">Nenhuma atividade recente.</p>';

                all.forEach(item => {
                    list.appendChild(createActivityItem(item));
                });
            }
        }"""
        
JS_DASHBOARD_NEW = """        function renderDashboard() {
            const totalIn = entradas.reduce((acc, curr) => acc + (parseFloat(curr.valor) || 0), 0);
            const totalOut = saidas.reduce((acc, curr) => acc + (parseFloat(curr.valor) || 0), 0);
            const balance = totalIn - totalOut;

            document.getElementById('currentBalance').textContent = formatCurrency(balance);
            document.getElementById('currentBalance').style.color = balance >= 0 ? 'var(--text)' : 'var(--danger)';
            document.getElementById('totalIn').textContent = formatCurrency(totalIn);
            document.getElementById('totalOut').textContent = formatCurrency(totalOut);

            const clientList = document.getElementById('homeClientList');
            if(!clientList) return;
            clientList.innerHTML = clientes.length ? '' : '<p style="text-align: center; color: var(--text-muted); padding: 20px;">Nenhum cliente cadastrado.</p>';

            clientes.sort((a,b)=> a.nome.localeCompare(b.nome)).forEach(c => {
                const div = document.createElement('div');
                div.className = 'activity-item';
                
                const watsHtml = c.telefone ? `<a href="https://wa.me/55${c.telefone.replace(/\D/g, '')}" target="_blank" style="color: #25D366; font-size: 1.5rem; text-decoration: none;"><i class="fab fa-whatsapp"></i></a>` : '';
                
                div.innerHTML = `
                    <div class="activity-icon in" style="background: rgba(255, 255, 255, 0.1); color: #fff; flex-shrink: 0;">
                        <i class="fas fa-user"></i>
                    </div>
                    <div class="activity-info" style="flex: 1;">
                        <h4 style="color: #fff;">${c.nome}</h4>
                        <p style="font-size: 0.9rem; color: var(--text-muted); margin: 4px 0;">${c.telefone || 'Sem telefone'}</p>
                    </div>
                    ${watsHtml}
                `;
                clientList.appendChild(div);
            });
        }"""
# Using raw regex because the old might have slightly different spaces
old_dash_text = """        function renderDashboard() {
            const totalIn = entradas.reduce((acc, curr) => acc + (parseFloat(curr.valor) || 0), 0);
            const totalOut = saidas.reduce((acc, curr) => acc + (parseFloat(curr.valor) || 0), 0);
            const balance = totalIn - totalOut;

            document.getElementById('currentBalance').textContent = formatCurrency(balance);
            document.getElementById('currentBalance').style.color = balance >= 0 ? 'var(--text)' : 'var(--danger)';
            document.getElementById('totalIn').textContent = formatCurrency(totalIn);
            document.getElementById('totalOut').textContent = formatCurrency(totalOut);

            // Recent Activity (combine and sort)
            const all = [
                ...entradas.map(e => ({ ...e, type: 'in' })),
                ...saidas.map(s => ({ ...s, type: 'out' }))
            ].sort((a, b) => parseDate(b.data) - parseDate(a.data)).slice(0, 10);

            const list = document.getElementById('recentActivity');
            list.innerHTML = all.length ? '' : '<p style="text-align: center; color: var(--text-muted); padding: 20px;">Nenhuma atividade recente.</p>';

            all.forEach(item => {
                list.appendChild(createActivityItem(item));
            });
        }"""
html = html.replace(old_dash_text, JS_DASHBOARD_NEW)

# novoCliente logic replacement
JS_NOVOCLIENTE_OLD = """        async function novoCliente() {
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
        }"""
JS_NOVOCLIENTE_NEW = """        function openClienteModal() {
            document.getElementById('clienteOverlay').style.display = 'flex';
            document.getElementById('clienteNome').value = '';
            document.getElementById('clienteWhatsapp').value = '';
            document.getElementById('clienteCpf').value = '';
        }
        
        function closeClienteModal() {
            document.getElementById('clienteOverlay').style.display = 'none';
        }
        
        async function handleClienteSubmit(e) {
            e.preventDefault();
            const nome = document.getElementById('clienteNome').value;
            const whatsapp = document.getElementById('clienteWhatsapp').value;
            const cpf = document.getElementById('clienteCpf').value;
            if (!nome) return;
            
            showLoader(true);
            closeClienteModal();
            try {
                const resp = await fetch(API_URL, {
                    method: 'POST',
                    body: JSON.stringify({
                        op: 'criarCliente',
                        nome: nome,
                        telefone: whatsapp,
                        cpf: cpf
                    })
                });
                const result = await resp.json();
                if (result.sucesso) {
                    syncData();
                }
            } catch (err) {
                alert('Erro ao salvar cliente');
            } finally {
                showLoader(false);
            }
        }
        
        function novoCliente() {
            openClienteModal();
            closeModal(); // close Lançamento modal if open
            closeAgendaModal(); // close Agenda modal if open
        }
"""
html = html.replace(JS_NOVOCLIENTE_OLD, JS_NOVOCLIENTE_NEW)


# Hook listener
LISTENER_HOOK_OLD = """            document.getElementById('entryForm').addEventListener('submit', handleEntrySubmit);
            document.getElementById('agendaForm').addEventListener('submit', handleAgendaSubmit);"""
LISTENER_HOOK_NEW = """            document.getElementById('entryForm').addEventListener('submit', handleEntrySubmit);
            document.getElementById('agendaForm').addEventListener('submit', handleAgendaSubmit);
            document.getElementById('clienteForm').addEventListener('submit', handleClienteSubmit);"""
html = html.replace(LISTENER_HOOK_OLD, LISTENER_HOOK_NEW)

# 4. WhatsApp button in Agenda
html = html.replace(
"""                    <div class="activity-info" style="flex: 1;">
                        <h4 style="color: ${isToday ? 'var(--primary)' : 'inherit'};">${isToday ? 'HOJE - ' : ''}${item.data} ${item.hora ? 'às '+item.hora : ''}</h4>""",
"""                 
                    <div class="activity-info" style="flex: 1;">
                        <h4 style="color: ${isToday ? 'var(--primary)' : 'inherit'};">${isToday ? 'HOJE - ' : ''}${item.data} ${item.hora ? 'às '+item.hora : ''}</h4>"""
)

html = html.replace(
"""                    <div style="display:flex; flex-direction:column; gap:5px;">
                        <button onclick="concluirAgenda('${item.id}', '${item.cliente}', '${parseFloat(item.valor||0)}', '${item.endereco}')" style="background: var(--success); color: #fff; border: none; padding: 12px; border-radius: 8px; cursor: pointer;"><i class="fas fa-check"></i></button>
                        <button onclick="excluirAgenda('${item.id}')" style="background: var(--danger); color: #fff; border: none; padding: 12px; border-radius: 8px; cursor: pointer;"><i class="fas fa-trash"></i></button>
                    </div>""",
"""                    <div style="display:flex; flex-direction:column; gap:5px;">
                        ${(function(){
                            const clienteObj = item.cliente ? clientes.find(c => c.nome === item.cliente) : null;
                            if(clienteObj && clienteObj.telefone) {
                                let msg = 'Olá, ' + clienteObj.nome + '\\nConfirmo nosso agendamento para *' + item.data + '*';
                                if(item.hora) msg += ' às *' + item.hora + '*';
                                msg += '.\\nValor combinado: R$ ' + parseFloat(item.valor||0).toFixed(2);
                                return `<button onclick=\"window.open('https://wa.me/55${clienteObj.telefone.replace(/\\D/g, '')}?text=${encodeURIComponent(msg)}', '_blank')\" style=\"background: #25D366; color: #fff; border: none; padding: 12px; border-radius: 8px; cursor: pointer;\"><i class=\"fab fa-whatsapp\"></i></button>`;
                            }
                            return '';
                        })()}
                        <button onclick="concluirAgenda('${item.id}', '${item.cliente}', '${parseFloat(item.valor||0)}', '${item.endereco}')" style="background: var(--success); color: #fff; border: none; padding: 12px; border-radius: 8px; cursor: pointer;"><i class="fas fa-check"></i></button>
                        <button onclick="excluirAgenda('${item.id}')" style="background: var(--danger); color: #fff; border: none; padding: 12px; border-radius: 8px; cursor: pointer;"><i class="fas fa-trash"></i></button>
                    </div>""")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(html)
