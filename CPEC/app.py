import os
import json
from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "chave-super-segura"  # Troque por algo mais complexo em produção

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USUARIOS_FILE = os.path.join(BASE_DIR, "usuarios.json")


def carregar_json(caminho):
    if not os.path.exists(caminho):
        return {}
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None

    if request.method == "POST":
        cpf = request.form.get("usuario")
        senha = request.form.get("senha")

        if not cpf or not senha:
            erro = "Preencha todos os campos"
        else:
            usuarios = carregar_json(USUARIOS_FILE)
            if cpf in usuarios and check_password_hash(usuarios[cpf]["senha"], senha):
                session["usuario"] = cpf
                session["nome"] = usuarios[cpf].get("nome", "Usuário")
                return redirect(url_for("home"))
            else:
                erro = "Usuário ou senha inválidos"

    return render_template("login.html", erro=erro)


@app.route("/home")
def home():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("home.html", nome=session.get("nome"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# Rota opcional para criar usuários (apenas para teste, pode remover depois)
@app.route("/criar_usuario", methods=["GET", "POST"])
def criar_usuario():
    erro = None
    if request.method == "POST":
        cpf = request.form.get("usuario")
        senha = request.form.get("senha")
        nome = request.form.get("nome")

        if not cpf or not senha or not nome:
            erro = "Preencha todos os campos"
        else:
            usuarios = carregar_json(USUARIOS_FILE)
            if cpf in usuarios:
                erro = "Usuário já existe"
            else:
                usuarios[cpf] = {
                    "nome": nome,
                    "senha": generate_password_hash(senha)
                }
                salvar_json(USUARIOS_FILE, usuarios)
                flash("Usuário criado com sucesso!", "success")
                return redirect(url_for("login"))

    return render_template("criar_usuario.html", erro=erro)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
