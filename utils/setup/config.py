"""
Setup configuration classes
"""
from pathlib import Path

class SetupConfig:
    """Configuration class for setup process"""
    def __init__(self, use_mariadb=False, skip_vault=False, skip_plugins=False, env='dev'):
        self.use_mariadb = use_mariadb
        self.skip_vault = skip_vault
        self.skip_plugins = skip_plugins
        self.env = env
        self.base_dir = Path(__file__).resolve().parent.parent.parent

class DatabaseSetup:
    """Handle database initialization"""
    @staticmethod
    def init_sqlite(base_dir):
        """Initialize SQLite database"""
        instance_dir = base_dir / 'instance'
        if not instance_dir.exists():
            instance_dir.mkdir()
        print("\nInitialized SQLite database")
        return True

    @staticmethod
    def init_mariadb():
        """Initialize MariaDB database"""
        try:
            import pymysql
            return True
        except ImportError:
            print("\nError: pymysql not installed. Required for MariaDB support.")
            print("Install with: pip install pymysql")
            return False

class EnvironmentSetup:
    """Handle environment configuration"""
    @staticmethod
    def create_env_file(config: SetupConfig):
        """Create .env file with default settings if it doesn't exist"""
        env_path = config.base_dir / '.env'
        if not env_path.exists():
            with env_path.open('w') as f:
                f.write(f"FLASK_ENV={config.env}\n")
                f.write("FLASK_APP=app.py\n")
                f.write("SECRET_KEY=dev\n")
                if config.use_mariadb:
                    f.write("DB_TYPE=mariadb\n")
                    f.write("MARIADB_USER=root\n")
                    f.write("MARIADB_PASSWORD=\n")
                    f.write("MARIADB_HOST=localhost\n")
                    f.write("MARIADB_PORT=3306\n")
                    f.write("MARIADB_DATABASE=app\n")
                else:
                    f.write("DB_TYPE=sqlite\n")
            print("\nCreated .env file with default settings")
