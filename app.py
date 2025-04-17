import sys
import webbrowser
from threading import Timer
from flask import Flask, render_template, request, redirect, url_for, send_file, session
from fpdf import FPDF
from datetime import datetime
from flask import jsonify

import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

USUARIO_PADRAO = {
    'usuario': 'admin',
    'senha': '0000'
}

def abrir_navegador():
    webbrowser.open_new("http://127.0.0.1:5000/")

#pyinstaller ;noconfirm ;onefile ;add-data "templates;templates" ;add-data "static;static" ;add-data "estoque.db;." app.py

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.abspath(".")

base_path = get_base_path()
db_path = os.path.join(base_path, "estoque.db")

# Inicializar banco se necessário
def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            preco REAL,
            quantidade INTEGER
        );
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_estoque INTEGER,
            preco_venda REAL,
            quantidade INTEGER,
            data TEXT,
            FOREIGN KEY(id_estoque) REFERENCES estoque(id)
        );
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/api/estoque')
def api_estoque():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM estoque')
    itens = cursor.fetchall()
    conn.close()

    return jsonify([dict(row) for row in itens])


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        if usuario == 'admin' and senha == '0000':
            session['usuario'] = usuario
            return redirect(url_for('index'))
        else:
            return render_template('login.html', erro='Usuário ou senha incorretos.')
    return render_template('login.html')



@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))


def conectar_db():
    conn = sqlite3.connect('estoque.db')
    conn.row_factory = sqlite3.Row
    return conn


def conectar_db():
    conn = sqlite3.connect('estoque.db')
    conn.row_factory = sqlite3.Row
    return conn


def calcular_lucro():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT t.id_estoque, e.nome, t.preco_venda, t.quantidade, t.data, e.preco
        FROM transacoes t
        JOIN estoque e ON t.id_estoque = e.id
    ''')
    transacoes = cursor.fetchall()
    conn.close()
    total_lucro = 0
    linhas = []
    for row in transacoes:
        lucro = (row['preco_venda'] - row['preco']) * row['quantidade']
        total_lucro += lucro
        linhas.append(f"{row['nome']} | Qtde: {row['quantidade']} | Lucro: R${lucro:.2f}")

    resposta = "💰 *Relatório de Lucro*\n\n"
    resposta += "\n".join(linhas)
    resposta += f"\n\n📈 *Lucro Total:* R${total_lucro:.2f}"
    return resposta


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conn = conectar_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        id_item = request.form['id']
        nome = request.form['nome']
        preco = float(request.form['preco'])
        quantidade = int(request.form['quantidade'])

        cursor.execute('''
            UPDATE estoque 
            SET nome = ?, preco = ?, quantidade = ?
            WHERE id = ?
        ''', (nome, preco, quantidade, id_item))
        conn.commit()

    cursor.execute('SELECT * FROM estoque')
    estoque = cursor.fetchall()
    conn.close()

    return render_template('index.html', estoque=estoque)


@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar():
    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        quantidade = int(request.form['quantidade'])

        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO estoque (nome, preco, quantidade) VALUES (?, ?, ?)', (nome, preco, quantidade))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('adicionar.html')


@app.route('/vender', methods=['GET', 'POST'])
def vender():
    conn = conectar_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        id_estoque = int(request.form['id_estoque'])
        quantidade_vendida = int(request.form['quantidade'])
        preco_venda = float(request.form['preco_venda'])  # <-- preço da venda informado pelo usuário

        cursor.execute('SELECT quantidade FROM estoque WHERE id = ?', (id_estoque,))
        resultado = cursor.fetchone()

        if resultado and resultado['quantidade'] >= quantidade_vendida:
            nova_quantidade = resultado['quantidade'] - quantidade_vendida

            # Atualizar estoque
            cursor.execute('UPDATE estoque SET quantidade = ? WHERE id = ?', (nova_quantidade, id_estoque))

            # Registrar transação
            data = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                INSERT INTO transacoes (id_estoque, preco_venda, quantidade, data)
                VALUES (?, ?, ?, ?)
            ''', (id_estoque, preco_venda, quantidade_vendida, data))

            conn.commit()

    cursor.execute('SELECT id, nome FROM estoque')
    itens = cursor.fetchall()
    conn.close()

    return render_template('vender.html', itens=itens)


@app.route('/transacoes')
def transacoes():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT t.id, e.nome, t.quantidade, t.data
        FROM transacoes t
        JOIN estoque e ON t.id_estoque = e.id
        ORDER BY t.data DESC
    ''')
    transacoes = cursor.fetchall()
    conn.close()

    return render_template('transacoes.html', transacoes=transacoes)


@app.route('/lucro')
def lucro():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT t.id_estoque, e.nome, t.preco_venda, t.quantidade, t.data, e.preco
        FROM transacoes t
        JOIN estoque e ON t.id_estoque = e.id
    ''')
    transacoes = cursor.fetchall()

    dados_lucro = []
    for row in transacoes:
        lucro_total = (row['preco_venda'] - row['preco']) * row['quantidade']
        dados_lucro.append({
            'nome_item': row['nome'],
            'preco_venda': row['preco_venda'],
            'preco_compra': row['preco'],
            'quantidade': row['quantidade'],
            'lucro': lucro_total,
            'data': row['data']
        })

    conn.close()
    return render_template('lucro.html', dados=dados_lucro)


@app.route('/lucro_texto')
def lucro_texto():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    resposta = calcular_lucro()
    return f"<pre>{resposta}</pre>"


@app.route('/remover/<int:id>')
def remover(id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM estoque WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/exportar_transacoes_pdf')
def exportar_transacoes_pdf():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.id, e.nome, t.quantidade, t.data
        FROM transacoes t
        JOIN estoque e ON t.id_estoque = e.id
        ORDER BY t.data DESC
    ''')
    transacoes = cursor.fetchall()
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(200, 10, 'Relatório de Transações', ln=True, align='C')

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(20, 10, 'ID', 1)
    pdf.cell(70, 10, 'Item', 1)
    pdf.cell(30, 10, 'Qtd.', 1)
    pdf.cell(50, 10, 'Data', 1)
    pdf.ln()

    pdf.set_font('Arial', '', 12)
    for t in transacoes:
        pdf.cell(20, 10, str(t['id']), 1)
        pdf.cell(70, 10, t['nome'], 1)
        pdf.cell(30, 10, str(t['quantidade']), 1)
        pdf.cell(50, 10, t['data'], 1)
        pdf.ln()


    caminho_pdf = os.path.abspath('transacoes.pdf')
    pdf.output(caminho_pdf)
    return send_file(caminho_pdf, as_attachment=True)


if __name__ == '__main__':
    Timer(1, abrir_navegador).start()  # Aguarda 1 segundo e abre
    app.run(debug=False)
