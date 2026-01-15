import os
import json
from flask import Flask, render_template, request, redirect, session, url_for, send_file
from openpyxl import Workbook
from io import BytesIO

app = Flask(__name__)
app.secret_key = "chave-super-segura"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USUARIOS_FILE = os.path.join(BASE_DIR, "usuarios.json")
ESTOQUE_FILE = os.path.join(BASE_DIR, "estoque.json")
CAIXA_FILE = os.path.join(BASE_DIR, "caixa.json")
FUNCIONARIOS_FILE = os.path.join(BASE_DIR, "funcionarios.json")

# ------------------- Helpers -------------------

def carregar_json(caminho):
    if not os.path.exists(caminho):
        return {}
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# ------------------- Login -------------------

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        cpf = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "").strip()
        usuarios = carregar_json(USUARIOS_FILE)

        if cpf in usuarios and usuarios[cpf]["senha"] == senha:
            session["usuario"] = cpf
            session["nome"] = usuarios[cpf]["nome"]
            return redirect(url_for("home"))
        else:
            erro = "Usuário ou senha inválidos"
    return render_template("login.html", erro=erro)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ------------------- Dashboard -------------------

@app.route("/home")
def home():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("home.html", nome=session.get("nome"))

# ------------------- Estoque -------------------

@app.route("/estoque", methods=["GET", "POST"])
def estoque():
    if "usuario" not in session:
        return redirect(url_for("login"))

    estoque = carregar_json(ESTOQUE_FILE)
    erro = None

    if request.method == "POST":
        nome_item = request.form.get("nome_item", "").strip()
        quantidade = request.form.get("quantidade", "").strip()

        if not nome_item or not quantidade.isdigit():
            erro = "Preencha todos os campos corretamente."
        else:
            quantidade = int(quantidade)
            if nome_item in estoque:
                estoque[nome_item] += quantidade
            else:
                estoque[nome_item] = quantidade
            salvar_json(ESTOQUE_FILE, estoque)
            return redirect(url_for("estoque"))

    return render_template("estoque.html", estoque=estoque, erro=erro)

# ------------------- Caixa -------------------

@app.route("/caixa", methods=["GET", "POST"])
def caixa():
    if "usuario" not in session:
        return redirect(url_for("login"))

    caixa = carregar_json(CAIXA_FILE)
    if "saldo" not in caixa:
        caixa["saldo"] = 0.0

    erro = None
    if request.method == "POST":
        tipo = request.form.get("tipo")
        valor = request.form.get("valor", "").strip()
        if not valor or not valor.replace(".", "", 1).isdigit():
            erro = "Digite um valor válido."
        else:
            valor = float(valor)
            if tipo == "entrada":
                caixa["saldo"] += valor
            elif tipo == "saida":
                caixa["saldo"] -= valor
            salvar_json(CAIXA_FILE, caixa)
            return redirect(url_for("caixa"))

    return render_template("caixa.html", caixa=caixa, erro=erro)

# ------------------- Funcionários -------------------

@app.route("/funcionarios", methods=["GET", "POST"])
def funcionarios():
    if "usuario" not in session:
        return redirect(url_for("login"))

    funcionarios = carregar_json(FUNCIONARIOS_FILE)
    erro = None

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        cargo = request.form.get("cargo", "").strip()

        if not nome or not cargo:
            erro = "Preencha nome e cargo corretamente."
        else:
            id_func = str(len(funcionarios) + 1)
            funcionarios[id_func] = {"nome": nome, "cargo": cargo}
            salvar_json(FUNCIONARIOS_FILE, funcionarios)
            return redirect(url_for("funcionarios"))

    return render_template("funcionarios.html", funcionarios=funcionarios, erro=erro)

# ------------------- Relatórios -------------------

@app.route("/relatorios", methods=["GET", "POST"])
def relatorios():
    if "usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        tipo = request.form.get("tipo")
        wb = Workbook()
        ws = wb.active
        ws.title = tipo

        if tipo == "estoque":
            dados = carregar_json(ESTOQUE_FILE)
            ws.append(["Item", "Quantidade"])
            for item, qtd in dados.items():
                ws.append([item, qtd])
        elif tipo == "caixa":
            dados = carregar_json(CAIXA_FILE)
            ws.append(["Saldo"])
            ws.append([dados.get("saldo", 0)])
        elif tipo == "funcionarios":
            dados = carregar_json(FUNCIONARIOS_FILE)
            ws.append(["ID", "Nome", "Cargo"])
            for id_func, info in dados.items():
                ws.append([id_func, info["nome"], info["cargo"]])

        arquivo = BytesIO()
        wb.save(arquivo)
        arquivo.seek(0)
        return send_file(arquivo, download_name=f"{tipo}.xlsx", as_attachment=True)

    return render_template("relatorios.html")

# ------------------- Run -------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
