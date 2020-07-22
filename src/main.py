"""
:Author: PDT
:Since: 2020/05/24
"""

from flask import Flask

from server import index, configuration
from config import Config
from server.asset_server import create_asset
from server.asset_type_server import delete_asset_type, get_one_asset_type, get_all_asset_types, create_asset_type

# Getting config values
# ---------------------
template_folder = Config.get().read('frontend', 'template_folder', '/res/templates')

# Creating Flask Application
# --------------------------
app = Flask(__name__, template_folder=template_folder)

# Adding Routes provided in server to app
# ---------------------------------------
app.add_url_rule('/', 'index', index, methods=['GET'])
app.add_url_rule('/configuration', 'configuration', configuration, methods=['GET'])

app.add_url_rule('/asset-type/create', 'create-asset-type', create_asset_type, methods=['GET', 'POST'])
app.add_url_rule('/asset-types', 'asset-types', get_all_asset_types, methods=['GET'])
app.add_url_rule('/asset-type/<int:asset_type_id>', 'asset-type', get_one_asset_type, methods=['GET', 'POST'])

app.add_url_rule('/asset-type/<int:asset_type_id>/create-asset', 'create-asset', create_asset, methods=['GET', 'POST'])

if __name__ == '__main__':
    app.run(debug=True)
