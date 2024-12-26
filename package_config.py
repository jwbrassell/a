class PackageConfig:
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    SKIP_VAULT_MIDDLEWARE = True
    SKIP_VAULT_INIT = True
    SKIP_BLUEPRINTS = True  # Skip all blueprints during packaging
    SECRET_KEY = "packaging-key"
    
    @staticmethod
    def init_app(app):
        pass

