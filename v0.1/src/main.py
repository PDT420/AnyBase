"""
:Author: PDT
:Since: 2020/05/24

This is the main application of AnyBase. Run this.
"""
# import redis
from quart import Quart

from asset.asset_server import AssetServer
from asset_type.asset_type_server import AssetTypeServer
from config import Config
from database.db_connection import DbConnection
from database.sqlite_connection import SqliteConnection

# Getting config values
# ---------------------
from misc.common_server import CommonServer
from plugins.notes_plugin import NotesPluginServer

Config.get().change_path('U:/projects/anybase_modular_management/res/config.ini')
template_folder = Config.get().read('frontend', 'template_folder', '/res/templates')
static_folder = Config.get().read('frontend', 'static_folder', 'res/static')

# Creating Quart Application
# --------------------------
app = Quart(
    import_name=__name__,
    template_folder=template_folder,
    static_url_path='/static',
    static_folder=static_folder
)

# app.secret_key = "SomeSecret"

# Initializing redis connection
# -----------------------------
# strict_redis = redis.StrictRedis(host='localhost', port=6379)
# strict_redis.execute_command('FLUSHDB')

# Initialization
# --------------

# Database
# ~~~~~~~~
db_path = Config.get().read('local database', 'path')
db_connection: DbConnection = SqliteConnection.get(db_path)

# Adding Routes provided by the server to app
# -------------------------------------------

# Server Routes
# ~~~~~~~~~~~~~
CommonServer.get().register_routes(app=app)
AssetServer.get().register_routes(app=app)
AssetTypeServer.get().register_routes(app=app)

# Plugin Routes
# ~~~~~~~~~~~~~
NotesPluginServer.get().register_routes(app=app)

if __name__ == '__main__':
    app.run('localhost', port=5000, debug=True)