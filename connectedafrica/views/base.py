from flask import Blueprint, render_template

from connectedafrica.core import app


@app.context_processor
def inject_globals():
    return {
        'APP_NAME': app.config.get('APP_NAME')
    }


# TODO: maybe factor out into a differently-named controller?

blueprint = Blueprint('base', __name__)


@blueprint.route('/')
def index():
    return render_template('index.html')

