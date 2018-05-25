## Staging

### Requirements

Install in the host machine:

* [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
* [Vagrant](https://www.vagrantup.com/downloads.html)

```
wget -q https://www.virtualbox.org/download/oracle_vbox_2016.asc -O- | sudo apt-key add -
sudo add-apt-repository \
     "deb http://download.virtualbox.org/virtualbox/debian \
     $(lsb_release -cs) \
     contrib"
sudo apt-get update
sudo apt-get install -y virtualbox-5.2
wget https://releases.hashicorp.com/vagrant/2.1.1/vagrant_2.1.1_x86_64.deb
sudo dpkg --install vagrant_2.1.1_x86_64.deb
```

### Getting going

On the _host_ machine (ebola2018.dide.ic.ac.uk), run the following commands.

```
git clone https://github.com/imperialebola2018/ebola-server/staging staging
cd staging/staging
```

First, login to the vault and arrage credentials

```
../ebola-server vault-login
cp ../.vault_token shared
```

Then get a copy of the current outputs (*this is going to change as soon as we have a canonical copy*)

```
git clone git@github.com:imperialebola2018/ebola-outputs shared/ebola-outputs
git -C shared/ebola-outputs checkout minimontagu
```

then

```
vagrant up
vagrant ssh -c 'sudo mount /mnt/ebola2018'
vagrant ssh -c /vagrant/deploy
```

After a while you should be able to log into https://ebola2018.dide.ic.ac.uk:1443
