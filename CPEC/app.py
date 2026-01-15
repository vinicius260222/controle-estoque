from flask import Flask, render_template, request, redirect, session, url_for
import os
import json

# =============================
# CONFIGURAÇÃO BÁSICA
# =============================

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chave-secreta-cpec")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

USUARIOS_FILE = os.path.join(DATA_DIR, "usuarios.json")
PRODUTOS_FILE = os.path.join(DATA_DIR, "produtos.json")


# =============================
# FUNÇÕES AUXILIARES
# =============================

def carregar_json(caminho, padrao):
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return padrao


def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


# =============================
# ROTAS DE LOGIN
# =============================

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    usuarios = carregar_json(USUARIOS_FILE, {})

    if request.method == "POST":
        cpf = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "").strip()

        if cpf in usuarios and usuarios[cpf] == senha:
            session["usuario"] = cpf
            return redirect(url_for("home"))
        else:
            erro = "Usuário ou senha inválidos"

    return render_template("login.html", erro=erro)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =============================
# HOME (NÃO ALTERA LAYOUT)
# =============================

@app.route("/home")
def home():
    if "usuario" not in session:
        return redirect(url_for("login"))

    return render_template("home.html", usuario=session["usuario"])


# =============================
# CADASTRO DE PRODUTOS
# =============================

@app.route("/cadastro-produtos", methods=["GET", "POST"])
def cadastro_produtos():
    if "usuario" not in session:
        return redirect(url_for("login"))

    produtos = carregar_json(PRODUTOS_FILE, {})

    if request.method == "POST":
        codigo = request.form.get("codigo").strip()
        nome = request.form.get("nome").strip()
        categoria = request.form.get("categoria").strip()
        unidade = request.form.get("unidade").strip()
        observacoes = request.form.get("observacoes", "").strip()

        if codigo and nome:
            produtos[codigo] = {
                "nome": nome,
                "categoria": categoria,
                "unidade": unidade,
                "observacoes": observacoes
            }
            salvar_json(PRODUTOS_FILE, produtos)

        return redirect(url_for("cadastro_produtos"))

    return render_template("cadastro_produtos.html", produtos=produtos)


# =============================
# TESTE DE VIDA (RENDER)
# =============================

@app.route("/ping")
def ping():
    return "pong"


# =============================
# START (OBRIGATÓRIO PARA RENDER)
# =============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
