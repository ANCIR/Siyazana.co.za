import os
import pwd
from fabric.api import cd, env, task, require, sudo, prefix, shell_env, run
from fabric.contrib.files import exists, upload_template
from fabric.context_managers import shell_env


VIRTUALENV_DIR = 'connectedafrica_ve'
CODE_DIR = 'connectedafrica'
PROD_HOSTS = ['ec2-54-76-245-198.eu-west-1.compute.amazonaws.com']
PACKAGES = (
    'git-core',
    'memcached',
    'nginx',
    'npm',
    'python-dev',
    'python-virtualenv',
    'supervisor',
)
# Nginx & Supervisor constants
SERVER_NAMES = 'sa.connectedafrica.org ec2-54-76-245-198.eu-west-1.compute.amazonaws.com'
PROXY_PORT = 5001
PROXY_HOST = '127.0.0.1'
LOG_DIR = 'connectedafrica_logs'


@task
def prod():
    env.deploy_user = 'connectedafrica'
    env.deploy_dir = '/home/connectedafrica/'
    env.branch = 'master'
    env.nginx_bind = '127.0.0.1:80'
    env.hosts = PROD_HOSTS


@task
def provision():
    require('deploy_user', 'deploy_dir', provided_by=[prod])

    commands = (
        'apt-get install %s --no-upgrade' % ' '.join(PACKAGES),
        'apt-get build-dep lxml --no-upgrade',
        'mkdir -p %s' % env.deploy_dir,
        'chown -R %s:%s %s' % (env.deploy_user, env.deploy_user, env.deploy_dir),
    )
    sudo('; '.join(commands))


@task
def deploy():
    require('deploy_user', 'deploy_dir', 'branch',
            provided_by=[prod])

    repo_dir = os.path.join(env.deploy_dir, CODE_DIR)
    ve_dir = os.path.join(env.deploy_dir, VIRTUALENV_DIR)

    if not exists(ve_dir):
        sudo('virtualenv -p python2.7 %s' % ve_dir, user=env.deploy_user)

    if not exists(repo_dir):
        with cd(env.deploy_dir):
            sudo('git clone -b %s https://github.com/codeforafrica/connectedAFRICA.git %s'
                 % (env.branch, repo_dir), user=env.deploy_user)
    else:
        with cd(repo_dir):
            sudo('git checkout -B %s' % env.branch, user=env.deploy_user)
            sudo('git pull origin %s' % env.branch, user=env.deploy_user)

    with cd(repo_dir), prefix('. ../%s/bin/activate' % VIRTUALENV_DIR):
        sudo('pip install -e ./', user=env.deploy_user)
        sudo('make install', user=env.deploy_user)

    # render and upload templates
    upload_template(os.path.join(os.path.dirname(__file__), 'deploy/nginx.template'),
                    '/etc/nginx/sites-enabled/connectedafrica.conf',
                    get_nginx_template_context(), use_sudo=True, backup=False)
    upload_template(os.path.join(os.path.dirname(__file__), 'deploy/supervisor.template'),
                    '/etc/supervisor/conf.d/connectedafrica.conf',
                    get_supervisor_template_context(), use_sudo=True, backup=False)
    # make sure logging dir exists and update processes
    log_dir = os.path.join(env.deploy_dir, LOG_DIR)
    sudo('mkdir -p %s' % log_dir, user=env.deploy_user)
    sudo('supervisorctl update')
    sudo('/etc/init.d/nginx reload')


@task
def make(rule):
    require('deploy_dir', provided_by=[prod])

    repo_dir = os.path.join(env.deploy_dir, CODE_DIR)

    with cd(repo_dir), prefix('. ../%s/bin/activate' % VIRTUALENV_DIR):
        with shell_env(GRANO_HOST='http://backend.connectedafrica.org',
                       GRANO_PROJECT='southafrica',
                       COAF_SETTINGS='settings'):
            run('make %s' % rule)


def get_nginx_template_context():
    return {
        'server-name': SERVER_NAMES,
        'server-port': env.nginx_bind,
        'static-path': os.path.join(env.deploy_dir, 'connectedafrica/connectedafrica/static/'),
        'log': os.path.join(env.deploy_dir, LOG_DIR, 'nginx.log'),
        'err-log': os.path.join(env.deploy_dir, LOG_DIR, 'nginx.err'),
        'proxy-host': PROXY_HOST,
        'proxy-port': PROXY_PORT,
    }


def get_supervisor_template_context():
    return {
        'user': env.deploy_user,
        'project-dir': os.path.join(env.deploy_dir, CODE_DIR),
        've-dir': os.path.join(env.deploy_dir, VIRTUALENV_DIR),
        'log': os.path.join(env.deploy_dir, LOG_DIR, 'gunicorn.log'),
        'err-log': os.path.join(env.deploy_dir, LOG_DIR, 'gunicorn.err'),
        'host': PROXY_HOST,
        'port': PROXY_PORT,
        'process-name': '%(program_name)s_%(process_num)s'
    }
