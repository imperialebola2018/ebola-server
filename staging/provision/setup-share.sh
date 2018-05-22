apt-get update
apt-get install -y cifs-utils

mkdir -p /mnt/ebola2018
if grep -q /mnt/ebola2018 /etc/fstab; then
    echo "Share already set up"
else
    echo "Adding share"
    cat /vagrant/fstab >> /etc/fstab
fi
