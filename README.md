## ebola-server

Repurpose vimc's api server to work with the ebola response.  This is a work in progress.


```
pip3 install -r requirements.txt
```

then

```
./scripts/prepare_orderly_volume ebola-outputs
./scripts/generate_passwords
./ebola-server start
```
