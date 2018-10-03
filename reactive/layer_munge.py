from charmhelpers.fetch import apt_install
import charms.leadership as leadership
import charms.reactive as reactive
import charms.reactive.flags as flags
import charms.munge.munge as munge
import charmhelpers.core.hookenv as hookenv
import charmhelpers.core.host as host

MUNGE_PACKAGE = 'munge'


flags.register_trigger(when='config.changed.munge_key',
                       clear_flag='munge.configured')
flags.register_trigger(when='leadership.changed.munge_key',
                       clear_flag='munge.configured')
flags.register_trigger(when='leadership.changed.munge_key',
                       clear_flag='munge.exposed')


@reactive.when_not('munge.installed')
def install_slurm():
    hookenv.status_set('maintenance', 'installing munge package')

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
        munge_key = host.pwgen(length=4096)
    leadership.leader_set(munge_key=munge_key)


@reactive.when('endpoint.munge-consumer.munge_key_updated')
@reactive.when('leadership.is_leader')
def consume_munge_key(munge_consumer):
    '''consume a munge key if a relation to a provider has been made
    via a consumer interface regardless of whether it has been generated
    or not. Store it in leader settings to propagate to other units.'''
    munge_key = munge_consumer.munge_key()
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
    # set a flag confirming that munge key is rendered
    flags.set_flag('munge.configured')


@reactive.when_file_changed(munge.MUNGE_KEY_PATH)
def restart_on_munge_change():
    host.service_restart(munge.MUNGE_SERVICE)


@reactive.when('endpoint.munge-provider.joined')
@reactive.when('leadership.is_leader')
@reactive.when('leadership.set.munge_key')
@reactive.when('munge.configured')
@reactive.when_not('munge.exposed')
def provide_munge_key(munge_provider):
    '''Provide munge key if any consumers are related and if '''
    munge_key = leadership.leader_get('munge_key')
    munge_provider.expose_munge_key(munge_key)
    flags.set_flag('munge.exposed')
