// --- CONFIGURAÇÃO ---
// Se o script estiver "preso" (container-bound) na planilha, use getActiveSpreadsheet().
// Se for script independente, coloque o ID da planilha entre aspas abaixo.
try {
    var ID_PLANILHA = SpreadsheetApp.getActiveSpreadsheet().getId();
} catch (e) {
    var ID_PLANILHA = "COLOCAR_ID_DA_PLANILHA_AQUI_SE_DER_ERRO";
}

const CACHE_MINUTOS = 0;

function doGet(e) {
    try {
        const op = e.parameter.op;
        const ultimoTimestampCliente = e.parameter.ts || 0;

        if (op === "ler") return lerDados(ultimoTimestampCliente);

        // Teste de conexão simples
        if (op === "ping") return respostaJSON({ sucesso: true, msg: "Pong" });

        return respostaJSON({ erro: "Operação GET inválida: " + op });
    } catch (err) {
        return respostaJSON({ erro: "Erro interno no GET: " + err.toString() });
    }
}

function doPost(e) {
    const lock = LockService.getScriptLock();
    if (!lock.tryLock(10000)) {
        return respostaJSON({ erro: "Servidor ocupado. Tente novamente." });
    }

    try {
        if (!e.postData || !e.postData.contents) {
            return respostaJSON({ erro: "Nenhum dado recebido (Body vazio)" });
        }

        const dados = JSON.parse(e.postData.contents);
        const op = dados.op;
        let resultado;

        if (op === "criarCliente") resultado = criarCliente(dados.nome, dados.telefone || "", dados.cpf || "", dados.pdfBase64);
        else if (op === "lancar") resultado = lancarTransacao(dados.clienteId, dados.descricao, dados.valor);
        else if (op === "abater") resultado = abaterDivida(dados.clienteId, dados.valor, dados.metodo);
        else if (op === "pagar") resultado = pagarTransacao(dados.id); // Usado para remover item individualmente
        else if (op === "excluirCliente") resultado = excluirCliente(dados.clienteId);
        else if (op === "editarCliente") resultado = editarCliente(dados.clienteId, dados.novoNome, dados.novoTelefone, dados.novoCPF);
        else if (op === "pagarLote") resultado = pagarLote(dados.ids, dados.metodo);
        else if (op === "registrarFluxo") resultado = registrarFluxo(dados.tipo, dados.descricao, dados.valor, dados.metodo, dados.categoria);
        else if (op === "excluirFluxo") resultado = excluirFluxo(dados.id, dados.tipo);
        else if (op === "agendar") resultado = agendarFrete(dados.data, dados.hora, dados.cliente, dados.endereco, dados.valor);
        else if (op === "concluirAgendamento") resultado = concluirAgendamento(dados.id);
        else if (op === "excluirAgendamento") resultado = excluirAgendamento(dados.id);
        else resultado = { erro: "Operação desconhecida: " + op };

        if (resultado && resultado.sucesso) {
            marcarAlteracao();
        }

        return respostaJSON(resultado);

    } catch (err) {
        return respostaJSON({ erro: "Erro interno no POST: " + err.toString() });
    } finally {
        lock.releaseLock();
    }
}

// --- CONTROLE DE VERSÃO ---
function marcarAlteracao() {
    const agora = Date.now().toString();
    PropertiesService.getScriptProperties().setProperty('ULTIMA_MODIFICACAO', agora);
}

function lerDados(ultimoTimestampCliente) {
    const props = PropertiesService.getScriptProperties();
    let ultimaModifServidor = props.getProperty('ULTIMA_MODIFICACAO');

    if (!ultimaModifServidor) {
        ultimaModifServidor = Date.now().toString();
        props.setProperty('ULTIMA_MODIFICACAO', ultimaModifServidor);
    }

    if (ultimoTimestampCliente && String(ultimoTimestampCliente) === String(ultimaModifServidor)) {
        return respostaJSON({ sucesso: true, modificado: false, timestamp: ultimaModifServidor });
    }

    const ss = SpreadsheetApp.openById(ID_PLANILHA);
    const sheetClientes = verificarEstrutura(ss, "Clientes", ["ID", "Nome", "Telefone", "CPF", "PDF"]);
    const sheetTransacoes = verificarEstrutura(ss, "Transacoes", ["ID", "ClienteID", "Data", "Descricao", "Valor"]);
    const sheetEntradas = verificarEstrutura(ss, "Entradas", ["ID", "Data", "Descricao", "Valor", "Metodo", "Categoria"]);
    const sheetSaidas = verificarEstrutura(ss, "Saidas", ["ID", "Data", "Descricao", "Valor", "Categoria"]);
    const sheetAgenda = verificarEstrutura(ss, "Agenda", ["ID", "Data", "Hora", "Cliente", "Endereco", "Valor", "Status"]);

    const dadosClientes = sheetClientes.getDataRange().getValues().slice(1);
    const listaClientes = dadosClientes.filter(r => r[0] !== "").map(row => ({
        id: row[0], nome: row[1], telefone: row[2], cpf: row[3] || "", pdf: row[4] || ""
    }));

    const dadosTransacoes = sheetTransacoes.getDataRange().getValues().slice(1);
    const listaTransacoes = dadosTransacoes.filter(r => r[0] !== "").map(row => ({
        id: row[0], clienteId: row[1], data: formatarData(row[2]), descricao: row[3], valor: Number(row[4])
    }));

    const dadosEntradas = sheetEntradas.getDataRange().getValues().slice(1);
    const listaEntradas = dadosEntradas.filter(r => r[0] !== "").map(row => ({
        id: row[0], data: formatarData(row[1]), descricao: row[2], valor: Number(row[3]), metodo: row[4], categoria: row[5]
    }));

    const dadosSaidas = sheetSaidas.getDataRange().getValues().slice(1);
    const listaSaidas = dadosSaidas.filter(r => r[0] !== "").map(row => ({
        id: row[0], data: formatarData(row[1]), descricao: row[2], valor: Number(row[3]), categoria: row[4]
    }));

    const dadosAgenda = sheetAgenda.getDataRange().getValues().slice(1);
    const listaAgenda = dadosAgenda.filter(r => r[0] !== "").map(row => ({
        id: row[0], data: formatarData(row[1]), hora: formatarHora(row[2]), cliente: row[3], endereco: row[4], valor: Number(row[5]), status: row[6]
    }));

    return respostaJSON({
        sucesso: true, modificado: true, timestamp: ultimaModifServidor,
        clientes: listaClientes, transacoes: listaTransacoes, entradas: listaEntradas, saidas: listaSaidas, agenda: listaAgenda
    });
}

// --- FUNÇÕES DE ESCRITA ---

function criarCliente(nome, telefone, cpf, pdfBase64) {
    const ss = SpreadsheetApp.openById(ID_PLANILHA);
    const sheet = verificarEstrutura(ss, "Clientes", ["ID", "Nome", "Telefone", "CPF", "PDF"]);

    let novoId = 1;
    const lastRow = sheet.getLastRow();
    if (lastRow > 1) {
        const ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues().flat(); // Coluna 1 = ID
        const idsNum = ids.map(x => parseInt(x)).filter(x => !isNaN(x));
        if (idsNum.length > 0) novoId = Math.max(...idsNum) + 1;
    }

    sheet.appendRow([novoId, nome, telefone, cpf, ""]);
    return { sucesso: true, id: novoId };
}

function lancarTransacao(clienteId, descricao, valor) {
    const ss = SpreadsheetApp.openById(ID_PLANILHA);
    const sheet = verificarEstrutura(ss, "Transacoes", ["ID", "ClienteID", "Data", "Descricao", "Valor"]);
    const novoId = Date.now().toString();
    const dataHoje = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "dd/MM/yyyy");

    sheet.appendRow([novoId, clienteId, dataHoje, descricao, valor]);
    return { sucesso: true, id: novoId };
}

function abaterDivida(clienteId, valorPagamento, metodo = "DINHEIRO") {
    const ss = SpreadsheetApp.openById(ID_PLANILHA);
    const sheet = ss.getSheetByName("Transacoes");
    if (!sheet) return { erro: "Aba Transacoes não encontrada" };

    let valorRestante = Number(valorPagamento);
    if (isNaN(valorRestante) || valorRestante <= 0) return { erro: "Valor inválido" };

    // 1. REGISTRAR NO CAIXA (Fluxo de Entrada)
    const sCli = ss.getSheetByName("Clientes");
    let nomeCliente = "Cliente " + clienteId;
    if (sCli) {
        const dCli = sCli.getDataRange().getValues();
        for (let i = 1; i < dCli.length; i++) {
            if (String(dCli[i][0]) === String(clienteId)) { nomeCliente = dCli[i][1]; break; }
        }
    }
    registrarFluxo("entrada", "Recebimento Fiado (Abate): " + nomeCliente, valorPagamento, metodo);

    // 2. DAR BAIXA NAS DÍVIDAS
    const range = sheet.getDataRange();
    const values = range.getValues(); // Leitura única

    let dividas = [];
    // Coluna E (Index 4) = Valor. Coluna B (Index 1) = ClienteID
    for (let i = 1; i < values.length; i++) {
        if (String(values[i][1]) === String(clienteId) && Number(values[i][4]) > 0) {
            dividas.push({ rowIndex: i + 1, valor: Number(values[i][4]) });
        }
    }

    let deletar = [];
    let atualizar = [];

    for (let divida of dividas) {
        if (valorRestante <= 0) break;

        let pagoNesta = Math.min(divida.valor, valorRestante);
        let novoSaldo = divida.valor - pagoNesta;

        if (novoSaldo <= 0.01) deletar.push(divida.rowIndex);
        else atualizar.push({ rowIndex: divida.rowIndex, val: novoSaldo });

        valorRestante -= pagoNesta;
    }

    // Executar Updates
    atualizar.forEach(o => sheet.getRange(o.rowIndex, 5).setValue(o.val));
    // Executar Deletes (do final pro começo pra não mudar índices)
    deletar.sort((a, b) => b - a).forEach(r => sheet.deleteRow(r));

    // 3. SE SOBROU, GERA CRÉDITO
    if (valorRestante > 0.01) {
        const dataHoje = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "dd/MM/yyyy");
        // Crédito é valor negativo na tabela de dívidas
        sheet.appendRow([Date.now(), clienteId, dataHoje, "CRÉDITO/TROCO", -valorRestante]);
    }

    return { sucesso: true, abatido: valorPagamento - valorRestante, credito: valorRestante };
}

function pagarTransacao(id) {
    const ss = SpreadsheetApp.openById(ID_PLANILHA);
    const sheet = ss.getSheetByName("Transacoes");
    const dados = sheet.getDataRange().getValues();
    for (let i = 1; i < dados.length; i++) {
        if (String(dados[i][0]) === String(id)) {
            sheet.deleteRow(i + 1);
            return { sucesso: true };
        }
    }
    return { erro: "Item não encontrado para excluir." };
}

function pagarLote(ids, metodo = "DINHEIRO") {
    const ss = SpreadsheetApp.openById(ID_PLANILHA);
    const sheet = ss.getSheetByName("Transacoes");
    const d = sheet.getDataRange().getValues();
    if (d.length < 2) return { sucesso: true, msg: "Lista vazia" };

    const header = d[0];
    const rows = d.slice(1);

    // Identificar itens a remover
    const itensPagos = rows.filter(r => ids.includes(String(r[0])));
    if (itensPagos.length === 0) return { erro: "Nenhum item encontrado para baixar." };

    // 1. REGISTRAR NO CAIXA O TOTAL
    const totalPago = itensPagos.reduce((acc, r) => acc + (Number(r[4]) || 0), 0);
    const clienteId = itensPagos[0][1];

    const sCli = ss.getSheetByName("Clientes");
    let nomeCliente = "Cliente " + clienteId;
    if (sCli) {
        const dC = sCli.getDataRange().getValues();
        for (let i = 1; i < dC.length; i++) {
            if (String(dC[i][0]) === String(clienteId)) { nomeCliente = dC[i][1]; break; }
        }
    }
    registrarFluxo("entrada", "Recebimento Fiado (Lote): " + nomeCliente, totalPago, metodo);

    // 2. REESCREVER TABELA SEM OS PAGOS
    const novos = rows.filter(r => !ids.includes(String(r[0]))); // Mantém os que NÃO estão na lista

    sheet.clearContents();
    sheet.appendRow(header); // Devolve cabeçalho

    if (novos.length > 0) {
        sheet.getRange(2, 1, novos.length, novos[0].length).setValues(novos);
    }

    return { sucesso: true };
}

function excluirCliente(id) {
    const ss = SpreadsheetApp.openById(ID_PLANILHA);
    const sTr = ss.getSheetByName("Transacoes");

    // Remove transações
    if (sTr) {
        const d = sTr.getDataRange().getValues();
        const dels = [];
        for (let i = 1; i < d.length; i++) {
            if (String(d[i][1]) === String(id)) dels.push(i + 1);
        }
        dels.sort((a, b) => b - a).forEach(r => sTr.deleteRow(r));
    }

    // Remove Cliente
    const sCli = ss.getSheetByName("Clientes");
    const dC = sCli.getDataRange().getValues();
    for (let i = 1; i < dC.length; i++) {
        if (String(dC[i][0]) === String(id)) {
            sCli.deleteRow(i + 1);
            return { sucesso: true };
        }
    }
    return { erro: "Cliente não encontrado" };
}

function editarCliente(id, nome, tel, cpf) {
    const ss = SpreadsheetApp.openById(ID_PLANILHA);
    const sheet = ss.getSheetByName("Clientes");
    const d = sheet.getDataRange().getValues();
    for (let i = 1; i < d.length; i++) {
        if (String(d[i][0]) === String(id)) {
            if (nome) sheet.getRange(i + 1, 2).setValue(nome);
            // Mantém valor antigo se não vier novo
            if (tel !== undefined && tel !== null) sheet.getRange(i + 1, 3).setValue(tel);
            if (cpf !== undefined && cpf !== null) sheet.getRange(i + 1, 4).setValue(cpf);
            return { sucesso: true };
        }
    }
    return { erro: "Cliente não encontrado" };
}

function registrarFluxo(tipo, descricao, valor, metodo, categoria) {
    const ss = SpreadsheetApp.openById(ID_PLANILHA);
    const dataHoje = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "dd/MM/yyyy");
    const novoId = Date.now().toString() + Math.floor(Math.random() * 1000); // ID único robusto

    if (tipo === "entrada") {
        const sheet = verificarEstrutura(ss, "Entradas", ["ID", "Data", "Descricao", "Valor", "Metodo", "Categoria"]);
        sheet.appendRow([novoId, dataHoje, descricao, valor, metodo || "DINHEIRO", categoria || "OUTROS"]);
    } else {
        const sheet = verificarEstrutura(ss, "Saidas", ["ID", "Data", "Descricao", "Valor", "Categoria"]);
        sheet.appendRow([novoId, dataHoje, descricao, valor, categoria || "OUTROS"]);
    }
    return { sucesso: true };
}

function excluirFluxo(id, tipo) {
    const ss = SpreadsheetApp.openById(ID_PLANILHA);
    const nomeAba = tipo === "entrada" ? "Entradas" : "Saidas";
    const sheet = ss.getSheetByName(nomeAba);
    if (!sheet) return { erro: "Aba não existe" };

    const dados = sheet.getDataRange().getValues();
    for (let i = 1; i < dados.length; i++) {
        if (String(dados[i][0]) === String(id)) {
            sheet.deleteRow(i + 1);
            return { sucesso: true };
        }
    }
    return { erro: "Item não encontrado" };
}

function agendarFrete(dataAgendada, hora, cliente, endereco, valor) {
    const ss = SpreadsheetApp.openById(ID_PLANILHA);
    const sheet = verificarEstrutura(ss, "Agenda", ["ID", "Data", "Hora", "Cliente", "Endereco", "Valor", "Status"]);
    const novoId = Date.now().toString() + Math.random().toString(36).substr(2, 5);

    // Forçamos a data como string na planilha para evitar o GAS converter fuso horário (adicionando um apóstrofo se necessário, mas o apps script aceitará a string)
    sheet.appendRow([novoId, ' ' + dataAgendada, hora, cliente, endereco, valor || 0, "PENDENTE"]);
    return { sucesso: true };
}

function concluirAgendamento(id) {
    const ss = SpreadsheetApp.openById(ID_PLANILHA);
    const sheet = ss.getSheetByName("Agenda");
    if (!sheet) return { erro: "Aba não existe" };

    const dados = sheet.getDataRange().getValues();
    for (let i = 1; i < dados.length; i++) {
        if (String(dados[i][0]) === String(id)) {
            sheet.getRange(i + 1, 7).setValue("CONCLUIDO");
            return { sucesso: true };
        }
    }
    return { erro: "Não encontrado" };
}

function excluirAgendamento(id) {
    const ss = SpreadsheetApp.openById(ID_PLANILHA);
    const sheet = ss.getSheetByName("Agenda");
    if (!sheet) return { erro: "Aba não existe" };

    const dados = sheet.getDataRange().getValues();
    for (let i = 1; i < dados.length; i++) {
        if (String(dados[i][0]) === String(id)) {
            sheet.deleteRow(i + 1);
            return { sucesso: true };
        }
    }
    return { erro: "Item não encontrado" };
}

// --- UTILITÁRIOS ---

function verificarEstrutura(ss, nome, headers) {
    let sheet = ss.getSheetByName(nome);
    if (!sheet) {
        sheet = ss.insertSheet(nome);
        sheet.appendRow(headers);
        // Formatação básica
        sheet.setFrozenRows(1);
        sheet.getRange(1, 1, 1, headers.length).setFontWeight("bold");
    }
    return sheet;
}

function formatarData(d) {
    if (Object.prototype.toString.call(d) === '[object Date]') {
        return Utilities.formatDate(d, Session.getScriptTimeZone(), "dd/MM/yyyy");
    }
    return d;
}

function formatarHora(h) {
    if (Object.prototype.toString.call(h) === '[object Date]') {
        return Utilities.formatDate(h, Session.getScriptTimeZone(), "HH:mm");
    }
    return h;
}

function respostaJSON(obj) {
    return ContentService
        .createTextOutput(JSON.stringify(obj))
        .setMimeType(ContentService.MimeType.JSON);
}
