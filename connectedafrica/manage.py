import os

from flask_script import Manager
from flask_assets import ManageAssets

from connectedafrica.core import assets, grano
from connectedafrica.views import app

manager = Manager(app)
manager.add_command("assets", ManageAssets(assets))


@manager.command
def truncateproject():
    """ Delete the project's entities, relations and schemata (dev only) """
    from connectedafrica.core import client as grano_instance, grano as project
    client = grano_instance.client
    resp = client.session.delete(client.path('/projects/%s/_truncate' % project.slug))
    client.evaluate(resp)

    resp = client.session.get(client.path('/projects/%s/schemata' % project.slug))
    # iterate over schemata in reverse to yield parents last
    for schemata in reversed(client.evaluate(resp)[1]['results']):
        client.session.delete(schemata['api_url'])

if __name__ == "__main__":
    manager.run()
