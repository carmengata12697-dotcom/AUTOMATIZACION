class clientes(db.Model):
    __tablename__ = 'clientes'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    pais = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    activo = db.Column(db.Boolean, default=True)

    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_ultima_compra = db.Column(db.DateTime, nullable=True)

    #relacion con transacciones
    transactions = db.relationship('transactions', backref='cliente', lazy=True)
    portfolios = db.relationship('portfolios', backref='cliente', lazy=True)

    def to_dict(self):
        """Convierte el objeto cliente a un diccionario para facilitar su serialización a JSON."""
        return {
            'id': self.id,
            'email': self.email,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'pais': self.pais,
            'telefono': self.telefono,
            'activo': self.activo,
            'fecha_registro': self.fecha_registro.isoformat(),
            'fecha_ultima_compra': self.fecha_ultima_compra.isoformat(),
            'transactions': [transaction.to_dict() for transaction in self.transactions],
            'portfolios': [portfolio.to_dict() for portfolio in self.portfolios],
            'total_acciones': len(self.transactions) if self.transactions else 0,
        }

    def __repr__(self):
        return f'<Cliente {self.email} >'

#clase para las transacciones
class transactions(db.Model):
    id, cliente_id, monto, moneda, tipo, estado, descripcion,
    #relacion con cliente
    #estado posibles: pendiente, completada, cancelada
    #tipo posibles: compra, venta, deposito, retiro

#portafolio


#auditoria
