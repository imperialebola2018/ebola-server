import os.path
import re

import docker

RSYNC_IMAGE = "imperialebola2018/rsync"


def volume_exists(volume_name, client):
    try:
        client.volumes.get(volume_name)
        return True
    except docker.errors.NotFound:
        return False


def volume_import(src, dest, client, verbose, remove=False, update=False):
    # This is possibly a bit magic, not sure:
    re_tar = re.compile(r"\.tar(\.(gz|bz2))?$")
    m = re_tar.search(src)
    if m:
        archive_to_volume(src, dest, m.groups()[1], client, verbose, remove)
    else:
        directory_to_volume(src, dest, client, verbose, remove, update)


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


def archive_to_volume(src, dest, compression, client, verbose, remove=False):
    if not os.path.exists(src):
        raise Exception("Source '{}' does not exist".format(src))

    if volume_exists(dest, client):
        print("Volume '{}' already exists".format(dest))
        if remove:
            print("...deleting!")
            client.volumes.get(dest).remove()
        else:
            raise Exception("Not continuing")

    client.volumes.create(dest)

    flags = "-{}xvf".format(tar_compression_flag(compression))
    if compression:
        target = "/src.tar.{}".format(compression)
    else:
        target = "/src.tar"

    cmd = ["tar", "-C", "/dest", flags, target]
    src = docker.types.Mount(target=target, source=os.path.abspath(src),
                             read_only=True, type="bind")
    dest = docker.types.Mount(target="/dest", source=dest)

    print("Importing data from archive to volume")
    res = client.containers.run(image=RSYNC_IMAGE, command=cmd,
                                remove=True, mounts=[src, dest])
    if verbose:
        print(res.decode("UTF-8"))
    print("Done")


def volume_export(src, dest, client, verbose):
    # This is possibly a bit magic, not sure:
    re_tar = re.compile(r"\.tar(\.(gz|bz2))?$")
    m = re_tar.search(dest)
    if m:
        volume_to_archive(src, dest, m.groups()[1], client, verbose)
    else:
        volume_to_directory(src, dest, client, verbose)


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
    print("Exporting data from volume to directory on disk")
    res = client.containers.run(image=RSYNC_IMAGE, command=cmd,
                                remove=True, mounts=[src_vol, dest_bind])
    if verbose:
        print(res.decode("UTF-8"))
    print("Done")


def volume_to_archive(src, dest, compression, client, verbose):
    if not volume_exists(src, client):
        raise Exception("Volume '{}' does not exist".format(src))

    flags = "-{}cvf".format(tar_compression_flag(compression))
    if compression:
        target = "/dest.tar.{}".format(compression)
    else:
        target = "/dest.tar"

    cmd = ["tar", "-C", "/src", flags, target, "."]

    # Create the file so that we get reasonable permissions:
    with open(dest, "wb") as f:
        pass

    src_vol = docker.types.Mount(target="/src", source=src, read_only=True)
    dest_bind = docker.types.Mount(target=target,
                                   source=os.path.abspath(dest),
                                   type="bind")
    print("Exporting data from volume to tar archive")
    res = client.containers.run(image=RSYNC_IMAGE, command=cmd,
                                remove=True, mounts=[src_vol, dest_bind])
    if verbose:
        print(res.decode("UTF-8"))
    print("Done")


def tar_compression_flag(ext):
    if ext:
        return {"gz": "z", "bz2": "j"}[ext]
    else:
        return ""
