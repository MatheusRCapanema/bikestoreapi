from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    idade = Column(Integer, nullable=False)
    cpf = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)

    foto_path = Column(String, nullable=True)

    cart_items = relationship("Carrinho", back_populates="cliente")
    reservas = relationship("ReservaServico", back_populates="cliente")


class Loja(Base):
    __tablename__ = "lojas"

    id = Column(Integer, primary_key=True, index=True)
    nome_loja = Column(String, nullable=False)
    cnpj = Column(String, unique=True, index=True, nullable=False)
    cep = Column(String, nullable=False)
    endereco = Column(String, nullable=False)
    complemento = Column(String, nullable=True)
    lote = Column(String, nullable=True)
    senha_hash = Column(String, nullable=False)

    descricao = Column(String, nullable=True)
    foto_path = Column(String, nullable=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    produtos = relationship("Produto", back_populates="loja")
    servicos = relationship("Servico", back_populates="loja")
    reservas = relationship("ReservaServico", back_populates="loja")


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome_produto = Column(String, nullable=False)
    preco = Column(Float, nullable=False)
    loja_id = Column(Integer, ForeignKey("lojas.id"))
    
    image_path = Column(String, nullable=True)
    quantidade_estoque = Column(Integer, default=0)

    loja = relationship("Loja", back_populates="produtos")


class ReservaProduto(Base):
    __tablename__ = "reservas_produtos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    loja_id = Column(Integer, ForeignKey("lojas.id"), nullable=False)
    
    data_reserva = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="RESERVADO")
    
    data_limite = Column(DateTime, nullable=True)
    
    cliente = relationship("Cliente")
    loja = relationship("Loja")
    itens = relationship("ItemReserva", back_populates="reserva", cascade="all, delete-orphan")


class ItemReserva(Base):
    __tablename__ = "itens_reserva"

    id = Column(Integer, primary_key=True, index=True)
    reserva_id = Column(Integer, ForeignKey("reservas_produtos.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, default=1)
    preco_unitario = Column(Float, default=0.0)

    reserva = relationship("ReservaProduto", back_populates="itens")
    produto = relationship("Produto")


class Servico(Base):
    __tablename__ = "servicos"

    id = Column(Integer, primary_key=True, index=True)
    nome_servico = Column(String, nullable=False)
    descricao = Column(String, nullable=True)
    preco = Column(Float, nullable=False)
    loja_id = Column(Integer, ForeignKey("lojas.id"))

    loja = relationship("Loja", back_populates="servicos")

    horarios = relationship(
        "ServicoHorario",
        back_populates="servico",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class ServicoHorario(Base):
    __tablename__ = "servicos_horarios"

    id = Column(Integer, primary_key=True, index=True)
    servico_id = Column(
        Integer,
        ForeignKey("servicos.id", ondelete="CASCADE"),
        nullable=False
    )
    horario = Column(DateTime, nullable=False)
    is_disponivel = Column(Boolean, default=True)

    servico = relationship("Servico", back_populates="horarios")

class ReservaServico(Base):
    __tablename__ = "reservas_servicos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    loja_id = Column(Integer, ForeignKey("lojas.id"))
    servico_id = Column(Integer, ForeignKey("servicos.id"))
    data_horario = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="PENDENTE")

    cliente = relationship("Cliente", back_populates="reservas")
    loja = relationship("Loja", back_populates="reservas")
    servico = relationship("Servico")


class Carrinho(Base):
    __tablename__ = "carrinho"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    quantidade = Column(Integer, default=1)

    cliente = relationship("Cliente", back_populates="cart_items")
    produto = relationship("Produto")
