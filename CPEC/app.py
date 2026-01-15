from flask import Flask, render_template, request, redirect, session, url_for
import json
import os
from uuid import uuid4

app = Flask(__name__)
app.secret_key = "chave-secreta-cpec"

# ===============================
# CONFIGURAÇÃO DE PASTAS / ARQUIVOS
# ===============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

PRODUTOS_FILE = os.path.join(DATA_DIR, "produtos.json")

# ===============================
# GARANTIR ESTRUTURA
# ===============================

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

if not os.path.exists(PRODUTOS_FILE):
    with open(PRODUTOS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

# ===============================
# FUNÇÕES AUXILIARES
# ===============================

def carregar_json(caminho, padrao):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return padrao


def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


# ===============================
# LOGIN (SIMPLES POR ENQUANTO)
# ===============================

USUARIOS = {
    "admin": "1234"
}

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None

    if request.method == "POST":
        usuario = request.form.get("usuario")
        senha = request.form.get("senha")

        if usuario in USUARIOS and USUARIOS[usuario] == senha:
            session["usuario"] = usuario
            return redirect(url_for("home"))
        else:
            erro = "Usuário ou senha inválidos"

    return render_template("login.html", erro=erro)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ===============================
# HOME
# ===============================

@app.route("/home")
def home():
    if "usuario" not in session:
        return redirect(url_for("login"))

    return render_template("home.html")


# ===============================
# CADASTRO DE PRODUTOS
# ===============================

@app.route("/cadastro-produtos", methods=["GET", "POST"])
def cadastro_produtos():
    if "usuario" not in session:
        return redirect(url_for("login"))

    produtos = carregar_json(PRODUTOS_FILE, {})

    if request.method == "POST":
        produto_id = str(uuid4())[:8]

        produtos[produto_id] = {
            "id": produto_id,
            "nome": request.form.get("nome"),
            "categoria": request.form.get("categoria"),
            "unidade": request.form.get("unidade"),
            "preco_custo": float(request.form.get("preco_custo") or 0),
            "preco_venda": float(request.form.get("preco_venda") or 0),
            "estoque_minimo": int(request.form.get("estoque_minimo") or 0),
            "fornecedor": request.form.get("fornecedor"),
            "observacoes": request.form.get("observacoes"),
            "status": "ativo" if request.form.get("status") else "inativo"
        }

        salvar_json(PRODUTOS_FILE, produtos)
        return redirect(url_for("cadastro_produtos"))

    return render_template("cadastro_produtos.html", produtos=produtos)

# ===============================
# START
# ===============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
