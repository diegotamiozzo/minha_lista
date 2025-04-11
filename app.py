import os
import re
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file
from fpdf import FPDF
from datetime import datetime
from pytz import timezone

app = Flask(__name__)
PDF_DIR = "pdfs"  # Diretório onde os PDFs serão salvos
os.makedirs(PDF_DIR, exist_ok=True)  # Garante que a pasta exista

def gerar_nome_pdf(ordem_servico, cliente):
    fuso_brasilia = timezone('America/Sao_Paulo')
    timestamp = datetime.now(fuso_brasilia).strftime("%d-%m-%Y_%Hh%M")
    
    # Sanitiza os nomes e força cliente para minúsculas
    ordem_servico = re.sub(r'[^\w\-]', '_', ordem_servico.strip())
    cliente = re.sub(r'[^\w\-]', '_', cliente.strip().lower())

    nome_arquivo = f"{ordem_servico}_{cliente}_{timestamp}.pdf"
    return os.path.join(PDF_DIR, nome_arquivo)

def pesquisar_codigo_por_trechos_descricao(nome_arquivo_db, termos):
    caminho_arquivo_db = os.path.join('data', nome_arquivo_db)
    if not os.path.exists(caminho_arquivo_db):
        return jsonify({'error': 'Banco de dados não encontrado.'}), 404
    try:
        conn = sqlite3.connect(caminho_arquivo_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='materiais'")
        if cursor.fetchone() is None:
            return jsonify({'error': 'Tabela "materiais" não encontrada no banco de dados.'}), 500
        query = "SELECT Codigo, Descricao FROM materiais WHERE" + " AND ".join([" LOWER(Descricao) LIKE ?" for _ in termos])
        parametros = [f"%{termo}%" for termo in termos]
        cursor.execute(query, parametros)
        resultados = cursor.fetchall()
        conn.close()
        return pd.DataFrame(resultados, columns=["Codigo", "Descricao"]) if resultados else pd.DataFrame()
    except sqlite3.Error as e:
        return jsonify({'error': f'Erro ao consultar o banco de dados: {e}'}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pesquisar', methods=['POST'])
def pesquisar():
    termos_pesquisa = request.form['material'].strip().lower()
    if not termos_pesquisa:
        return jsonify({'error': 'Por favor, insira um termo de pesquisa válido.'}), 400
    termos_pesquisa = termos_pesquisa.split()
    resultados = pesquisar_codigo_por_trechos_descricao("materiais.db", termos_pesquisa)
    if isinstance(resultados, tuple):
        return resultados
    return jsonify(resultados.to_dict(orient='records'))

@app.route('/finalizar', methods=['POST'])
def finalizar():
    solicitante = request.form.get('solicitante')
    ordem_servico = request.form.get('ordem_servico')
    cliente = request.form.get('cliente')
    data_solicitacao = request.form.get('data_solicitacao')
    data_retirada = request.form.get('data_retirada')
    hora_retirada = request.form.get('hora_retirada')
    materiais_selecionados_codigo = request.form.getlist('itens_codigo')
    materiais_selecionados_descricao = request.form.getlist('itens_descricao')
    materiais_selecionados_quantidade = request.form.getlist('itens_quantidade')
    materiais_selecionados_unidade = request.form.getlist('itens_unidade')

    if not materiais_selecionados_codigo:
        return jsonify({'error': 'Nenhum item selecionado.'}), 400

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Solicitação de Materiais", ln=True, align='C')
    pdf.ln(8)
    pdf.cell(200, 8, txt=f"Solicitante: {solicitante}", ln=True)
    pdf.cell(200, 8, txt=f"Nº da Ordem de Serviço: {ordem_servico}", ln=True)
    pdf.cell(200, 8, txt=f"Cliente: {cliente}", ln=True)
    pdf.cell(200, 8, txt=f"Data da Solicitação: {data_solicitacao}", ln=True)
    pdf.cell(200, 8, txt=f"Data da Retirada: {data_retirada}", ln=True)
    pdf.cell(200, 8, txt=f"Hora da Retirada: {hora_retirada}", ln=True)
    pdf.ln(8)

    pdf.set_font("Arial", style='B', size=10)
    pdf.cell(15, 8, txt="Cód.", border=1, align='C')
    pdf.cell(156, 8, txt="Descrição do Material", border=1, align='C')
    pdf.cell(12, 8, txt="Qtde", border=1, align='C')
    pdf.cell(12, 8, txt="Uni.", border=1, align='C')
    pdf.ln()
    pdf.set_font("Arial", size=8)

    for codigo, descricao, quantidade, unidade in zip(materiais_selecionados_codigo, materiais_selecionados_descricao, materiais_selecionados_quantidade, materiais_selecionados_unidade):
        pdf.cell(15, 8, txt=codigo, border=1, align='C')
        pdf.cell(156, 8, txt=descricao, border=1, align='L')
        pdf.cell(12, 8, txt=quantidade, border=1, align='C')
        pdf.cell(12, 8, txt=unidade, border=1, align='C')
        pdf.ln()

    # Remove PDFs antigos (opcional)
    for arquivo in os.listdir(PDF_DIR):
        caminho_arquivo = os.path.join(PDF_DIR, arquivo)
        if arquivo.endswith(".pdf"):
            os.remove(caminho_arquivo)

    # Salva o novo PDF com nome personalizado
    pdf_path = gerar_nome_pdf(ordem_servico, cliente)
    pdf.output(pdf_path)

    return jsonify({'message': 'PDF gerado com sucesso.', 'pdf_path': pdf_path})

@app.route('/baixar_pdf', methods=['GET'])
def baixar_pdf():
    arquivos = sorted([f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")], reverse=True)
    if arquivos:
        return send_file(os.path.join(PDF_DIR, arquivos[0]), as_attachment=True)
    return jsonify({'error': 'Arquivo PDF não encontrado.'}), 404

if __name__ == '__main__':
    app.run(debug=True)
