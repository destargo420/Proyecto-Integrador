class Config:
    SECRET_KEY = 'B!1qDWDSDAWad$%*SS¿a'



class DevelopmentConfig(Config):
    DEBUG = True
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'bd_proyecto'

config = { 
    'development': DevelopmentConfig
}