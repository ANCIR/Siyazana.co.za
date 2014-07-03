import os

from flask.ext.script import Manager
from flask.ext.assets import ManageAssets

from connectedafrica.core import assets, grano
from connectedafrica.views import app

manager = Manager(app)
manager.add_command("assets", ManageAssets(assets))


@manager.command
def loadschemata():
    """ Load the pre-defined schemata for this project. """
    fn = os.path.join(os.path.dirname(__file__), 'schema.yaml')
    grano.schemata.upsert_from_file(fn)


@manager.command
def truncateproject():
    """ Delete the project's entities, relations and schemata (dev only) """
    from connectedafrica.core import client as grano_instance, grano as project
    client = grano_instance.client
    resp = client.session.delete(client.path('/projects/%s/_truncate' % project.slug))
    client.evaluate(resp)


if __name__ == "__main__":
    manager.run()
