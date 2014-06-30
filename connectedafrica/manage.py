from flask.ext.script import Manager
from flask.ext.assets import ManageAssets

from connectedafrica.core import assets, app
from connectedafrica.views.base import blueprint as base_blueprint
from connectedafrica.loaders import schemata


app.register_blueprint(base_blueprint)

manager = Manager(app)
manager.add_command("assets", ManageAssets(assets))


@manager.command
def loadschemata():
    """ Load the pre-defined schemata for this project. """
    schemata.load()


@manager.command
def load():
    """ Load all the datas. """
    pass


@manager.command
def truncateproject():
    """ Delete the project's entities, relations and schemata (dev only) """
    from connectedafrica.core import client as grano_instance, grano as project
    client = grano_instance.client
    resp = client.session.delete(client.path('/projects/%s/_truncate' % project.slug))
    client.evaluate(resp)


if __name__ == "__main__":
    manager.run()
