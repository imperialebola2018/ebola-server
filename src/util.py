import os.path

import docker

RSYNC_IMAGE = "imperialebola2018/rsync"


def volume_exists(volume_name, client):
    try:
        client.volumes.get(volume_name)
        return True
    except docker.errors.NotFound:
        return False


def directory_to_volume(src, dest, client, verbose, remove=False, update=False):
    if not os.path.exists(src):
        raise Exception("Source '{}' does not exist".format(src))

    if volume_exists(dest, client):
        print("Volume '{}' already exists".format(dest))
        if remove:
            print("...deleting!")
            client.volumes.get(dest).remove()
        elif not update:
            return;

    client.volumes.create(dest)
    cmd = ["rsync", "-avh", "--delete",
           "--no-owner", "--no-group",
           "/src/", "/dest"]
    src = docker.types.Mount(target="/src", source=os.path.abspath(src),
                             read_only=True, type="bind")
    dest = docker.types.Mount(target="/dest", source=dest)

    print("Importing data from disk to volume")
    res = client.containers.run(image=RSYNC_IMAGE, command=cmd,
                                remove=True, mounts=[src, dest])
    if verbose:
        print(res.decode("UTF-8"))
    print("Done")


def volume_to_directory(src, dest, client, verbose):
    if not volume_exists(src, client):
        raise Exception("Volume '{}' does not exist".format(src))
    if not os.path.exists(dest):
        os.makedirs(dest)
    elif not os.path.isdir(dest):
        raise Exception(
            "Destination path '{}' exists but is not directory".format(dest))

    st = os.stat(dest)
    owner = "{}:{}".format(st.st_uid, st.st_gid)
    cmd = ["rsync", "-avh", "--delete",
           "--owner", "--group", "--chown", owner,
           "/src/", "/dest/"]

    src_vol = docker.types.Mount(target="/src", source=src, read_only=True)
    dest_bind = docker.types.Mount(target="/dest", source=os.path.abspath(dest),
                                  type="bind")
    print("Exporting data from volume to disk")
    res = client.containers.run(image=RSYNC_IMAGE, command=cmd,
                                remove=True, mounts=[src_vol, dest_bind])
    if verbose:
        print(res.decode("UTF-8"))
    print("Done")
