##INSTALL OS
install Centos tanpat penambahan user lain (hanya root)
------------

## INSTALL MYSQL
instruksi install ada di link dibawah:
https://dinfratechsource.com/2018/11/10/how-to-install-latest-mysql-5-7-21-on-rhel-centos-7/
----------------------------------------------------------

## OPEN MYSQL root MENGGUNAKAN PASSWORD GRANT (SEMENTARA) & CREAD USER ADMIN
create user admin, grant all, flush privileges and host '%' don't localhost
instruksi ada di link dibawah:
https://stackoverflow.com/questions/19101243/error-1130-hy000-host-is-not-allowed-to-connect-to-this-mysql-server
----------------------------------------------------------

## RUNNING HTTPD
# systemctl start httpd 
-----------------------------------------------------------

## Aktifkan service http
#firewall-cmd --permanent --zone=public --add-service=http
https://musaamin.web.id/cara-setting-firewall-dengan-firewalld-di-centos-7/
-----------------------------------------------------------

## UNTUK CEK PORT YANG DIBUKA (OPTIONAL) 
https://www.thegeekdiary.com/centos-rhel-how-to-find-if-a-network-port-is-open-or-not/
-----------------------------------------------------------

##Install DIRENV
Download direnv as root
```
download direnv (save di /home)
# wget https://github.com/direnv/direnv/releases/download/v2.20.0/direnv.linux-amd64 
```
Change name file has been download as root
``` 
# mv direnv.linux-amd64 direnv
```
Change permission file as root
```
# chmod +x direnv
```
Copy file into /usr/bin as root
```
# cp direnv /usr/bin
-----------------------------------------------------------

## BASH
Add the following line at the end of the ~/.bashrc file:
```
eval "$(direnv hook bash)"
------------------------------------------------------------

## ZSH create file .zshrc
buat file baru
# nano ~/.zshrc
Add the following line at the end of the ~/.zshrc file:
```
eval "$(direnv hook zsh)"
-------------------------------------------------------------

## Install PyEnv
First install required packages
```
# yum -y install epel-release
# yum install git gcc zlib-devel bzip2-devel readline-devel sqlite-devel openssl-devel
```
If fail install pyenv add packages below
```
# yum install zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel xz xz-devel libffi-devel findutils
```
# curl -L https://raw.github.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash

```
At the end of the installation you’ll get a warning:
```
WARNING: seems you still have not added 'pyenv' to the load path.

# Load pyenv automatically by adding
# the following to ~/.bash_profile:

export PATH="/home/nahmed/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```
You must add the above 3 lines at the end of your ~/.bash_profile in directory HOME/user
```
# echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bash_profile
# echo 'eval "$(pyenv init -)"' >> ~/.bash_profile
# echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bash_profile

delete 'export Path'
```
Once the above lines are added, restart your shell or simply reload the profile:
```
# source ~/.bash_profile
```
check pyenv has been install
```
# pyenv
------------------------------------------------------------

## Install wkhtmltopdf
install dependencies
```
# yum install -y xorg-x11-fonts-75dpi
# yum install -y xorg-x11-fonts-Type1
# yum install xz
```
install wkhtmltopdf
```
(save di /home)
# wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
```
Untar and move wkhtmltox
```
# unxz wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
# tar -xvf wkhtmltox-0.12.4_linux-generic-amd64.tar
# mv wkhtmltox /usr/bin/wkhtmltox 

copy /usr/bin/wkhtmltox/bin to /usr/bin
atau
copy /home/wkhtmltox/bin to /usr/bin
```
check wkhtmtopdf
```
# wkhtmltopdf -V
-------------------------------------------------------------

## Setup Backend Track-Go
Create folder backend on home directory
```
# mkdir $HOME/backend
```
Setup pyenv in directory backend
```
# cd $HOME/backend
# pyenv install 3.5.3
```
Wait until install finish
```
# pyenv shell 3.5.3                 >> Ganti Versi python
# pip install virtualenv
# virtualenv env
```
Create file .envrc
```
# nano .envrc
```
Add into .envrc
```
source $HOME/backend/env/bin/activate
```
Allow direnv
```
# direnv allow
---------------------------------------------------------------

Logout from ssh then login again
setup environment python has been finish
then copy folder backend into backend folder
after copy into folder backend
```
# cd $HOME/backend/trackgo-api/
```
install requirement lib for python
```
# yum install libmysqlclient-dev python-dev
# yum install mysql-devel

jangan lupa '$ source ~/.bash_profile' harus diaktifkan dulu

# pip install -r requirements.txt
```
wait until finish install.

Setup Configuration
```
$ nano $HOME/backend/rest/configuration.py
```
Change line ```:1055```
```
# TODO: MySQL Configuration
['MYSQL_HOST'] = 'localhost'
['MYSQL_USER'] = 'root'
['MYSQL_PASSWORD'] = 'secret'
['MYSQL_DB'] = '123'
['MYSQL_CURSORCLASS'] = 'DictCursor'
['MYSQL_CONNECT_TIMEOUT'] = 30
```
setting mysql host, mysql user and mysql pass

backend has been setup

### Change library flask-fcm (locate)
```
# /HOME/backend/env/lib/python3.5/site-packages/flask_fcm.py

```
lalu rubah isi file ```flask_fcm.py```
```
$ sudo nano flask_fcm.py
```
rubah isi dari line ```:28``` dengan script dibawah
```
    def notify_single_device(self, *args, **kwargs):
        response = self.service.notify_single_device(*args, **kwargs)
        if int(response['failure']) > 0:
            self.handle_failure()
        return True

    def notify_multiple_devices(self, *args, **kwargs):
        response = self.service.notify_multiple_devices(*args, **kwargs)
        if int(response['failure']) > 0:
            self.handle_failure()
        return True

    def handle_failure(self):
        raise Exception("Failed to send notification")
```

### Running Application as services
- create service file or copy trackgo-cis.service to directory /etc/systemd/system
```
[Unit]
Description=Track-Go REST-API
After=syslog.target network.target

[Service]
User=root
ExecStart=/bin/bash -c "source $HOME/backend/env/bin/activate ; python $HOME/backend/trackgo-api/wsgi.py -p 7091 >> /var/log/trackgo/trackgo.log"
Restart=always
RestartSec=180s

[Install]
WantedBy=multi-user.target
```
if want change port or add another port change name service and change following line:
example
```
ExecStart=/bin/bash -c "source /home/backend/env/bin/activate ; python /home/backend/trackgo-api/wsgi.py -p 7091 >> /var/log/trackgo/trackgo.log"
```
became
```
ExecStart=/bin/bash -c "source /home/backend/env/bin/activate ; python /home/backend/trackgo-api/wsgi.py -p 7092 >> /var/log/trackgo/trackgo-7092.log"
```
- enable service
```
# systemctl enable trackgo-cis.service
``` 

- start service
```
# systemctl start trackgo-cis.service
-----------------------------------------------------



Setup Configuration For Tracking System

### Change MySQL Credential on rest/configuration.py find configuration below and change it with yours

MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'your_password'
MYSQL_DB = 'your_db'

### Change Log file in order to Logging and it must be filled

LOG_FILE = '/var/log/trackgo-api-beton/trackgo.log'

### Set Session Configuration

HOST_USSAGE_WSGI = 'localhost'
PORT_USSAGE_WSGI = '7091'

### Change Email Configuration

MAIL_DEFAULT_SENDER = "email@betonworks.co.id"
MAIL_FINANCE_RECIPIENTS = "email@betonworks.co.id"

### To Generate MySQL please make sure generateDB_conn.py have been change with yours configuration, and find

self.host = "localhost"
self.user = "root"
self.passwd = "your_password"
self.charSet = "utf8mb4"

### Open generateDB_app.py for generate MySQL and find configuration below also change it

cur, conn = myDB.get_session('your_database')

company = [{
    "prefix_db": "trackgo_cisangkan",
    "name": "PT. Cisangkan",
    "phone": "",
    "email": "",
    "address": ""
}]

### Create DB 
CREATE DATABASE trackgo_cisangkan di mysql

kemudian generate 
$ python generateDB_conn.py
$ python generateDB_app.py


