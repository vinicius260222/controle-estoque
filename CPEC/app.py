from flask import Flask, render_template, request, redirect, url_for, session
import os
import json

# =============================
# CONFIGURAÇÃO BÁSICA
# =============================
app = Flask(__name__)
app.secret_key = "cpec-chave-super-segura"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

USUARIOS_FILE = os.path.join(DATA_DIR, "usuarios.json")

# =============================
# FUNÇÕES AUXILIARES
# =============================
def carregar_usuarios():
    if not os.path.exists(USUARIOS_FILE):
        return {}
    with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_usuarios(usuarios):
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)

# =============================
# USUÁRIOS PADRÃO (SE NÃO EXISTIR)
# =============================
if not os.path.exists(USUARIOS_FILE):
    usuarios_padrao = {
        "1": {
            "cpf": "04932346913",
            "senha": "02111982",
            "nome": "Administrador"
        },
        "2": {
            "cpf": "00766969959",
            "senha": "01061981",
            "nome": "Usuário 2"
        },
        "3": {
            "cpf": "13455528902",
            "senha": "06102006",
            "nome": "Usuário 3"
        }
    }
    salvar_usuarios(usuarios_padrao)

# =============================
# ROTAS
# =============================

# ROTA INICIAL → LOGIN
@app.route("/")
def index():
    return redirect(url_for("login_page"))

# LOGIN (GET)
@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

# LOGIN (POST)
@app.route("/login", methods=["POST"])
def login():
    cpf = request.form.get("cpf")
    senha = request.form.get("senha")

    usuarios = carregar_usuarios()

    for user in usuarios.values():
        if user["cpf"] == cpf and user["senha"] == senha:
            session["usuario"] = user["nome"]
            session["cpf"] = user["cpf"]
            return redirect(url_for("home"))

    return render_template("login.html", erro="Usuário ou senha inválidos")

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

# HOME (PROTEGIDA)
@app.route("/home")
def home():
    if "usuario" not in session:
        return redirect(url_for("login_page"))

    return render_template(
        "home.html",
        usuario=session["usuario"]
    )

# =============================
# START (RENDER)
# =============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
