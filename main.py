import os
import uuid
import shutil
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, send_from_directory
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from flasgger import Swagger
from flask_cors import CORS

# Importar nossa configuração de DB e modelos
from database import Base, engine, SessionLocal
from models import (
    Cliente, Loja, Produto, Servico, ReservaServico, ReservaProduto,
    Carrinho, ServicoHorario, ItemReserva, ItemReserva, ReservaProduto
)

# Garantir que o diretório de imagens exista
if not os.path.exists("images"):
    os.makedirs("images")

app = Flask(__name__)
swagger = Swagger(app)  # Inicializa o Flasgger
CORS(app)

@app.route("/images/<path:filename>")
def serve_image(filename):
    """Serve arquivos de imagem do diretório /images."""
    return send_from_directory("images", filename)

# Criar as tabelas no banco
Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_db():
    """Função utilitária para obter sessão do banco de dados."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------------------
#  ROTAS DE CLIENTE (Registro / Login)
# -------------------------------------------

@app.route("/cliente/registro", methods=["POST"])
def registrar_cliente():
    """
    Registra um novo cliente.
    ---
    tags:
      - Cliente
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nome:
              type: string
              description: Nome do cliente
            idade:
              type: integer
              description: Idade do cliente
            cpf:
              type: string
              description: CPF do cliente (único)
            senha:
              type: string
              description: Senha para login
    responses:
      200:
        description: Cliente registrado com sucesso
      400:
        description: Dados incompletos ou CPF já existente
    """
    db: Session = next(get_db())
    data = request.get_json()
    nome = data.get("nome")
    idade = data.get("idade")
    cpf = data.get("cpf")
    senha = data.get("senha")

    if not nome or not idade or not cpf or not senha:
        return jsonify(detail="Dados incompletos."), 400

    if db.query(Cliente).filter(Cliente.cpf == cpf).first():
        return jsonify(detail="CPF já cadastrado."), 400

    novo_cliente = Cliente(
        nome=nome,
        idade=int(idade),
        cpf=cpf,
        senha_hash=hash_password(senha)
    )
    db.add(novo_cliente)
    db.commit()
    db.refresh(novo_cliente)
    return jsonify(mensagem="Cliente registrado com sucesso", cliente_id=novo_cliente.id)

@app.route("/cliente/login", methods=["POST"])
def login_cliente():
    """
    Realiza login de um cliente.
    ---
    tags:
      - Cliente
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            cpf:
              type: string
            senha:
              type: string
    responses:
      200:
        description: Login realizado com sucesso
      400:
        description: CPF não encontrado ou dados incompletos
      401:
        description: Senha incorreta
    """
    db: Session = next(get_db())
    data = request.get_json()
    cpf = data.get("cpf")
    senha = data.get("senha")

    if not cpf or not senha:
        return jsonify(detail="Dados de login incompletos."), 400

    cliente_db = db.query(Cliente).filter(Cliente.cpf == cpf).first()
    if not cliente_db:
        return jsonify(detail="CPF não encontrado."), 400
    
    if not verify_password(senha, cliente_db.senha_hash):
        return jsonify(detail="Senha incorreta."), 401
    
    return jsonify(mensagem="Login de cliente realizado com sucesso", cliente_id=cliente_db.id)


# -------------------------------------------
#  ROTAS DE LOJA (Registro / Login)
# -------------------------------------------

@app.route("/loja/registro", methods=["POST"])
def registrar_loja():
    """
    Registra uma nova loja.
    ---
    tags:
      - Loja
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nome_loja:
              type: string
            cnpj:
              type: string
            cep:
              type: string
            endereco:
              type: string
            complemento:
              type: string
            lote:
              type: string
            senha:
              type: string
            latitude:
              type: number
            longitude:
              type: number
    responses:
      200:
        description: Loja registrada com sucesso
      400:
        description: Dados incompletos ou CNPJ já cadastrado
    """
    db: Session = next(get_db())
    data = request.get_json()

    nome_loja = data.get("nome_loja")
    cnpj = data.get("cnpj")
    cep = data.get("cep")
    endereco = data.get("endereco")
    complemento = data.get("complemento")
    lote = data.get("lote")
    senha = data.get("senha")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if not (nome_loja and cnpj and cep and endereco and senha):
        return jsonify(detail="Dados incompletos para cadastro de loja."), 400

    if db.query(Loja).filter(Loja.cnpj == cnpj).first():
        return jsonify(detail="CNPJ já cadastrado."), 400
    
    nova_loja = Loja(
        nome_loja=nome_loja,
        cnpj=cnpj,
        cep=cep,
        endereco=endereco,
        complemento=complemento,
        lote=lote,
        senha_hash=hash_password(senha),
        latitude=float(latitude) if latitude else None,
        longitude=float(longitude) if longitude else None
    )
    db.add(nova_loja)
    db.commit()
    db.refresh(nova_loja)
    return jsonify(mensagem="Loja registrada com sucesso", loja_id=nova_loja.id)

@app.route("/loja/login", methods=["POST"])
def login_loja():
    """
    Realiza login de uma loja.
    ---
    tags:
      - Loja
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            cnpj:
              type: string
            senha:
              type: string
    responses:
      200:
        description: Login realizado com sucesso
      400:
        description: Dados incompletos ou CNPJ não encontrado
      401:
        description: Senha incorreta
    """
    db: Session = next(get_db())
    data = request.get_json()

    cnpj = data.get("cnpj")
    senha = data.get("senha")

    if not cnpj or not senha:
        return jsonify(detail="Dados de login incompletos para loja."), 400

    loja_db = db.query(Loja).filter(Loja.cnpj == cnpj).first()
    if not loja_db:
        return jsonify(detail="CNPJ não encontrado."), 400
    
    if not verify_password(senha, loja_db.senha_hash):
        return jsonify(detail="Senha incorreta."), 401
    
    return jsonify(mensagem="Login de loja realizado com sucesso", loja_id=loja_db.id)

@app.route("/loja/<int:loja_id>", methods=["GET"])
def obter_detalhes_loja(loja_id):
    """
    Retorna as informações de uma loja específica.
    ---
    tags:
      - Loja
    parameters:
      - name: loja_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Detalhes da loja
        schema:
          type: object
          properties:
            id: { type: integer }
            nome_loja: { type: string }
            cnpj: { type: string }
            cep: { type: string }
            endereco: { type: string }
            complemento: { type: string }
            lote: { type: string }
            latitude: { type: number }
            longitude: { type: number }
      404:
        description: Loja não encontrada
    """
    db: Session = next(get_db())
    loja = db.query(Loja).filter(Loja.id == loja_id).first()
    if not loja:
        return jsonify(detail="Loja não encontrada."), 404
    return jsonify(
        id=loja.id, nome_loja=loja.nome_loja, cnpj=loja.cnpj, cep=loja.cep, endereco=loja.endereco, complemento=loja.complemento, lote=loja.lote, latitude=loja.latitude, longitude=loja.longitude,
        foto_path = loja.foto_path, descricao = loja.descricao
    )


# -------------------------------------------
#  PRODUTOS (Exemplo que mantém form-data para upload de imagem)
# -------------------------------------------

@app.route("/loja/<int:loja_id>/produto_com_imagem", methods=["POST"])
def cadastrar_produto_com_imagem(loja_id):
    """
    Cadastra um novo produto (com imagem) para a loja especificada.
    ---
    tags:
      - Produtos
    consumes:
      - multipart/form-data
    parameters:
      - name: loja_id
        in: path
        type: integer
        required: true
      - name: nome_produto
        in: formData
        type: string
        required: true
      - name: preco
        in: formData
        type: number
        required: true
      - name: quantidade_estoque
        in: formData
        type: integer
        required: true
      - name: arquivo
        in: formData
        type: file
        required: true
        description: Imagem do produto
    responses:
      200:
        description: Produto cadastrado com sucesso
      400:
        description: Dados incompletos ou arquivo inválido
      404:
        description: Loja não encontrada
    """
    db: Session = next(get_db())

    loja = db.query(Loja).filter(Loja.id == loja_id).first()
    if not loja:
        return jsonify(detail="Loja não encontrada."), 404

    nome_produto = request.form.get("nome_produto")
    preco = request.form.get("preco")
    quantidade_estoque = request.form.get("quantidade_estoque")

    if not nome_produto or not preco or not quantidade_estoque:
        return jsonify(detail="Dados de produto incompletos."), 400

    arquivo = request.files.get("arquivo")
    if not arquivo:
        return jsonify(detail="Arquivo de imagem não foi enviado."), 400

    if not arquivo.content_type.startswith("image/"):
        return jsonify(detail="Arquivo não é uma imagem válida."), 400

    ext = arquivo.filename.split(".")[-1]
    nome_arquivo = f"loja_{loja_id}_{uuid.uuid4()}.{ext}"
    caminho_arquivo = os.path.join("images", nome_arquivo)

    with open(caminho_arquivo, "wb") as buffer:
        shutil.copyfileobj(arquivo, buffer)

    novo_produto = Produto(
        nome_produto=nome_produto,
        preco=float(preco),
        loja_id=loja_id,
        image_path=caminho_arquivo,
        quantidade_estoque=int(quantidade_estoque),
    )
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)

    return jsonify(
        mensagem="Produto cadastrado com sucesso",
        produto_id=novo_produto.id,
        image_path=novo_produto.image_path
    )

@app.route("/loja/<int:loja_id>/produtos", methods=["GET"])
def listar_produtos_loja(loja_id):
    """
    Retorna todos os produtos de uma loja específica.
    ---
    tags:
      - Produtos
    parameters:
      - name: loja_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Lista de produtos da loja
        schema:
          type: array
          items:
            type: object
            properties:
              id: { type: integer }
              nome_produto: { type: string }
              preco: { type: number }
              image_path: { type: string }
      404:
        description: Loja não encontrada
    """
    db: Session = next(get_db())
    loja = db.query(Loja).filter(Loja.id == loja_id).first()
    if not loja:
        return jsonify(detail="Loja não encontrada."), 404
    produtos = db.query(Produto).filter(Produto.loja_id == loja_id).all()
    return jsonify([
    {"id": p.id, "nome_produto": p.nome_produto, "preco": p.preco, "image_path": p.image_path, "quantidade_estoque": p.quantidade_estoque}
    for p in produtos
])


@app.route("/loja/<int:loja_id>/produto/<int:produto_id>", methods=["DELETE"])
def remover_produto(loja_id, produto_id):
    """
    Remove um produto de determinada loja.
    ---
    tags:
      - Produtos
    parameters:
      - name: loja_id
        in: path
        type: integer
        required: true
      - name: produto_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Produto removido com sucesso
      404:
        description: Produto não encontrado ou não pertence à loja
    """
    db: Session = next(get_db())
    produto = db.query(Produto).filter(

 # Check if the product exists and belongs to the specified store
        Produto.id == produto_id,
        Produto.loja_id == loja_id
    ).first()

    if not produto:
        return jsonify(detail="Produto não encontrado ou não pertence à loja informada."), 404

    db.delete(produto)
    db.commit()

 # Delete the associated image file
    if produto.image_path and os.path.exists(produto.image_path):
        os.remove(produto.image_path)


    return jsonify(mensagem="Produto removido com sucesso.")


# -------------------------------------------
#  RESERVA PRODUTO (fluxo de retirada, etc.)
# -------------------------------------------

@app.route("/loja/<int:loja_id>/reserva/<int:reserva_id>/marcar_retirada", methods=["PUT"])
def marcar_retirada(loja_id, reserva_id):
    """
    Marca uma reserva de produto como RETIRADA (feito pela loja).
    ---
    tags:
      - Reservas
    parameters:
      - name: loja_id
        in: path
        type: integer
        required: true
      - name: reserva_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Reserva marcada como RETIRADA
      400:
        description: Status inválido para esta operação
      404:
        description: Reserva não encontrada para esta loja
    """
    db: Session = next(get_db())
    reserva = db.query(ReservaProduto).filter(
        ReservaProduto.id == reserva_id,
        ReservaProduto.loja_id == loja_id
    ).first()
    if not reserva:
        return jsonify(detail="Reserva não encontrada para esta loja."), 404
    
    if reserva.status != "RESERVADO":
        return jsonify(detail=f"Não é possível marcar retirada com status {reserva.status}."), 400

    reserva.status = "RETIRADO"
    db.commit()
    db.refresh(reserva)
    return jsonify(mensagem="Reserva marcada como RETIRADA.")

@app.route("/loja/<int:loja_id>/reservas/cancelar_expiradas", methods=["PUT"])
def cancelar_expiradas(loja_id):
    """
    Cancela reservas de produto que estejam expiradas ou fora do prazo de retirada.
    ---
    tags:
      - Reservas
    parameters:
      - name: loja_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Reservas expiradas canceladas e estoque devolvido
    """
    db: Session = next(get_db())
    agora = datetime.utcnow()

    # Reservas vencidas pela data_limite
    reservas_expiradas_2dias = db.query(ReservaProduto).filter(
        ReservaProduto.loja_id == loja_id,
        ReservaProduto.status == "RESERVADO",
        ReservaProduto.data_limite < agora
    ).all()

    for reserva in reservas_expiradas_2dias:
        reserva.status = "CANCELADO"
        for item in reserva.itens:
            produto = db.query(Produto).filter(Produto.id == item.produto_id).first()
            produto.quantidade_estoque += item.quantidade
        db.commit()

    # Reservas não retiradas até 4 dias
    reservas_expiradas_4dias = db.query(ReservaProduto).filter(
        ReservaProduto.loja_id == loja_id,
        ReservaProduto.status == "RESERVADO",
        ReservaProduto.data_reserva + timedelta(days=4) < agora
    ).all()

    for reserva in reservas_expiradas_4dias:
        reserva.status = "CANCELADO"
        for item in reserva.itens:
            produto = db.query(Produto).filter(Produto.id == item.produto_id).first()
            produto.quantidade_estoque += item.quantidade
        db.commit()

    return jsonify(mensagem="Reservas expiradas foram canceladas e estoque devolvido.")


# -------------------------------------------
#  SERVIÇOS
# -------------------------------------------

@app.route("/loja/<int:loja_id>/servicos", methods=["GET"])
def listar_servicos_loja(loja_id):
    """
    Retorna todos os serviços de uma loja específica.
    ---
    tags:
      - Serviços
    parameters:
      - name: loja_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Lista de serviços da loja
        schema:
          type: array
          items:
            type: object
            properties:
              id: { type: integer }
              nome_servico: { type: string }
              preco: { type: number }
              descricao: { type: string}
      404:
        description: Loja não encontrada
    """
    db: Session = next(get_db())
    loja = db.query(Loja).filter(Loja.id == loja_id).first()
    if not loja:
        return jsonify(detail="Loja não encontrada."), 404
    
    servicos = db.query(Servico).filter(Servico.loja_id == loja_id).all()
    return jsonify(servicos=[{
        "id": s.id, "nome_servico": s.nome_servico, "preco": s.preco, "descricao": s.descricao
        } for s in servicos])

@app.route("/loja/<int:loja_id>/servico", methods=["POST"])
def cadastrar_servico(loja_id):
    """
    Cadastra um novo serviço para a loja.
    ---
    tags:
      - Serviços
    consumes:
      - application/json
    parameters:
      - name: loja_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nome_servico:
              type: string
            preco:
              type: number
            descricao:
              type: string
    responses:
      200:
        description: Serviço cadastrado com sucesso
      400:
        description: Dados incompletos
      404:
        description: Loja não encontrada
    """
    db: Session = next(get_db())
    data = request.get_json()

    nome_servico = data.get("nome_servico")
    preco = data.get("preco")
    descricao = data.get("descricao") or ""

    loja = db.query(Loja).filter(Loja.id == loja_id).first()
    if not loja:
        return jsonify(detail="Loja não encontrada."), 404
    
    if not nome_servico or preco is None:
        return jsonify(detail="Dados insuficientes para criar serviço."), 400

    novo_servico = Servico(
        nome_servico=nome_servico,
        preco=float(preco),
        descricao=descricao,
        loja_id=loja_id
    )
    db.add(novo_servico)
    db.commit()
    db.refresh(novo_servico)
    return jsonify(mensagem="Serviço cadastrado com sucesso", servico_id=novo_servico.id)

@app.route("/loja/<int:loja_id>/servico/<int:servico_id>", methods=["DELETE"])
def remover_servico(loja_id, servico_id):
    db: Session = next(get_db())
    servico = (
        db.query(Servico)
          .filter(Servico.id == servico_id, Servico.loja_id == loja_id)
          .first()
    )
    if not servico:
        return jsonify(detail="Serviço não encontrado ou não pertence à loja informada."), 404

    # Só isso já é suficiente:
    db.delete(servico)
    db.commit()
    return jsonify(mensagem="Serviço removido com sucesso."), 200

@app.route("/loja/<int:loja_id>/servico/<int:servico_id>/horarios", methods=["GET"])
def listar_horarios_servico(loja_id, servico_id):
    """
    Lista os horários disponíveis para um serviço específico em uma loja.
    ---
    tags:
      - Serviços
    parameters:
      - name: loja_id
        in: path
        type: integer
        required: true
      - name: servico_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Retorna lista de horários do serviço
      404:
        description: Serviço não encontrado para a loja
    """
    db: Session = next(get_db())
    servico = db.query(Servico).filter(
        Servico.id == servico_id,
        Servico.loja_id == loja_id
    ).first()
    if not servico:
        return jsonify(detail="Serviço não encontrado para esta loja."), 404

    horarios = db.query(ServicoHorario).filter(
        ServicoHorario.servico_id == servico_id
    ).all()

    return jsonify(horarios_servico=[{
        "id": h.id, "horario": h.horario, "is_disponivel": h.is_disponivel
    } for h in horarios])

@app.route("/loja/<int:loja_id>/servico/<int:servico_id>/horarios", methods=["POST"])
def criar_horarios_servico(loja_id, servico_id):
    """
    Cria horários disponíveis para um serviço.
    ---
    tags:
      - Serviços
    consumes:
      - application/json
    parameters:
      - name: loja_id
        in: path
        type: integer
        required: true
      - name: servico_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            horarios:
              type: array
              items:
                type: string
              example: ["2025-03-28T13:00:00", "2025-03-28T14:00:00"]
    responses:
      200:
        description: Horários adicionados com sucesso
      400:
        description: Lista de horários não fornecida
      404:
        description: Serviço não encontrado para a loja
    """
    db: Session = next(get_db())
    data_json = request.get_json()
    if not data_json or "horarios" not in data_json:
        return jsonify(detail="É necessário enviar uma lista de horários no corpo (JSON)."), 400
    
    horarios = data_json["horarios"]  # lista de strings no formato datetime

    servico = db.query(Servico).filter(
        Servico.id == servico_id,
        Servico.loja_id == loja_id
    ).first()
    if not servico:
        return jsonify(detail="Serviço não encontrado para esta loja."), 404

    for h_str in horarios:
        try:
            h = datetime.fromisoformat(h_str)
        except ValueError:
            continue  # ou retornar erro

        existe = db.query(ServicoHorario).filter(
            ServicoHorario.servico_id == servico_id,
            ServicoHorario.horario == h
        ).first()
        if existe:
            continue

        novo_horario = ServicoHorario(
            servico_id=servico_id,
            horario=h,
            is_disponivel=True
        )
        db.add(novo_horario)

    db.commit()
    return jsonify(mensagem="Horários adicionados ao serviço com sucesso.")

@app.route("/loja/<int:loja_id>/agenda", methods=["GET"])
def ver_agenda_reservas(loja_id):
    """
    Exibe a agenda de reservas de serviços de uma loja.
    ---
    tags:
      - Serviços
    parameters:
      - name: loja_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Retorna a lista de reservas de serviço
      404:
        description: Loja não encontrada
    """
    db: Session = next(get_db())
    loja = db.query(Loja).filter(Loja.id == loja_id).first()
    if not loja:
        return jsonify(detail="Loja não encontrada."), 404

    reservas = db.query(ReservaServico).filter(ReservaServico.loja_id == loja_id).all()
    retorno = []
    for r in reservas:
        retorno.append({
            "reserva_id": r.id,
            "cliente_id": r.cliente_id,
            "servico_id": r.servico_id,
            "data_horario": r.data_horario,
            "status": r.status
        })
    return jsonify(agenda_loja=retorno)

@app.route("/loja/reserva/<int:reserva_id>/aceitar", methods=["PUT"])
def aceitar_reserva(reserva_id):
    """
    Aceita uma reserva de serviço.
    ---
    tags:
      - Serviços
    parameters:
      - name: reserva_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Reserva aceita com sucesso
      400:
        description: Reserva já está aceita
      404:
        description: Reserva não encontrada
    """
    db: Session = next(get_db())
    reserva = db.query(ReservaServico).filter(ReservaServico.id == reserva_id).first()
    if not reserva:
        return jsonify(detail="Reserva não encontrada."), 404

    if reserva.status == "ACEITO":
        return jsonify(detail="Reserva já está aceita."), 400

    reserva.status = "ACEITO"
    db.commit()
    db.refresh(reserva)
    return jsonify(mensagem="Reserva aceita com sucesso!")

@app.route("/loja/reserva/<int:reserva_id>/rejeitar", methods=["PUT"])
def rejeitar_reserva(reserva_id):
    """
    Rejeita uma reserva de serviço.
    ---
    tags:
      - Serviços
    parameters:
      - name: reserva_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Reserva rejeitada com sucesso
      400:
        description: Reserva já estava rejeitada
      404:
        description: Reserva não encontrada
    """
    db: Session = next(get_db())
    reserva = db.query(ReservaServico).filter(ReservaServico.id == reserva_id).first()
    if not reserva:
        return jsonify(detail="Reserva não encontrada."), 404

    if reserva.status == "REJEITADA":
        return jsonify(detail="Reserva já está rejeitada."), 400

    reserva.status = "REJEITADA"
    db.commit()
    db.refresh(reserva)
    return jsonify(mensagem="Reserva rejeitada com sucesso!")

# -------------------------------------------
#  ATUALIZAR PERFIL LOJA (mantido como multipart se enviar foto)
# -------------------------------------------

@app.route("/loja/<int:loja_id>/atualizar_perfil", methods=["PUT"])
def atualizar_perfil_loja(loja_id):
    """
    Atualiza informações de perfil de uma loja (nome, descrição, localização, foto).
    ---
    tags:
      - Loja
    consumes:
      - multipart/form-data
    parameters:
      - name: loja_id
        in: path
        type: integer
        required: true
      - name: nome_loja
        in: formData
        type: string
        required: false
      - name: descricao
        in: formData
        type: string
        required: false
      - name: latitude
        in: formData
        type: number
        required: false
      - name: longitude
        in: formData
        type: number
        required: false
      - name: arquivo
        in: formData
        type: file
        required: false
        description: Imagem/foto da loja
    responses:
      200:
        description: Perfil atualizado com sucesso
      400:
        description: Arquivo inválido
      404:
        description: Loja não encontrada
    """
    db: Session = next(get_db())
    loja = db.query(Loja).filter(Loja.id == loja_id).first()
    if not loja:
        return jsonify(detail="Loja não encontrada."), 404

    nome_loja = request.form.get("nome_loja")
    descricao = request.form.get("descricao")
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")
    arquivo = request.files.get("arquivo")

    if nome_loja is not None:
        loja.nome_loja = nome_loja

    if descricao is not None:
        loja.descricao = descricao

    if latitude is not None:
        loja.latitude = float(latitude)
    if longitude is not None:
        loja.longitude = float(longitude)

    if arquivo:
        if not arquivo.content_type.startswith("image/"):
            return jsonify(detail="O arquivo enviado não é uma imagem válida."), 400
        
        ext = arquivo.filename.split(".")[-1]
        nome_arquivo = f"loja_{loja_id}_{uuid.uuid4()}.{ext}"
        caminho_arquivo = os.path.join("images", nome_arquivo)
        with open(caminho_arquivo, "wb") as buffer:
            shutil.copyfileobj(arquivo, buffer)
        loja.foto_path = caminho_arquivo

    db.commit()
    db.refresh(loja)

    return jsonify(
        mensagem="Perfil da loja atualizado com sucesso.",
        loja_id=loja.id,
        nome_loja=loja.nome_loja,
        descricao=loja.descricao,
        latitude=loja.latitude,
        longitude=loja.longitude,
        foto_path=loja.foto_path
    )

# -------------------------------------------
#  CLIENTE - Visualizar Lojas, Produtos, Serviços
# -------------------------------------------

@app.route("/lojas", methods=["GET"])
def listar_lojas():
    """
    Lista todas as lojas cadastradas.
    ---
    tags:
      - Loja
    responses:
      200:
        description: Lista de lojas
    """
    db: Session = next(get_db())
    lojas = db.query(Loja).all()
    retorno = []
    for l in lojas:
        retorno.append({
            "loja_id": l.id,
            "nome_loja": l.nome_loja,
            "cnpj": l.cnpj,
            "endereco": l.endereco,
            "latitude": l.latitude,
            "longitude": l.longitude
        })
    return jsonify(lojas=retorno)

@app.route("/produtos", methods=["GET"])
def buscar_produtos():
    """
    Busca produtos, opcionalmente filtrando por loja_id e nome_produto.
    ---
    tags:
      - Produtos
    parameters:
      - name: loja_id
        in: query
        type: integer
        required: false
      - name: nome_produto
        in: query
        type: string
        required: false
    responses:
      200:
        description: Retorna lista de produtos
    """
    db: Session = next(get_db())

    loja_id = request.args.get("loja_id")
    nome_produto = request.args.get("nome_produto")

    query = db.query(Produto)
    if loja_id:
        query = query.filter(Produto.loja_id == int(loja_id))
    if nome_produto:
        query = query.filter(Produto.nome_produto.ilike(f"%{nome_produto}%"))
    produtos = query.all()

    resultado = []
    for p in produtos:
        resultado.append({
            "id": p.id,
            "nome_produto": p.nome_produto,
            "preco": p.preco,
            "loja_id": p.loja_id
        })
    return jsonify(produtos=resultado)

@app.route("/servicos", methods=["GET"])
def buscar_servicos():
    """
    Busca serviços, opcionalmente filtrando por loja_id e nome_servico.
    ---
    tags:
      - Serviços
    parameters:
      - name: loja_id
        in: query
        type: integer
        required: false
      - name: nome_servico
        in: query
        type: string
        required: false
    responses:
      200:
        description: Retorna lista de serviços
    """
    db: Session = next(get_db())
    loja_id = request.args.get("loja_id")
    nome_servico = request.args.get("nome_servico")

    query = db.query(Servico)
    if loja_id:
        query = query.filter(Servico.loja_id == int(loja_id))
    if nome_servico:
        query = query.filter(Servico.nome_servico.ilike(f"%{nome_servico}%"))
    servicos = query.all()

    resultado = []
    for s in servicos:
        resultado.append({
            "id": s.id,
            "nome_servico": s.nome_servico,
            "descricao": s.descricao,
            "preco": s.preco,
            "loja_id": s.loja_id
        })
    return jsonify(servicos=resultado)

# -------------------------------------------
#  CARRINHO DE COMPRAS
# -------------------------------------------

@app.route("/cliente/<int:cliente_id>/carrinho", methods=["POST"])
def adicionar_item_carrinho(cliente_id):
    """
    Adiciona um item ao carrinho do cliente.
    ---
    tags:
      - Carrinho
    consumes:
      - application/json
    parameters:
      - name: cliente_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            produto_id:
              type: integer
            quantidade:
              type: integer
              default: 1
    responses:
      200:
        description: Produto adicionado ou quantidade atualizada
      400:
        description: Dados incompletos ou produtos de outra loja
      404:
        description: Cliente ou produto não encontrado
    """
    db: Session = next(get_db())

    data = request.get_json()
    if not data:
        return jsonify(detail="É necessário informar os dados em JSON."), 400

    produto_id = data.get("produto_id")
    quantidade = data.get("quantidade", 1)

    if not produto_id:
        return jsonify(detail="É necessário informar produto_id."), 400
    
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        return jsonify(detail="Cliente não encontrado."), 404
    
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        return jsonify(detail="Produto não encontrado."), 404

    itens_existentes = db.query(Carrinho).filter(Carrinho.cliente_id == cliente_id).all()
    if itens_existentes:
        primeiro_item = itens_existentes[0]
        produto_primeiro_item = db.query(Produto).filter(Produto.id == primeiro_item.produto_id).first()
        if produto_primeiro_item.loja_id != produto.loja_id:
            return jsonify(detail="Carrinho contém produtos de outra loja. Remova-os antes."), 400

    item_existente = db.query(Carrinho).filter(
        Carrinho.cliente_id == cliente_id,
        Carrinho.produto_id == produto_id
    ).first()

    if item_existente:
        item_existente.quantidade += int(quantidade)
        db.commit()
        db.refresh(item_existente)
        return jsonify(mensagem="Quantidade atualizada no carrinho.")
    else:
        novo_item = Carrinho(
            cliente_id=cliente_id,
            produto_id=int(produto_id),
            quantidade=int(quantidade)
        )
        db.add(novo_item)
        db.commit()
        db.refresh(novo_item)
        return jsonify(mensagem="Produto adicionado ao carrinho.")

@app.route("/cliente/<int:cliente_id>/carrinho", methods=["DELETE"])
def remover_item_carrinho(cliente_id):
    """
    Remove um item do carrinho do cliente.
    ---
    tags:
      - Carrinho
    parameters:
      - name: cliente_id
        in: path
        type: integer
        required: true
      - name: produto_id
        in: query
        type: integer
        required: true
    responses:
      200:
        description: Item removido
      400:
        description: produto_id não informado
      404:
        description: Cliente não encontrado ou item não está no carrinho
    """
    db: Session = next(get_db())

    produto_id = request.args.get("produto_id")
    if not produto_id:
        return jsonify(detail="É necessário informar produto_id para remoção."), 400

    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        return jsonify(detail="Cliente não encontrado."), 404

    item = db.query(Carrinho).filter(
        Carrinho.cliente_id == cliente_id,
        Carrinho.produto_id == int(produto_id)
    ).first()

    if not item:
        return jsonify(detail="Item não está no carrinho."), 404

    db.delete(item)
    db.commit()
    return jsonify(mensagem="Item removido do carrinho.")

@app.route("/cliente/<int:cliente_id>/carrinho", methods=["GET"])
def visualizar_carrinho(cliente_id):
    """
    Exibe os itens do carrinho de um cliente.
    ---
    tags:
      - Carrinho
    parameters:
      - name: cliente_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Lista de itens do carrinho
      404:
        description: Cliente não encontrado
    """
    db: Session = next(get_db())
    itens = db.query(Carrinho).filter(Carrinho.cliente_id == cliente_id).all()
    resultado = []
    for i in itens:
        produto = db.query(Produto).filter(Produto.id == i.produto_id).first()
        resultado.append({
            "carrinho_item_id": i.id,
            "produto_id": i.produto_id,
            "nome_produto": produto.nome_produto if produto else None,
            "quantidade": i.quantidade,
            "preco_unitario": produto.preco if produto else None,
            "subtotal": (produto.preco * i.quantidade) if produto else None
        })
    return jsonify(itens_carrinho=resultado)

@app.route("/cliente/<int:cliente_id>/finalizar_carrinho", methods=["POST"])
def finalizar_carrinho(cliente_id):
    """
    Finaliza o carrinho de compras, criando uma reserva de produtos.
    ---
    tags:
      - Carrinho
    parameters:
      - name: cliente_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Reserva criada com sucesso
      400:
        description: Carrinho vazio, estoque insuficiente ou produtos de lojas diferentes
      404:
        description: Produto no carrinho não existe
    """
    db: Session = next(get_db())
    itens_carrinho = db.query(Carrinho).filter(Carrinho.cliente_id == cliente_id).all()

    if not itens_carrinho:
        return jsonify(detail="Carrinho está vazio."), 400

    loja_id = None

    for item in itens_carrinho:
        produto = db.query(Produto).filter(Produto.id == item.produto_id).first()
        if not produto:
            return jsonify(detail="Produto no carrinho não existe."), 404

        if loja_id is None:
            loja_id = produto.loja_id
        else:
            if produto.loja_id != loja_id:
                return jsonify(detail="Carrinho possui produtos de lojas diferentes."), 400

        if produto.quantidade_estoque < item.quantidade:
            return jsonify(detail=f"Estoque insuficiente para o produto {produto.nome_produto}."), 400

    # Abater estoque
    for item in itens_carrinho:
        produto = db.query(Produto).filter(Produto.id == item.produto_id).first()
        produto.quantidade_estoque -= item.quantidade
        db.commit()

    # Criar reserva
    reserva = ReservaProduto(
        cliente_id=cliente_id,
        loja_id=loja_id,
        data_reserva=datetime.utcnow(),
        status="RESERVADO"
    )
    reserva.data_limite = reserva.data_reserva + timedelta(days=2)
    db.add(reserva)
    db.commit()
    db.refresh(reserva)

    # Criar itens de reserva
    for item in itens_carrinho:
        produto = db.query(Produto).filter(Produto.id == item.produto_id).first()
        novo_item = ItemReserva(
            reserva_id=reserva.id,
            produto_id=produto.id,
            quantidade=item.quantidade,
            preco_unitario=produto.preco
        )
        db.add(novo_item)

    db.commit()

    # Limpar carrinho
    for item in itens_carrinho:
        db.delete(item)
    db.commit()

    return jsonify(
        mensagem="Reserva criada com sucesso. Vá à loja para retirar.",
        reserva_id=reserva.id,
        data_limite=reserva.data_limite
    )

@app.route("/cliente/<int:cliente_id>/reserva/<int:reserva_id>/marcar_retirada", methods=["PUT"])
def cliente_marcar_retirada(cliente_id, reserva_id):
    """
    O cliente marca sua reserva de produto como RETIRADA.
    ---
    tags:
      - Reservas
    parameters:
      - name: cliente_id
        in: path
        type: integer
        required: true
      - name: reserva_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Reserva marcada como RETIRADA
      400:
        description: Status inválido ou fora do prazo
      404:
        description: Reserva não encontrada para este cliente
    """
    db: Session = next(get_db())
    reserva = db.query(ReservaProduto).filter(
        ReservaProduto.id == reserva_id,
        ReservaProduto.cliente_id == cliente_id
    ).first()
    if not reserva:
        return jsonify(detail="Reserva não encontrada para este cliente."), 404
    
    if reserva.status != "RESERVADO":
        return jsonify(detail="Não é possível marcar retirada neste status."), 400

    agora = datetime.utcnow()
    limite_4_dias = reserva.data_reserva + timedelta(days=4)
    if agora > limite_4_dias:
        return jsonify(detail="Já se passaram 4 dias, não é mais possível marcar como retirada."), 400

    reserva.status = "RETIRADO"
    db.commit()
    db.refresh(reserva)

    return jsonify(mensagem="Reserva marcada como RETIRADA pelo cliente.")

# -------------------------------------------
#  AGENDAMENTO DE SERVIÇOS
# -------------------------------------------

@app.route("/servico/<int:servico_id>/horarios_disponiveis", methods=["GET"])
def listar_horarios_disponiveis(servico_id):
    """
    Lista os horários disponíveis para um determinado serviço.
    ---
    tags:
      - Serviços
    parameters:
      - name: servico_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Retorna lista de horários disponíveis
    """
    db: Session = next(get_db())
    horarios = db.query(ServicoHorario).filter(
        ServicoHorario.servico_id == servico_id,
        ServicoHorario.is_disponivel == True
    ).all()

    resultado = []
    for h in horarios:
        resultado.append({
            "horario_id": h.id,
            "datahora": h.horario
        })
    return jsonify(horarios_disponiveis=resultado)

@app.route("/cliente/<int:cliente_id>/servicos/<int:servico_id>/agendar", methods=["POST"])
def agendar_servico(cliente_id, servico_id):
    """
    Agenda um serviço para um determinado horário.
    ---
    tags:
      - Serviços
    consumes:
      - application/json
    parameters:
      - name: cliente_id
        in: path
        type: integer
        required: true
      - name: servico_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            horario_id:
              type: integer
    responses:
      200:
        description: Serviço agendado com sucesso
      400:
        description: Horário indisponível ou cliente já tem agendamento neste dia
      404:
        description: Cliente ou serviço não encontrado
    """
    db: Session = next(get_db())
    data = request.get_json()

    horario_id = data.get("horario_id")
    if not horario_id:
        return jsonify(detail="É necessário informar horario_id."), 400

    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        return jsonify(detail="Cliente não encontrado."), 404

    servico = db.query(Servico).filter(Servico.id == servico_id).first()
    if not servico:
        return jsonify(detail="Serviço não encontrado."), 404

    horario_disponivel = db.query(ServicoHorario).filter(
        ServicoHorario.id == int(horario_id),
        ServicoHorario.servico_id == servico_id,
        ServicoHorario.is_disponivel == True
    ).first()

    if not horario_disponivel:
        return jsonify(detail="Horário não está disponível ou não existe para este serviço."), 400

    data_alvo = horario_disponivel.horario.date()
    reservas_mesmo_dia = db.query(ReservaServico).filter(
        ReservaServico.cliente_id == cliente_id,
        ReservaServico.data_horario.between(
            datetime(data_alvo.year, data_alvo.month, data_alvo.day, 0, 0, 0),
            datetime(data_alvo.year, data_alvo.month, data_alvo.day, 23, 59, 59)
        )
    ).all()

    if reservas_mesmo_dia:
        return jsonify(detail="Você já tem um agendamento neste dia."), 400

    nova_reserva = ReservaServico(
        cliente_id=cliente_id,
        loja_id=servico.loja_id,
        servico_id=servico_id,
        data_horario=horario_disponivel.horario,
        status="PENDENTE"
    )
    db.add(nova_reserva)

    horario_disponivel.is_disponivel = False
    db.commit()
    db.refresh(nova_reserva)
    return jsonify(mensagem="Serviço agendado com sucesso.", reserva_id=nova_reserva.id)

@app.route("/cliente/<int:cliente_id>/reserva/<int:reserva_id>/cancelar", methods=["PUT"])
def cancelar_reserva(cliente_id, reserva_id):
    """
    Cancela uma reserva de serviço (feita pelo cliente).
    ---
    tags:
      - Serviços
    parameters:
      - name: cliente_id
        in: path
        type: integer
        required: true
      - name: reserva_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Reserva cancelada com sucesso
      400:
        description: Não é possível cancelar neste status ou falta 1 hora para o serviço
      404:
        description: Reserva não encontrada para este cliente
    """
    db: Session = next(get_db())
    reserva = db.query(ReservaServico).filter(
        ReservaServico.id == reserva_id,
        ReservaServico.cliente_id == cliente_id
    ).first()

    if not reserva:
        return jsonify(detail="Reserva não encontrada para este cliente."), 404

    if reserva.status in ["CANCELADO", "REJEITADA"]:
        return jsonify(detail="A reserva já está cancelada ou rejeitada."), 400

    agora = datetime.now()
    diferenca = reserva.data_horario - agora
    if diferenca.total_seconds() < 3600:
        return jsonify(detail="Não é possível cancelar com menos de 1 hora de antecedência."), 400

    if reserva.status not in ["PENDENTE", "ACEITO"]:
        return jsonify(detail="Não é possível cancelar neste status."), 400

    reserva.status = "CANCELADO"
    db.commit()
    db.refresh(reserva)

    horario_disponivel = db.query(ServicoHorario).filter(
        ServicoHorario.servico_id == reserva.servico_id,
        ServicoHorario.horario == reserva.data_horario
    ).first()
    if horario_disponivel:
        horario_disponivel.is_disponivel = True
        db.commit()

    return jsonify(mensagem="Reserva cancelada com sucesso.")

@app.route("/cliente/<int:cliente_id>/agenda", methods=["GET"])
def ver_agenda_cliente(cliente_id):
    """
    Lista as reservas de serviço do cliente.
    ---
    tags:
      - Serviços
    parameters:
      - name: cliente_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Retorna a lista de reservas do cliente
    """
    db: Session = next(get_db())
    reservas = db.query(ReservaServico).filter(ReservaServico.cliente_id == cliente_id).all()

    retorno = []
    for r in reservas:
        retorno.append({
            "reserva_id": r.id,
            "cliente_id": r.cliente_id,
            "loja_id": r.loja_id,
            "servico_id": r.servico_id,
            "data_horario": r.data_horario,
            "status": r.status
        })
    return jsonify(agenda_cliente=retorno)

# -------------------------------------------
#  ATUALIZAR PERFIL CLIENTE (mantido como multipart se enviar foto)
# -------------------------------------------

@app.route("/cliente/<int:cliente_id>/atualizar_perfil", methods=["PUT"])
def atualizar_perfil_cliente(cliente_id):
    """
    Atualiza informações de perfil de um cliente (nome, idade, foto).
    ---
    tags:
      - Cliente
    consumes:
      - multipart/form-data
    parameters:
      - name: cliente_id
        in: path
        type: integer
        required: true
      - name: nome
        in: formData
        type: string
        required: false
      - name: idade
        in: formData
        type: integer
        required: false
      - name: arquivo
        in: formData
        type: file
        required: false
        description: Foto do cliente
    responses:
      200:
        description: Perfil do cliente atualizado com sucesso
      400:
        description: Arquivo inválido
      404:
        description: Cliente não encontrado
    """
    db: Session = next(get_db())
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        return jsonify(detail="Cliente não encontrado."), 404

    nome = request.form.get("nome")
    idade = request.form.get("idade")
    arquivo = request.files.get("arquivo")

    if nome is not None:
        cliente.nome = nome

    if idade is not None:
        cliente.idade = int(idade)

    if arquivo:
        if not arquivo.content_type.startswith("image/"):
            return jsonify(detail="O arquivo enviado não é uma imagem válida."), 400
        
        ext = arquivo.filename.split(".")[-1]
        nome_arquivo = f"cliente_{cliente_id}_{uuid.uuid4()}.{ext}"
        caminho_arquivo = os.path.join("images", nome_arquivo)

        with open(caminho_arquivo, "wb") as buffer:
            shutil.copyfileobj(arquivo, buffer)

        cliente.foto_path = caminho_arquivo

    db.commit()
    db.refresh(cliente)

    return jsonify(
        mensagem="Perfil do cliente atualizado com sucesso.",
        cliente_id=cliente.id,
        nome=cliente.nome,
        idade=cliente.idade,
        foto_path=cliente.foto_path
    )

if __name__ == "__main__":
    # Executar a aplicação Flask
    # Você pode configurar host='0.0.0.0' se quiser expor em rede
    app.run(debug=True, port=5000)