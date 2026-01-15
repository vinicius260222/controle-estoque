import os
import json
from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = "chave-super-segura"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USUARIOS_FILE = os.path.join(BASE_DIR, "usuarios.json")


def carregar_json(caminho):
    if not os.path.exists(caminho):
        return {}
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None

    if request.method == "POST":
        # Remove espaços extras
        cpf = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "").strip()

        if not cpf or not senha:
            erro = "Preencha todos os campos"
        else:
            usuarios = carregar_json(USUARIOS_FILE)

            if cpf in usuarios and usuarios[cpf]["senha"] == senha:
                session["usuario"] = cpf
                session["nome"] = usuarios[cpf]["nome"]
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
