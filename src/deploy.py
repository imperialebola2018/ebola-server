import time

import psycopg2

import service


def deploy():
    s = service.Service({})
    s.start()
    configure(s)


def stop():
    s = service.Service({})
    s.stop()


def configure(service):
    configure_database(service)
    configure_orderly(service)
    configure_reporting_api(service)


def docker_exec_run(container, command, check=True):
    res = container.exec_run(command)
    if check and res[0] != 0:
        raise Exception("command failed with output: " + res[1])
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

    # print("- Injecting public key for token verification into container")
    # docker_exec_run(container, "mkdir -p " + join(config_path, "token_key"))
    # docker_cp(keypair_paths['public'], container.name, join(config_path, "token_key/public_key.der"))

    print("- Sending go signal to reporting API")
    docker_exec_run(container, "touch {}/go_signal".format(config_path))


def configure_orderly(service):
    print("Configuring orderly")
    docker_exec_run(service.orderly, "touch /orderly_go")


def configure_database(service):
    print("Configuring database")
    db_set_passwords(service.db, service.vault)


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
    pw = {u: vault.read("secret/database/users/{}".format(u))["data"]["value"]
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
