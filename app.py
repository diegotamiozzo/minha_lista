import os
import pandas as pd
import chardet
from flask import Flask, render_template, request, jsonify, send_file
from fpdf import FPDF

app = Flask(__name__)
PDF_PATH = "solicitacao_material.pdf"

def pesquisar_codigo_por_trechos_descricao(nome_arquivo, termos):
    caminho_arquivo = os.path.join('data', nome_arquivo)

    if not os.path.exists(caminho_arquivo):
        return jsonify({'error': 'Arquivo CSV não encontrado.'}), 404

    try:
        with open(caminho_arquivo, 'rb') as f:
            result = chardet.detect(f.read())
            encoding = result['encoding']
        df = pd.read_csv(caminho_arquivo, sep=';', encoding=encoding, dtype={'Codigo': str})
    except Exception as e:
        return jsonify({'error': f'Erro ao ler o CSV: {e}'}), 500

    if 'Codigo' not in df.columns or 'Descricao' not in df.columns:
        return jsonify({'error': 'O arquivo CSV deve conter colunas "Codigo" e "Descricao".'}), 500

    resultados = df.copy()
    for termo in termos:
        resultados = resultados[
            resultados['Descricao'].str.lower().str.contains(termo, na=False) |
            resultados['Codigo'].str.contains(termo, na=False)
        ]
    
    return resultados

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pesquisar', methods=['POST'])
def pesquisar():
    termos_pesquisa = request.form['material'].strip().lower()
    if not termos_pesquisa:
        return jsonify({'error': 'Por favor, insira um termo de pesquisa válido.'}), 400
    
    termos_pesquisa = termos_pesquisa.split()
    nome_arquivo_csv = "feed.csv" 
    resultados = pesquisar_codigo_por_trechos_descricao(nome_arquivo_csv, termos_pesquisa)

    if isinstance(resultados, tuple):  # Verifica se houve um erro na função
        return resultados  # Retorna a resposta de erro

    materials = resultados.to_dict(orient='records')
    return jsonify(materials)

@app.route('/finalizar', methods=['POST'])
def finalizar():
    # Captura dos dados do formulário
    solicitante = request.form.get('solicitante')
    ordem_servico = request.form.get('ordem_servico')
    cliente = request.form.get('cliente')
    data_solicitacao = request.form.get('data_solicitacao')
    data_retirada = request.form.get('data_retirada')
    hora_retirada = request.form.get('hora_retirada')
    
    # Itens selecionados
    materiais_selecionados_codigo = request.form.getlist('itens_codigo')
    materiais_selecionados_descricao = request.form.getlist('itens_descricao')
    materiais_selecionados_quantidade = request.form.getlist('itens_quantidade')
    materiais_selecionados_unidade = request.form.getlist('itens_unidade')

    if not materiais_selecionados_codigo:
        return jsonify({'error': 'Nenhum item selecionado.'}), 400

    # Criação do PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Adicionando informações do solicitante e detalhes da retirada
    pdf.cell(200, 10, txt="Solicitação de Materiais", ln=True, align='C')
    pdf.ln(10)

    pdf.cell(200, 10, txt=f"Solicitante: {solicitante}", ln=True)
    pdf.cell(200, 10, txt=f"Nº da Ordem de Serviço: {ordem_servico}", ln=True)
    pdf.cell(200, 10, txt=f"Cliente: {cliente}", ln=True)
    pdf.cell(200, 10, txt=f"Data da Solicitação: {data_solicitacao}", ln=True)
    pdf.cell(200, 10, txt=f"Data da Retirada: {data_retirada}", ln=True)
    pdf.cell(200, 10, txt=f"Hora da Retirada: {hora_retirada}", ln=True)
    pdf.ln(10)

    # Adicionando os itens selecionados com quantidade e unidade
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(20, 10, txt="Cód.", border=1, align='C')
    pdf.cell(145, 10, txt="Descrição", border=1, align='C')
    pdf.cell(15, 10, txt="Qtde", border=1, align='C')
    pdf.cell(15, 10, txt="Uni.", border=1, align='C')
    pdf.ln()

    pdf.set_font("Arial", size=10)
    for codigo, descricao, quantidade, unidade in zip(materiais_selecionados_codigo, materiais_selecionados_descricao, materiais_selecionados_quantidade, materiais_selecionados_unidade):
        pdf.cell(20, 10, txt=codigo, border=1, align='C')
        pdf.cell(145, 10, txt=descricao, border=1, align='L')
        pdf.cell(15, 10, txt=quantidade, border=1, align='C')
        pdf.cell(15, 10, txt=unidade, border=1, align='C')
        pdf.ln()
    
    # Salvando o PDF
    pdf.output(PDF_PATH)
    
    return jsonify({'message': 'PDF gerado com sucesso.'})

@app.route('/baixar_pdf', methods=['GET'])
def baixar_pdf():
    if os.path.exists(PDF_PATH):
        return send_file(PDF_PATH, as_attachment=True)
    return jsonify({'error': 'Arquivo PDF não encontrado.'}), 404

if __name__ == '__main__':
    app.run(debug=True)
