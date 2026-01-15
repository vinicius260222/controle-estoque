from flask import Flask, render_template, request, redirect, session, url_for
import json
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chave-secreta-super-segura")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

USUARIOS_FILE = os.path.join(BASE_DIR, "usuarios.json")
NOMES_FILE = os.path.join(BASE_DIR, "nomes.json")


# ---------- FUNÇÕES AUXILIARES ----------

def carregar_usuarios():
    if not os.path.exists(USUARIOS_FILE):
        return {}
    with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def carregar_nomes():
    if not os.path.exists(NOMES_FILE):
        return {}
    with open(NOMES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------- ROTAS ----------

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None

    if request.method == "POST":
        cpf = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "").strip()

        usuarios = carregar_usuarios()
        nomes = carregar_nomes()

        if cpf in usuarios and usuarios[cpf] == senha:
            session["usuario"] = cpf
            session["nome"] = nomes.get(cpf, "Usuário")
            return redirect(url_for("home"))
        else:
            erro = "Usuário ou senha inválidos"

    return render_template("login.html", erro=erro)


@app.route("/home")
def home():
    if "usuario" not in session:
        return redirect(url_for("login"))

    return render_template(
        "home.html",
        nome=session.get("nome")
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- START ----------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
