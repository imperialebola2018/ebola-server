import json
import os
import time

import docker
import hvac

import compose


components = {
    "containers": {
        "reporting_api": "reporting_api",
        "db": "db",
        "proxy": "proxy",
        "orderly": "orderly"
    },
    "volumes": {
        "db": "db_volume",
        "orderly": "orderly_volume",
        "templates": "template_volume",
        "guidance": "guidance_volume"
    },
    "network": "default"
}


class Service:
    def __init__(self, settings):
        self.docker_prefix = "ebolaserver"

        self._validate_settings(settings)
        self.settings = settings
        # This one is not configurable but will be used
        self.settings['docker_prefix'] = self.docker_prefix

        self.client = docker.from_env()
        self.containers = components['containers'].copy()
        self.volumes = components['volumes'].copy()
        self.network = components['network']
        self._vault = None

    @staticmethod
    def from_configuration(path):
        with open(path) as f:
            settings = json.load(f)
        return Service(settings)

    def _validate_settings(self, settings):
        expected = ["proxy_port"]
        msg = set(settings.keys()) - set(expected)
        if msg:
            raise Exception("Missing keys: {}".format(", ".join(msg)))
        extra = set(expected) - set(settings.keys())
        if extra:
            raise Exception("Unknown keys: {}".format(", ".join(extra)))

    @property
    def vault(self):
        if not self._vault:
            self._vault = get_vault()
        return self._vault

    @property
    def container_names(self):
        return set([self.container_name(x) for x in self.containers.keys()])

    @property
    def status(self):
        expected = self.container_names
        actual = dict((c.name, c)
                      for c in self.client.containers.list(all=True))
        unexpected = list(x for x in actual.keys() - expected
                          if x.startswith(self.docker_prefix + "_"))
        if any(unexpected):
            raise Exception("Unexpected containers running: {}".format(
                unexpected))

        services = list(c for c in actual.values() if c.name in expected)
        statuses = set(c.status for c in services)

        if len(statuses) == 1:
            return statuses.pop()
        elif len(statuses) == 0:
            return None
        else:
            status_map = dict((c.name, c.status) for c in services)
            raise Exception(
                "service is in a indeterminate state. "
                "Manual intervention is required.\nStatus: {}".format(
                    status_map))

    def container_name(self, name):
        return "{}_{}_1".format(self.docker_prefix, self.containers[name])

    def volume_name(self, name):
        return "{}_{}".format(self.docker_prefix, self.volumes[name])

    @property
    def reporting_api(self):
        return self._get_container("reporting_api")

    @property
    def db(self):
        return self._get_container("db")

    @property
    def proxy(self):
        return self._get_container("proxy")

    @property
    def orderly(self):
        return self._get_container("orderly")

    @property
    def proxy(self):
        return self._get_container("proxy")

    @property
    def db_volume_present(self):
        try:
            self.client.volumes.get(self.volume_name("db"))
            return True
        except docker.errors.NotFound:
            return False

    @property
    def network_name(self):
        return "{}_{}".format(self.docker_prefix, self.network)

    def _get_container(self, name):
        try:
            return self.client.containers.get(self.container_name(name))
        except docker.errors.NotFound:
            return None

    def stop(self):
        # As documented in VIMC-805, the orderly container will
        # respond quickly to an interrupt, but not to whatever docker
        # stop (via docker-compose stop) is sending. This is
        # (presumably) a limitation of httpuv and not something I can
        # see how to work around at the R level. So instead we send an
        # interrupt signal (SIGINT) just before the stop, and that
        # seems to bring things down much more quicky.
        print("Stopping...({})".format(
            self.settings["docker_prefix"]),
            flush=True)
        if self.orderly:
            try:
                self.orderly.kill("SIGINT")
            except:
                print("Killing orderly container failed - continuing")
                pass
        compose.stop(self.settings)

    def pull(self):
        print("Pulling images", flush=True)
        compose.pull(self.settings)

    def start(self):
        print("Starting...", flush=True)
        compose.start(self.settings)
        print("- Checking we have started successfully")
        time.sleep(2)
        if self.status != "running":
            raise Exception("Failed to start. Service status is {}".format(
                self.status))


def get_vault(refresh=False):
    print("Connecting to the vault")
    # First try and login using a vault token.  That might fail
    # because the token is not present *or* because it has expired.
    # So we'll just pass and continue with more involved methods if
    # anything fails.
    vault_addr = "https://ebola2018.dide.ic.ac.uk:8200"
    if not refresh:
        try:
            token = os.environ['VAULT_TOKEN']
            print("...using local token")
            vault = hvac.Client(url=vault_addr, token=token)
            if vault.is_authenticated():
                return vault
        except:
            pass
    try:
        token = os.environ['VAULT_AUTH_GITHUB_TOKEN']
    except KeyError:
        token = input("Enter your github token: ").strip()
    print("...using github token")
    vault = hvac.Client(url=vault_addr)
    vault.auth_github(token)
    return vault


__all__ = ["Service"]
