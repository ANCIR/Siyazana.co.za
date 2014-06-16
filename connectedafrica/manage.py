from flask.ext.script import Manager
from flask.ext.assets import ManageAssets

from connectedafrica.core import assets, app
from connectedafrica.views.base import blueprint as base_blueprint


app.register_blueprint(base_blueprint)

manager = Manager(app)
manager.add_command("assets", ManageAssets(assets))


@manager.command
def load():
    """ Load all the datas. """
    pass


if __name__ == "__main__":
    manager.run()
