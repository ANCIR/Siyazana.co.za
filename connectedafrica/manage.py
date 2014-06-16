from flask.ext.script import Manager
from flask.ext.assets import ManageAssets

from connectedafrica.core import assets
from connectedafrica.web import app

manager = Manager(app)
manager.add_command("assets", ManageAssets(assets))


@manager.command
def load():
    """ Load all the datas. """
    pass


@manager.command
def run(port):
    app.run(host='0.0.0.0', port=int(port), debug=app.debug)


if __name__ == "__main__":
    manager.run()
