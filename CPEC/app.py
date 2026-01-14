from flask import Flask, render_template, request, redirect, session, url_for, send_file
from openpyxl import Workbook
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chave-secreta-super-segura")

# ---------- ARQUIVOS ----------
ARQUIVO_ESTOQUE = "estoque.json"
ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_CAIXA = "caixa.json"
ARQUIVO_MOVIMENTOS = "movimentos.json"

# ---------- FUNÇÕES AUXILIARES ----------

def carregar_json(arquivo, padrao):
    """Carrega qualquer JSON de forma segura."""
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Erro no {arquivo}: retornando valor padrão")
    return padrao

def salvar_json(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def carregar_usuarios():
    """Carrega usuarios.json de forma segura, retorna dict vazio se houver erro."""
    usuarios = carregar_json(ARQUIVO_USUARIOS, {})
    if not isinstance(usuarios, dict):
        return {}
    # garante que chaves e valores sejam strings
    return {str(k): str(v) for k, v in usuarios.items()}

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

# ---------- ROTAS ----------

@app.route("/", methods=["GET"])
def home():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("home.html", usuario=session["usuario"])

@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    usuarios = carregar_usuarios()
    if not usuarios:
        # Cria admin padrão se JSON vazio ou inválido
        usuarios = {"12345678900": "01011990"}
        salvar_json(ARQUIVO_USUARIOS, usuarios)

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()  # CPF
        senha = request.form.get("senha", "").strip()      # Data de nascimento ddmmaaaa
        if usuario in usuarios and usuarios[usuario] == senha:
            session["usuario"] = usuario
            return redirect(url_for("home"))
        else:
            erro = "CPF ou data de nascimento incorretos"
    return render_template("login.html", erro=erro)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- Cadastro de produtos ----------------

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if "usuario" not in session:
        return redirect(url_for("login"))
    estoque = carregar_json(ARQUIVO_ESTOQUE, {})
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        preco = float(request.form.get("preco", 0))
        categoria = request.form.get("categoria", "").strip()
        fornecedor = request.form.get("fornecedor", "").strip()
        if nome not in estoque:
            estoque[nome] = {"quantidade": 0, "preco": preco, "categoria": categoria, "fornecedor": fornecedor}
        else:
            # Atualiza info de cadastro se já existe
            estoque[nome]["preco"] = preco
            estoque[nome]["categoria"] = categoria
            estoque[nome]["fornecedor"] = fornecedor
        salvar_json(ARQUIVO_ESTOQUE, estoque)
        return redirect(url_for("cadastro"))
    return render_template("cadastro.html", estoque=estoque, usuario=session["usuario"])

# ---------------- Registrar produções ----------------

@app.route("/producao", methods=["GET", "POST"])
def producao():
    if "usuario" not in session:
        return redirect(url_for("login"))
    estoque = carregar_json(ARQUIVO_ESTOQUE, {})
    caixa = carregar_json(ARQUIVO_CAIXA, {"saldo": 0})
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        quantidade = int(request.form.get("quantidade", 0))
        tipo = request.form.get("tipo")
        preco = estoque[nome]["preco"] if nome in estoque else 0
        if nome not in estoque:
            estoque[nome] = {"quantidade": 0, "preco": preco, "categoria": "", "fornecedor": ""}
        if tipo == "entrada":
            estoque[nome]["quantidade"] += quantidade
        else:
            estoque[nome]["quantidade"] -= quantidade
            if estoque[nome]["quantidade"] < 0:
                estoque[nome]["quantidade"] = 0
            caixa["saldo"] += quantidade * preco
        salvar_json(ARQUIVO_ESTOQUE, estoque)
        salvar_json(ARQUIVO_CAIXA, caixa)
        registrar_movimento(nome, quantidade, tipo, session["usuario"])
        return redirect(url_for("producao"))
    return render_template("producao.html", estoque=estoque, caixa=caixa["saldo"], usuario=session["usuario"])

# ---------------- Movimentações ----------------

@app.route("/movimentacoes", methods=["GET"])
def movimentacoes():
    if "usuario" not in session:
        return redirect(url_for("login"))
    movimentos = carregar_json(ARQUIVO_MOVIMENTOS, [])
    return render_template("movimentacoes.html", movimentos=movimentos, usuario=session["usuario"])

# ---------------- Exportar Estoque ----------------

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
