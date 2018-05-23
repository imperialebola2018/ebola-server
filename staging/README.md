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

```
vagrant up
vagrant ssh -c 'sudo mount /mnt/ebola2018'
vagrant ssh -c /vagrant/deploy
```
