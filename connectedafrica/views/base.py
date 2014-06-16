from flask import Blueprint, render_template

#from connectedafrica.core import grano


blueprint = Blueprint('base', __name__)


@blueprint.route('/')
def index():
    return render_template('index.html')

