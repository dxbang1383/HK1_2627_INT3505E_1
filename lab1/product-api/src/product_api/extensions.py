from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Module-level proxy extensions
# Tách khỏi app giúp tái sử dụng, test độc lập và tránh circular import
db = SQLAlchemy()
migrate = Migrate()
