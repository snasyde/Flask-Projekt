from flask import Blueprint, render_template
from utils import login_required

blueprint = Blueprint('play', __name__, url_prefix='/play')

@blueprint.route('/')
@login_required
def index():
    return render_template('game.html')