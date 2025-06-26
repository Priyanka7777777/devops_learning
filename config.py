import os
from dotenv import load_dotenv

# Load env-specific .env file
env = os.getenv('FLASK_ENV', 'development')

if env == 'development':
    load_dotenv('.env.development')
elif env == 'testing':
    load_dotenv('.env.testing')
elif env == 'production':
    load_dotenv('.env.production')
else:
    load_dotenv()

class Config:
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret')
    DATABASE = os.getenv('DATABASE', 'fallback.db')

class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE = os.getenv('DATABASE', 'dev_database.db')

class TestingConfig(Config):
    TESTING = True
    DATABASE = os.getenv('DATABASE', 'test_database.db')

class ProductionConfig(Config):
    DEBUG = False
    DATABASE = os.getenv('DATABASE', 'prod_database.db')
