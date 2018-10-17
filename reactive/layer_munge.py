from charmhelpers.fetch import apt_install
import charms.leadership as leadership
import charms.reactive as reactive
import charms.reactive.flags as flags
import charms.munge.munge as munge
import charmhelpers.core.hookenv as hookenv
import charmhelpers.core.host as host

MUNGE_PACKAGE = 'munge'


# This trigger does not work. Only config.changed works.
# Moved to config_changed() below
#flags.register_trigger(when='config.changed.munge_key',
#                       clear_flag='munge.configured')
flags.register_trigger(when='leadership.changed.munge_key',
                       clear_flag='munge.configured')
flags.register_trigger(when='leadership.changed.munge_key',
                       clear_flag='munge.exposed')


@reactive.when_not('munge.installed')
def install_munge():
    hookenv.status_set('maintenance', 'installing munge package')
    hookenv.log('install_munge(): installing munge package')

    packages = [MUNGE_PACKAGE]
    apt_install(packages)

    flags.set_flag('munge.installed')


@reactive.when('leadership.is_leader')
@reactive.when_not('leadership.set.munge_key')
def obtain_munge_key(*args):
    # get flags
    munge_key = hookenv.config().get('munge_key')
    # Generate a munge key if it has not been provided via charm config
    if not munge_key:
        hookenv.log('obtain_munge_key(): No key in charm config, generating new key')
        munge_key = host.pwgen(length=4096)
    else:
        hookenv.log('obtain_munge_key(): Using key from charm config')
    leadership.leader_set(munge_key=munge_key)

@reactive.when('leadership.is_leader')
@reactive.when('config.changed')
def config_changed():
    hookenv.log('config_changed(): leader detected charm config change')
    charmconf = hookenv.config()
    # We are only interested if the munge_key has changed
    if charmconf.changed('munge_key'):
        hookenv.log('config:changed(): munge key has changed')
        prev_key = charmconf.previous('munge_key')
        munge_key = charmconf['munge_key']
        hookenv.log('config:changed(): previous key: %s' % prev_key)
        hookenv.log('config:changed(): new key: %s' % munge_key)
        leadership.leader_set(munge_key=munge_key)
        # clear munge.configured and munge.exposed
        flags.clear_flag('munge.configured')
        flags.clear_flag('munge.exposed')
        flags.set_flag('munge.changed_key_file')


@reactive.when('endpoint.munge-consumer.munge_key_updated')
@reactive.when('leadership.is_leader')
def consume_munge_key(munge_consumer):
    '''consume a munge key if a relation to a provider has been made
    via a consumer interface regardless of whether it has been generated
    or not. Store it in leader settings to propagate to other units.'''
    munge_key = munge_consumer.munge_key
    # do not do anything unless there is actually a key available
    # otherwise, keep using whatever was there before
    if munge_key:
        leadership.leader_set(munge_key=munge_key)
    flags.clear_flag('endpoint.munge-consumer.munge_key_updated')


@reactive.when('munge.installed')
@reactive.when('leadership.set.munge_key')
@reactive.when('leadership.changed.munge_key')
def configure_munge_key():
    munge_key = leadership.leader_get('munge_key')
    munge.render_munge_key(context={'munge_key': munge_key})
    hookenv.log('configure_munge_key(): leadership detected new munge key, rendered new file')
    # set a flag confirming that munge key is rendered
    flags.set_flag('munge.configured')


@reactive.when('munge.installed')
@reactive.when('munge.configured')
@reactive.when('munge.changed_key_file')
def restart_on_munge_change2():
    hookenv.log('restart_on_munge_change2(): file %s modified, restarting due to flag' % munge.MUNGE_KEY_PATH)
    host.service_restart(munge.MUNGE_SERVICE)
    flags.clear_flag('munge.changed_key_file')

# This only seems to work when we change through leadership, not charm config change.
# Also, deprecated? https://github.com/juju-solutions/charms.reactive/issues/44
#@reactive.when_file_changed(munge.MUNGE_KEY_PATH)
#def restart_on_munge_change():
#    ''' The when_file_changed gets triggered on leader-set munge_key=xxx but not
#    when key on disk is written due to a charm config change. Needs an extra flag. '''
#    hookenv.log('restart_on_munge_change(): file %s was modified, restarting munge' % munge.MUNGE_KEY_PATH)
#    host.service_restart(munge.MUNGE_SERVICE)


@reactive.when('endpoint.munge-provider.joined')
@reactive.when('leadership.is_leader')
@reactive.when('leadership.set.munge_key')
@reactive.when('munge.configured')
@reactive.when_not('munge.exposed')
def provide_munge_key_to_interface(munge_provider):
    '''Provide munge key if any consumers are related and if '''
    munge_key = leadership.leader_get('munge_key')
    hookenv.log('provide_munge_key_to_interface(): exposing munge key: %s' % munge_key)
    munge_provider.expose_munge_key(munge_key)
    munge_provider.provide_munge_key()
    flags.set_flag('munge.exposed')
