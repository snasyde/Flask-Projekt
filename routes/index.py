from flask import Blueprint, render_template

blueprint = Blueprint('index', __name__, template_folder='../templates/index')

# Route zur Startseite
@blueprint.route('/')
def index():
    return render_template('index.html')