from flask import Blueprint, render_template, request, url_for

from connectedafrica.core import grano, app


blueprint = Blueprint('base', __name__)


@blueprint.route('/')
def index():
    return render_template('index.html')

