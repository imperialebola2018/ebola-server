import time

import psycopg2

import service


def get_service(path_config):
    return service.Service.from_configuration(path_config)


def start(path_config):
    s = get_service(path_config)
    s.pull()
    s.start()
    configure(s)


def stop(path_config):
    s = get_service(path_config)
    s.stop()


def configure(service):
    configure_database(service)
    configure_orderly(service)
    configure_reporting_api(service)
    configure_proxy(service)


def docker_exec_run(container, command, environment=None, check=True,
                    verbose=False):
    res = container.exec_run(command, environment=environment)
    if check and res[0] != 0:
        raise Exception("command failed with output: " +
                        res[1].decode("UTF-8"))
    if verbose:
        print(res[1].decode("UTF-8"))
    return res


def add_property(container, config_path, key, value):
    path = "{}/config.properties".format(config_path)
    docker_exec_run(container, "touch {}".format(path))
    docker_exec_run(container, 'echo "{key}={value}" >> {path}'.format(
        key=key, value=value, path=path))


def configure_reporting_api(service):
    print("Configuring reporting API")
    config_path = "/etc/montagu/reports_api/"
    container = service.reporting_api
    docker_exec_run(container, "mkdir -p " + config_path)

    print("- Setting Orderly volume location")
    add_property(container, config_path, "orderly.root", "/orderly/")

    # NOTE: in montagu the public key is added here

    print("- Sending go signal to reporting API")
    docker_exec_run(container, "touch {}/go_signal".format(config_path))


def configure_orderly(service):
    print("Configuring orderly")
    token = service.vault.token
    cmd = ["/orderly/scripts/configure", "/orderly", token, "/orderly_go"]
    docker_exec_run(service.orderly, cmd, verbose=True)


def configure_database(service):
    print("Configuring database")
    db_set_passwords(service.db, service.vault)


def configure_proxy(service):
    print("Configuring proxy")

    env = {
        "HT_USER": "orderly",
        "HT_PASS": vault_read(service.vault, "secret/proxy/login", "value"),
        "SSL_CERTIFICATE":
        vault_read(service.vault, "secret/proxy/ssl_certificate", "value"),
        "SSL_PRIVATE_KEY":
        vault_read(service.vault, "secret/proxy/ssl_private_key", "value")
    }
    docker_exec_run(service.proxy, "configure_proxy", environment=env,
                    verbose=True)
    configure_proxy_users(service)


# TODO: far better would be to store the encrypted copy
def configure_proxy_users(service):
    vault = service.vault
    users = vault.list("secret/proxy/users")['data']['keys']
    print("Updating passwords for the proxy")
    for u in users:
        print("  - {}".format(u))
        p = vault_read(vault, "secret/proxy/users/{}".format(u), "password")
        docker_exec_run(service.proxy, ["add_user", u, p])


def db_connect(user, password):
    conn_settings = {
        "host": "localhost",
        "port": 5432,
        "name": "postgres",
        "user": user,
        "password": password
    }
    conn_string_template = "host='{host}' port='{port}' dbname='{name}' " + \
                           "user='{user}' password='{password}'"
    conn_string = conn_string_template.format(**conn_settings)
    return psycopg2.connect(conn_string)


def db_set_password(db, user, password):
    db.execute("ALTER USER {user} WITH PASSWORD '{password}'".format(
        user=user, password=password))


def db_set_passwords(container, vault):
    print("Setting database passwords")
    users = vault.list("secret/database/users")["data"]["keys"]
    pw = {u: vault_read(vault, "secret/database/users/{}".format(u), "value")
          for u in users}
    root_user = "postgres"
    print("  - {}".format(root_user))
    res = docker_exec_run(container, ["db-set-root-password", pw[root_user]])

    # This seems to take a few seconds to let us in
    for i in range(10):
        ok = False
        try:
            with db_connect(root_user, pw[root_user]) as conn:
                ok = True
        except psycopg2.OperationalError:
            print("...waiting")
            time.sleep(1)
    if not ok:
        raise Exception("did not get database up properly")

    with db_connect(root_user, pw[root_user]) as conn:
        with conn.cursor() as cur:
            for u, p in pw.items():
                if u != root_user:
                    print("  - {}".format(u))
                    db_set_password(cur, u, p)
        conn.commit()


def vault_read(vault, key, field):
    return vault.read(key)["data"][field]
