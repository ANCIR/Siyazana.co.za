from flask import Blueprint, render_template

from connectedafrica.core import app, pages


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

@blueprint.route('/pages/<path:path>/')
def page(path):
    page = pages.get_or_404(path)
    template = page.meta.get('template', 'pages.html')
    return render_template(template, page=page)
