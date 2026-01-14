from openpyxl import Workbook
from flask import send_file

from flask import Flask, render_template, request, redirect, session url for
import json
import os

app = Flask(__name__)
app.secret_key = "chave-secreta-super-segura"

ARQUIVO_ESTOQUE = "estoque.json"
ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_CAIXA = "caixa.json"


def carregar_json(arquivo, padrao):
    if os.path.exists(arquivo):
        with open(arquivo, "r") as f:
            return json.load(f)
    return padrao


def salvar_json(arquivo, dados):
    with open(arquivo, "w") as f:
        json.dump(dados, f, indent=4)


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuarios = carregar_json(ARQUIVO_USUARIOS, {})
        user = request.form["usuario"]
        senha = request.form["senha"]

        if user in usuarios and usuarios[user] == senha:
            session["usuario"] = user
            return redirect("/produtos")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/produtos", methods=["GET", "POST"])
def produtos():
    if "usuario" not in session:
        return redirect("/")

    estoque = carregar_json(ARQUIVO_ESTOQUE, {})
    caixa = carregar_json(ARQUIVO_CAIXA, {"saldo": 0})

    if request.method == "POST":
        nome = request.form["nome"]
        quantidade = int(request.form["quantidade"])
        preco = float(request.form["preco"])
        tipo = request.form["tipo"]

        if nome not in estoque:
            estoque[nome] = {"quantidade": 0, "preco": preco}

        if tipo == "entrada":
            estoque[nome]["quantidade"] += quantidade
        else:
            estoque[nome]["quantidade"] -= quantidade
            if estoque[nome]["quantidade"] < 0:
                estoque[nome]["quantidade"] = 0
            caixa["saldo"] += quantidade * estoque[nome]["preco"]

        salvar_json(ARQUIVO_ESTOQUE, estoque)
        salvar_json(ARQUIVO_CAIXA, caixa)
        return redirect("/produtos")

    return render_template(
        "produtos.html",
        estoque=estoque,
        caixa=caixa["saldo"],
        usuario=session["usuario"]
    )
@app.route("/exportar")
def exportar_excel():
    if "usuario" not in session:
        return redirect("/")

    estoque = carregar_json(ARQUIVO_ESTOQUE, {})
    caixa = carregar_json(ARQUIVO_CAIXA, {"saldo": 0})

    wb = Workbook()
    ws = wb.active
    ws.title = "Estoque"

    ws.append(["Produto", "Quantidade", "Preço Unitário", "Total"])

    for nome, dados in estoque.items():
        total = dados["quantidade"] * dados["preco"]
        ws.append([
            nome,
            dados["quantidade"],
            dados["preco"],
            total
        ])

    ws.append([])
    ws.append(["", "", "Caixa Total", caixa["saldo"]])

    caminho = "estoque.xlsx"
    wb.save(caminho)

    return send_file(
        caminho,
        as_attachment=True,
        download_name="estoque.xlsx"
    )

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)



