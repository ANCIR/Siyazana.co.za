from flask import Blueprint, render_template, request, url_for

from connectedafrica.core import grano, app


base = Blueprint('base', __name__)


@base.route('/')
@base.route('/index.html')
def index():
    return render_template('index.html')

