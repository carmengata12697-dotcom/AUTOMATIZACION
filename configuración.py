import os

class Configuracion:
    """Clase de configuración para la aplicación."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'my_secret_key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    JSON_SORT_KEYS = False

    #API
    API_KEY = os.environ.get('API_KEY', 'my_api_key')
                             
    #RATIO DE TIEMPO LIMITE PARA RESPUESTAS DE LA API
    RATIO_TIEMPO_LIMITE = '100 por hora'

class DevelopmentConfig(Configuracion):
    """Configuración específica para el entorno de desarrollo."""
    
class ProductionConfig(Configuracion):
    """Configuración específica para el entorno de producción."""

class TestingConfig(Configuracion):
    """Configuración específica para el entorno de pruebas."""


#Dicccionario de configuraciones para facilitar la selección del entorno
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}