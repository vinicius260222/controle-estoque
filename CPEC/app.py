import os
from flask import Flask, render_template, request, redirect, session, url_for, send_file
from openpyxl import Workbook
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chave-secreta-super-segura")

DATA_DIR = "/tmp/cpec_data"
os.makedirs(DATA_DIR, exist_ok=True)

# Arquivos
ARQUIVO_ESTOQUE = os.path.join(DATA_DIR, "estoque.json")
ARQUIVO_CAIXA = os.path.join(DATA_DIR, "caixa.json")
ARQUIVO_USUARIOS = os.path.join(DATA_DIR, "usuarios.json")
ARQUIVO_NOMES = os.path.join(DATA_DIR, "nomes.json")
ARQUIVO_MOVIMENTOS = os.path.join(DATA_DIR, "movimentos.json")
ARQUIVO_DESPESAS = os.path.join(DATA_DIR, "despesas.json")
ARQUIVO_FUNCIONARIOS = os.path.join(DATA_DIR, "funcionarios.json")
ARQUIVO_PONTO = os.path.join(DATA_DIR, "ponto.json")

# -------- Funções auxiliares --------

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

# --------- Rotas ---------

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

# -------- Cadastro de Produtos --------
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if "usuario" not in session:
        return redirect(url_for("login"))
    estoque = carregar_json(ARQUIVO_ESTOQUE, {})
    if request.method == "POST":
        nome = request.form.get("nome")
        preco = float(request.form.get("preco", 0))
        categoria = request.form.get("categoria", "")
        fornecedor = request.form.get("fornecedor", "")
        if nome not in estoque:
            estoque[nome] = {"quantidade": 0, "preco": preco, "categoria": categoria, "fornecedor": fornecedor}
        salvar_json(ARQUIVO_ESTOQUE, estoque)
        return redirect(url_for("cadastro"))
    return render_template("cadastro.html", estoque=estoque)

# -------- Produção --------
@app.route("/producao", methods=["GET", "POST"])
def producao():
    if "usuario" not in session:
        return redirect(url_for("login"))
    estoque = carregar_json(ARQUIVO_ESTOQUE, {})
    caixa = carregar_json(ARQUIVO_CAIXA, {"saldo": 0})
    movimentos = carregar_json(ARQUIVO_MOVIMENTOS, [])
    if request.method == "POST":
        nome = request.form.get("nome")
        quantidade = int(request.form.get("quantidade", 0))
        tipo = request.form.get("tipo")
        if nome not in estoque:
            estoque[nome] = {"quantidade": 0, "preco": 0, "categoria": "", "fornecedor": ""}
        if tipo == "entrada":
            estoque[nome]["quantidade"] += quantidade
        else:
            estoque[nome]["quantidade"] -= quantidade
            if estoque[nome]["quantidade"] < 0:
                estoque[nome]["quantidade"] = 0
            caixa["saldo"] += quantidade * estoque[nome]["preco"]
        movimentos.append({
            "produto": nome,
            "quantidade": quantidade,
            "tipo": tipo,
            "usuario": session["nome_usuario"],
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        })
        salvar_json(ARQUIVO_ESTOQUE, estoque)
        salvar_json(ARQUIVO_CAIXA, caixa)
        salvar_json(ARQUIVO_MOVIMENTOS, movimentos)
        return redirect(url_for("producao"))
    return render_template("producao.html", estoque=estoque, caixa=caixa["saldo"])

# -------- Movimentações --------
@app.route("/movimentacoes")
def movimentacoes():
    if "usuario" not in session:
        return redirect(url_for("login"))
    movimentos = carregar_json(ARQUIVO_MOVIMENTOS, [])
    return render_template("movimentacoes.html", movimentos=movimentos)

# -------- Despesas --------
@app.route("/despesas", methods=["GET", "POST"])
def despesas():
    if "usuario" not in session:
        return redirect(url_for("login"))
    despesas_lista = carregar_json(ARQUIVO_DESPESAS, [])
    if request.method == "POST":
        descricao = request.form.get("descricao")
        empresa = request.form.get("empresa")
        valor = float(request.form.get("valor", 0))
        pagamento = request.form.get("pagamento")
        vencimento = request.form.get("vencimento")
        despesas_lista.append({
            "descricao": descricao,
            "empresa": empresa,
            "valor": valor,
            "pagamento": pagamento,
            "vencimento": vencimento if pagamento=="prazo" else "",
            "usuario": session["nome_usuario"],
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        })
        salvar_json(ARQUIVO_DESPESAS, despesas_lista)
        return redirect(url_for("despesas"))
    return render_template("despesas.html", despesas=despesas_lista)

# -------- Funcionários --------
@app.route("/funcionarios", methods=["GET", "POST"])
def funcionarios():
    if "usuario" not in session:
        return redirect(url_for("login"))
    funcionarios_dict = carregar_json(ARQUIVO_FUNCIONARIOS, {})
    if request.method == "POST":
        cpf = request.form.get("cpf")
        funcionarios_dict[cpf] = {
            "nome": request.form.get("nome"),
            "idade": request.form.get("idade"),
            "data_inicio": request.form.get("data_inicio"),
            "cargo": request.form.get("cargo"),
            "observacoes": request.form.get("observacoes")
        }
        salvar_json(ARQUIVO_FUNCIONARIOS, funcionarios_dict)
        return redirect(url_for("funcionarios"))
    return render_template("funcionarios.html", funcionarios=funcionarios_dict)

# -------- Ponto --------
@app.route("/ponto", methods=["GET", "POST"])
def ponto():
    if "usuario" not in session:
        return redirect(url_for("login"))
    ponto_dict = carregar_json(ARQUIVO_PONTO, {})
    funcionarios_dict = carregar_json(ARQUIVO_FUNCIONARIOS, {})
    if request.method == "POST":
        cpf = request.form.get("cpf")
        data = request.form.get("data")
        status = request.form.get("status")
        if cpf not in ponto_dict:
            ponto_dict[cpf] = []
        ponto_dict[cpf].append({"data": data, "status": status})
        salvar_json(ARQUIVO_PONTO, ponto_dict)
        return redirect(url_for("ponto"))
    return render_template("ponto.html", ponto=ponto_dict, funcionarios=funcionarios_dict)

# -------- Exportar Estoque --------
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
    caminho = os.path.join(DATA_DIR, "estoque.xlsx")
    wb.save(caminho)
    return send_file(caminho, as_attachment=True, download_name="estoque.xlsx")

# -------- Iniciar --------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
