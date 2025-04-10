from flask import Flask, request, redirect, url_for
from fpdf import FPDF
import os
import urllib.parse

from flask import Flask, request, send_file
from fpdf import FPDF
import io

from flask import Flask, render_template, request, redirect
import sqlite3

from flask import Flask, render_template, request, redirect, session, url_for
import os

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Pode ser qualquer string única

UPLOAD_FOLDER = 'pdfs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

import sqlite3

def criar_tabela_clientes():
    conn = sqlite3.connect('estoque.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT,
            whatsapp TEXT,
            endereco TEXT
        )
    ''')
    conn.commit()
    conn.close()

criar_tabela_clientes()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        if usuario == 'admin' and senha == '1234':  # Troque para os dados reais
            session['logado'] = True
            return redirect('/painel')
        else:
            return render_template('login.html', erro='Usuário ou senha inválidos')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logado', None)
    return redirect('/login')


@app.route('/')
def home():
    return render_template('index.html')

'''@app.route('/salvar-lead', methods=['POST'])
def salvar_lead():
    nome = request.form['nome']
    email = request.form['email']
    whatsapp = request.form['whatsapp']

    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO leads (nome, email, whatsapp) VALUES (?, ?, ?)", (nome, email, whatsapp))
    conn.commit()
    conn.close()

    # Redirecionar pro WhatsApp
    msg = f"Olá! Quero testar o System Stock.%0A%0ANome: {nome}%0AEmail: {email}%0AWhatsApp: {whatsapp}"
    return redirect(f"https://wa.me/5582999311658?text={msg}")
'''

@app.route('/gerar-pdf', methods=['POST'])
def gerar_pdf():
    nome = request.form['nome']
    email = request.form['email']
    whatsapp = request.form['whatsapp']

    # Cria o PDF na memória
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="Dados do Lead - System Stock", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Nome: {nome}", ln=True)
    pdf.cell(200, 10, txt=f"E-mail: {email}", ln=True)
    pdf.cell(200, 10, txt=f"WhatsApp: {whatsapp}", ln=True)

    # Salva em memória e envia como download
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    return send_file(
        pdf_output,
        download_name=f"lead_{nome.replace(' ', '_')}.pdf",
        as_attachment=True
    )


from datetime import datetime


@app.route('/salvar-lead', methods=['POST'])
def salvar_lead():
    nome = request.form['nome']
    email = request.form['email']
    whatsapp = request.form['whatsapp']
    data = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Gerar PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="Lead System Stock", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Nome: {nome}", ln=True)
    pdf.cell(200, 10, txt=f"E-mail: {email}", ln=True)
    pdf.cell(200, 10, txt=f"WhatsApp: {whatsapp}", ln=True)

    safe_nome = nome.replace(" ", "_")
    filename = f"lead_{safe_nome}_{int(datetime.now().timestamp())}.pdf"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    pdf.output(filepath)

    # Salvar no banco
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO leads (nome, email, whatsapp, data, pdf_filename) VALUES (?, ?, ?, ?, ?)",
                   (nome, email, whatsapp, data, filename))
    conn.commit()
    conn.close()

    # WhatsApp
    link = request.url_root.rstrip("/") + f"/pdfs/{filename}"
    mensagem = f"Novo lead no System Stock!%0A%0ANome: {nome}%0AEmail: {email}%0AWhatsApp: {whatsapp}%0ABAIXAR PDF: {link}"
    whatsapp_link = f"https://wa.me/5582999311658?text={urllib.parse.quote(mensagem)}"

    return redirect(whatsapp_link)

    return redirect(whatsapp_link)

from flask import send_from_directory

@app.route('/pdfs/<filename>')
def baixar_pdf(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/painel')
def painel():
    if not session.get('logado'):
        return redirect('/login')

    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, email, whatsapp, data, pdf_filename FROM leads ORDER BY id DESC")
    leads = cursor.fetchall()
    conn.close()

    return render_template("painel.html", leads=leads)


import os
from flask import send_from_directory

@app.route('/pdfs', methods=['GET'])
def listar_pdfs():
    pasta_pdfs = os.path.join(app.root_path, 'pdfs')
    arquivos = [f for f in os.listdir(pasta_pdfs) if f.endswith('.pdf')]
    return render_template('pdfs.html', arquivos=arquivos)

@app.route('/excluir-pdf/<nome>', methods=['POST'])
def excluir_pdf(nome):
    caminho = os.path.join(app.root_path, 'pdfs', nome)
    if os.path.exists(caminho):
        os.remove(caminho)
    return redirect('/pdfs')


from flask import Flask, render_template, request, redirect, url_for

@app.route("/clientes", methods=["GET", "POST"])
def clientes():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        whatsapp = request.form["whatsapp"]
        endereco = request.form["endereco"]

        conn = sqlite3.connect("estoque.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO clientes (nome, email, whatsapp, endereco) VALUES (?, ?, ?, ?)",
                       (nome, email, whatsapp, endereco))
        conn.commit()
        conn.close()
        return redirect(url_for("clientes"))

    # Exibe lista de clientes cadastrados
    conn = sqlite3.connect("estoque.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()
    conn.close()
    return render_template("clientes.html", clientes=clientes)


@app.route("/clientes/editar/<int:id>", methods=["GET", "POST"])
def editar_cliente(id):
    conn = sqlite3.connect("estoque.db")
    cursor = conn.cursor()

    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        whatsapp = request.form["whatsapp"]
        endereco = request.form["endereco"]

        cursor.execute("""
            UPDATE clientes SET nome=?, email=?, whatsapp=?, endereco=?
            WHERE id=?
        """, (nome, email, whatsapp, endereco, id))
        conn.commit()
        conn.close()
        return redirect(url_for("clientes"))

    cursor.execute("SELECT * FROM clientes WHERE id=?", (id,))
    cliente = cursor.fetchone()
    conn.close()
    return render_template("editar_cliente.html", cliente=cliente)


@app.route("/clientes/excluir/<int:id>")
def excluir_cliente(id):
    conn = sqlite3.connect("estoque.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("clientes"))


if __name__ == '__main__':
    app.run(debug=True)
