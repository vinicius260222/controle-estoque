import os
from flask import Flask, render_template, request, redirect, session, url_for, send_file
from openpyxl import Workbook
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chave-secreta-super-segura")

DATA_DIR = "/tmp/cpec_data"
os.makedirs(DATA_DIR, exist_ok=True)

ARQUIVO_ESTOQUE = os.path.join(DATA_DIR, "estoque.json")
ARQUIVO_CAIXA = os.path.join(DATA_DIR, "caixa.json")
ARQUIVO_USUARIOS = os.path.join(DATA_DIR, "usuarios.json")
ARQUIVO_NOMES = os.path.join(DATA_DIR, "nomes.json")
ARQUIVO_MOVIMENTOS = os.path.join(DATA_DIR, "movimentos.json")
ARQUIVO_DESPESAS = os.path.join(DATA_DIR, "despesas.json")
ARQUIVO_FUNCIONARIOS = os.path.join(DATA_DIR, "funcionarios.json")
ARQUIVO_PONTO = os.path.join(DATA_DIR, "ponto.json")

def carregar_json(arquivo, padrao):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Erro no {arquivo}, retornando padrão")
    return padrao

def salvar_json(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def carregar_usuarios():
    padrao = {
        "04932346913": "02111982",
        "00766969959": "01061981",
        "13455528902": "06102006"
    }
    usuarios = carregar_json(ARQUIVO_USUARIOS, padrao)
    if not usuarios:
        salvar_json(ARQUIVO_USUARIOS, padrao)
        usuarios = padrao
    return {str(k): str(v) for k, v in usuarios.items()}

def carregar_nomes():
    padrao = {
        "04932346913": "Carlos",
        "00766969959": "Fernanda",
        "13455528902": "Vinicius"
    }
    nomes = carregar_json(ARQUIVO_NOMES, padrao)
    if not nomes:
        salvar_json(ARQUIVO_NOMES, padrao)
        nomes = padrao
    return {str(k): str(v) for k, v in nomes.items()}

def registrar_movimento(produto, quantidade, tipo, usuario):
    movimentos = carregar_json(ARQUIVO_MOVIMENTOS, [])
    movimentos.append({
        "produto": produto,
        "quantidade": quantidade,
        "tipo": tipo,
        "usuario": usuario,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    })
    salvar_json(ARQUIVO_MOVIMENTOS, movimentos)

def registrar_despesa(descricao, empresa, valor, pagamento, vencimento, usuario):
    despesas = carregar_json(ARQUIVO_DESPESAS, [])
    despesas.append({
        "descricao": descricao,
        "empresa": empresa,
        "valor": valor,
        "pagamento": pagamento,
        "vencimento": vencimento if pagamento == "prazo" else "",
        "usuario": usuario,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    })
    salvar_json(ARQUIVO_DESPESAS, despesas)

def carregar_funcionarios():
    return carregar_json(ARQUIVO_FUNCIONARIOS, {})

def salvar_funcionarios(funcionarios):
    salvar_json(ARQUIVO_FUNCIONARIOS, funcionarios)

def carregar_ponto():
    return carregar_json(ARQUIVO_PONTO, {})

def salvar_ponto(ponto):
    salvar_json(ARQUIVO_PONTO, ponto)

# ---------------- ROTAS ----------------

@app.route("/")
def raiz():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    usuarios = carregar_usuarios()
    nomes = carregar_nomes()
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "").strip()
        if usuario in usuarios and usuarios[usuario] == senha:
            session["usuario"] = usuario
            session["nome_usuario"] = nomes.get(usuario, f"Usuário {usuario}")
            return redirect(url_for("home"))
        else:
            erro = "CPF ou data de nascimento incorretos"
    return render_template("login.html", erro=erro)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/home")
def home():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("home.html", nome_usuario=session["nome_usuario"])

# As demais rotas continuam iguais (cadastro, producao, movimentacoes, despesas, funcionarios, ponto, exportar)
# Certifique-se que os nomes das funções sejam exatamente:
# cadastro, producao, movimentacoes, despesas, funcionarios, ponto, exportar
# para que os links do menu funcionem corretamente

# ---------------- START ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
