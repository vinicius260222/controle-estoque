from flask import Flask, render_template, request, redirect, session, url_for, send_file
from openpyxl import Workbook
import json
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chave-secreta-super-segura")

ARQUIVO_ESTOQUE = "estoque.json"
ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_CAIXA = "caixa.json"


# ---------- FUNÇÕES AUXILIARES ----------

def carregar_json(arquivo, padrao):
    if os.path.exists(arquivo):
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    return padrao


def salvar_json(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


# ---------- ROTAS ----------

@app.route("/", methods=["GET", "POST"])
def login():
    erro = None

    if request.method == "POST":
        usuarios = carregar_json(ARQUIVO_USUARIOS, {})
        usuario = request.form.get("usuario")
        senha = request.form.get("senha")

        if usuario in usuarios and usuarios[usuario] == senha:
            session["usuario"] = usuario
            return redirect(url_for("produtos"))
        else:
            erro = "Usuário ou senha inválidos"

    return render_template("login.html", erro=erro)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/produtos", methods=["GET", "POST"])
def produtos():
    if "usuario" not in session:
        return redirect(url_for("login"))

    estoque = carregar_json(ARQUIVO_ESTOQUE, {})
    caixa = carregar_json(ARQUIVO_CAIXA, {"saldo": 0})

    if request.method == "POST":
        nome = request.form.get("nome")
        quantidade = int(request.form.get("quantidade", 0))
        preco = float(request.form.get("preco", 0))
        tipo = request.form.get("tipo")

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

        return redirect(url_for("produtos"))

    return render_template(
        "produtos.html",
        estoque=estoque,
        caixa=caixa["saldo"],
        usuario=session["usuario"]
    )


@app.route("/exportar")
def exportar():
    if "usuario" not in session:
        return redirect(url_for("login"))

    estoque = carregar_json(ARQUIVO_ESTOQUE, {})
    caixa = carregar_json(ARQUIVO_CAIXA, {"saldo": 0})

    wb = Workbook()
    ws = wb.active
    ws.title = "Estoque"

    ws.append(["Produto", "Quantidade", "Preço Unitário", "Total"])

    for nome, dados in estoque.items():
        total = dados["quantidade"] * dados["preco"]
        ws.append([nome, dados["quantidade"], dados["preco"], total])

    ws.append([])
    ws.append(["", "", "Caixa Total", caixa["saldo"]])

    caminho = "estoque.xlsx"
    wb.save(caminho)

    return send_file(caminho, as_attachment=True, download_name="estoque.xlsx")


# ---------- START ----------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)



