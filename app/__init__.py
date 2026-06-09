# subdir that includes __init__.py file is considered a package and can be imported

from flask import Flask # top import
from config import Config # need to import config variables from class stored in config.py file
from flask_sqlalchemy import SQLAlchemy 
from flask_migrate import Migrate


# lowercase "config" is the name of the Python module config.py, and the one with the uppercase "C" is the actual class.


app = Flask(__name__) # variable app as instance of class Flask
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# When you call app.config.from_object(Config):
# 1. Flask inspects the Config class for all UPPERCASE attributes (lowercase will be ignored)
# 2. Copies each one into app.config as key-value pairs
# 3. Ignores lowercase attributes, methods, private variables


from app import routes, models # app package is DIFFERENT than app var above

# bottom import wellknown workaround avoids circular imports
# avoids error that results from mutual references between 2 files?




