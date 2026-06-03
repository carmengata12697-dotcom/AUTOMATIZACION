from flask import Flask, jsonify, request
from flask_cors import CORS
from datatools import datatime
import os
from dotenv import load_dotenv
from yfinance import Ticker
import pandas as pd
import numpy as np

#Cargar variables de entorno
load_dotenv()

#directorio

base_dir = os.path.dirname(os.path.abspath(__file__))

#inicializar la aplicación Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_my_secret_key')

#configurar la db
db_path = os.path.join(base_dir, 'instance', 'financel.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#habilitar CORS
CORS(app)
"""
#autenticación y autorización
@app.before_request
def authenticate():
    #verificar la clave de API en los encabezados de la solicitud
    api_key = request.headers.get('X-API-KEY')

#chekeo de las rutas
@app.route('/health')
# endpoint de prueba para verificar que la API está funcionando

#crear tablas de la conexión a la base de datos
with app.app_context():
    db.create_all()

#iniciar el servidor
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)"""