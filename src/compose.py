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
    p = Popen(cmd, shell=True)
    p.wait()
    if p.returncode != 0:
        raise Exception("An error occurred: docker-compose returned {}".format(
            p.returncode))
