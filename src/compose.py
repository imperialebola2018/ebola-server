from subprocess import Popen


def start(settings):
    run("up -d", settings)


def stop(settings):
    run("down", settings)


def pull(settings):
    run("pull", settings)


def run(args, settings):
    docker_prefix = settings["docker_prefix"]
    prefix = 'docker-compose --project-name {} '.format(docker_prefix)
    cmd = prefix + args
    env = get_env(settings)
    p = Popen(cmd, env=env, shell=True)
    p.wait()
    if p.returncode != 0:
        raise Exception("An error occurred: docker-compose returned {}".format(
            p.returncode))


def get_env(settings):
    env = {
        'PROXY_PORT': str(settings["proxy_port"])
    }
    return env
