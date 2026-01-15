import os
import json
import pandas as pd
from flask import Flask, render_template, request, redirect, session, url_for, send_file

app = Flask(__name__)
app.secret_key = "chave-super-segura"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USUARIOS_FILE = os.path.join(BASE_DIR, "usuarios.json")
FUNCIONARIOS_FILE = os.path.join(BASE_DIR, "funcionarios.json")
ESTOQUE_FILE = os.path.join(BASE_DIR, "estoque.json")
CAIXA_FILE = os.path.join(BASE_DIR, "caixa.json")

# Funções de carregar e salvar JSON
def carregar_json(caminho):
    if not os.path.exists(caminho):
        return {}
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4)

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
@app.route("/login", methods=["GET","POST"])
def login():
    erro = None
    if request.method == "POST":
        cpf = request.form.get("usuario")
        senha = request.form.get("senha")
        usuarios = carregar_json(USUARIOS_FILE)
        if cpf in usuarios and usuarios[cpf]["senha"] == senha:
            session["usuario"] = cpf
            session["nome"] = usuarios[cpf]["nome"]
            return redirect(url_for("home"))
        else:
            erro = "Usuário ou senha inválidos"
    return render_template("login.html", erro=erro)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- DASHBOARD ----------------
@app.route("/home")
def home():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("home.html")

# ---------------- ESTOQUE ----------------
@app.route("/estoque", methods=["GET", "POST"])
def estoque():
    estoque = carregar_json(ESTOQUE_FILE)
    erro = None

    if request.method == "POST":
        nome = request.form.get("nome")
        quantidade = request.form.get("quantidade")
        if not nome or not quantidade:
            erro = "Todos os campos obrigatórios!"
        else:
            try:
                quantidade = int(quantidade)
            except ValueError:
                quantidade = 0
            if nome in estoque:
                estoque[nome]["quantidade"] += quantidade
            else:
                estoque[nome] = {"quantidade": quantidade}
            salvar_json(ESTOQUE_FILE, estoque)

    return render_template("estoque.html", estoque=estoque, erro=erro)

# ---------------- CAIXA ----------------
@app.route("/caixa", methods=["GET", "POST"])
def caixa():
    caixa = carregar_json(CAIXA_FILE)
    if not caixa:
        caixa = {"saldo": 0, "movimentos": []}

    if request.method == "POST":
        tipo = request.form.get("tipo")  # entrada ou saida
        valor = request.form.get("valor")
        try:
            valor = float(valor)
        except ValueError:
            valor = 0
        if tipo == "entrada":
            caixa["saldo"] += valor
        elif tipo == "saida":
            caixa["saldo"] -= valor
        caixa["movimentos"].append({"tipo": tipo, "valor": valor})
        salvar_json(CAIXA_FILE, caixa)

    return render_template("caixa.html", caixa=caixa)

# ---------------- FUNCIONÁRIOS ----------------
@app.route("/funcionarios", methods=["GET", "POST"])
def funcionarios():
    funcionarios = carregar_json(FUNCIONARIOS_FILE)
    erro = None

    editar_cpf = request.args.get("editar")
    funcionario_editar = None

    if editar_cpf and editar_cpf in funcionarios:
        funcionario_editar = {
            "cpf": editar_cpf,
            "nome": funcionarios[editar_cpf]["nome"],
            "cargo": funcionarios[editar_cpf]["cargo"],
            "dias_trabalhados": funcionarios[editar_cpf].get("dias_trabalhados", 0)
        }

    if request.method == "POST":
        cpf = request.form.get("cpf")
        nome = request.form.get("nome")
        cargo = request.form.get("cargo")
        dias_trabalhados = request.form.get("dias_trabalhados", 0)

        if not cpf or not nome or not cargo:
            erro = "Preencha todos os campos obrigatórios."
        else:
            try:
                dias_trabalhados = int(dias_trabalhados)
            except ValueError:
                dias_trabalhados = 0

            funcionarios[cpf] = {
                "nome": nome,
                "cargo": cargo,
                "dias_trabalhados": dias_trabalhados
            }

            salvar_json(FUNCIONARIOS_FILE, funcionarios)
            return redirect(url_for("funcionarios"))

    return render_template(
        "funcionarios.html",
        funcionarios=funcionarios,
        erro=erro,
        funcionario_editar=funcionario_editar
    )

# ---------------- RELATÓRIOS ----------------
@app.route("/relatorios/estoque")
def relatorio_estoque():
    estoque = carregar_json(ESTOQUE_FILE)
    df = pd.DataFrame([
        {"Nome": nome, "Quantidade": dados["quantidade"]}
        for nome, dados in estoque.items()
    ])
    caminho = "relatorio_estoque.xlsx"
    df.to_excel(caminho, index=False)
    return send_file(caminho, as_attachment=True)

@app.route("/relatorios/caixa")
def relatorio_caixa():
    caixa = carregar_json(CAIXA_FILE)
    df = pd.DataFrame(caixa.get("movimentos", []))
    caminho = "relatorio_caixa.xlsx"
    df.to_excel(caminho, index=False)
    return send_file(caminho, as_attachment=True)

@app.route("/relatorios/funcionarios")
def relatorio_funcionarios():
    funcionarios = carregar_json(FUNCIONARIOS_FILE)
    df = pd.DataFrame([
        {
            "CPF": cpf,
            "Nome": dados["nome"],
            "Cargo": dados["cargo"],
            "Dias Trabalhados": dados.get("dias_trabalhados", 0)
        }
        for cpf, dados in funcionarios.items()
    ])
    caminho = "relatorio_funcionarios.xlsx"
    df.to_excel(caminho, index=False)
    return send_file(caminho, as_attachment=True)

# ---------------- EXECUTAR APP ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
