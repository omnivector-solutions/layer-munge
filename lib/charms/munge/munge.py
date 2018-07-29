from charmhelpers.core.templating import render
# import charms.leadership as leadership
# import charmhelpers.core.hookenv as hookenv


MUNGE_SERVICE = 'munge'
MUNGE_KEY_TEMPLATE = 'munge.key'
MUNGE_KEY_PATH = '/etc/munge/munge.key'


def render_munge_key(context):
    render(source=MUNGE_KEY_TEMPLATE,
           target=MUNGE_KEY_PATH,
           context=context,
           owner='munge',
           group='munge',
           perms=0o400)
