## ebola-server

Repurpose vimc's api server to work with the ebola response.  This is a work in progress.

## Prerequisites

* [Docker Community Edition](https://docs.docker.com/engine/installation/)
* [Docker Compose](https://docs.docker.com/compose/install/) - at least version 0.17.0
* Python 3 and pip (Python 3 is included with Ubuntu. For pip, use `apt install python3-pip`)

```
pip3 install -r requirements.txt

```

then

```
./scripts/generate_passwords
./ebola-server set-configuration production
./ebola-server vault-login
./ebola-server create-orderly-volume ebola-outputs
./ebola-server start
```

### Images

Some work needed to prepare images, and none of this is automated yet

Republish base image for building the orderly server:

```
docker pull docker.montagu.dide.ic.ac.uk:5000/orderly.server:master
docker image tag docker.montagu.dide.ic.ac.uk:5000/orderly.server:master \
  vimc/orderly.server:master
docker push vimc/orderly.server:master
```

Republish the modified version of the reporting api

```
docker.montagu.dide.ic.ac.uk:5000/montagu-reporting-api:ebola
docker image tag docker.montagu.dide.ic.ac.uk:5000/montagu-reporting-api:ebola \
  vimc/montagu-reporting-api:ebola
docker push vimc/montagu-reporting-api:ebola
```

and also publish our images

```
docker push imperialebola2018/ebola-db:latest
docker push imperialebola2018/ebola-proxy:latest
docker push imperialebola2018/ebola-orderly:latest
```
