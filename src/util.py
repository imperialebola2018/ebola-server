import os.path

import docker


def volume_exists(volume_name, client):
    try:
        client.volumes.get(volume_name)
        return True
    except docker.errors.NotFound:
        return False


def directory_to_volume(src, dest, client, remove=False):
    if not os.path.exists(src):
        raise Exception("Source '{}' does not exist".format(src))

    if volume_exists(dest, client):
        print("Volume '{}' already exists".format(dest))
        if remove:
            print("...deleting!")
            client.volumes.get(dest).remove()
        else:
            return;

    client.volumes.create(dest)
    cmd = ["ash", "-c", "cd /src; tar cf - . | (cd /dest && tar xf -)"]
    src = docker.types.Mount(target="/src", source=os.path.abspath(src),
                             read_only=True, type="bind")
    dest = docker.types.Mount(target="/dest", source=dest)

    print("Copying data")
    client.containers.run(image="alpine", command=cmd,
                          remove=True, mounts=[src, dest])
    print("Done")
