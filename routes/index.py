from flask import Blueprint, render_template

blueprint = Blueprint('index', __name__)

# Route zur Startseite
@blueprint.route('/')
def index():
    return render_template('index.html')