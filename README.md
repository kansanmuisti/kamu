# Installation

The easiest way to install a development environment is the provisioning method.
If you don't want to run a virtual machine on your computer, follow the manual method.

## Provisioning method

First download and install the latest versions of [Vagrant](http://vagrantup.com) and [Ansible](http://www.ansibleworks.com/). Ubuntu and Mac OS X packages for Vagrant are available from the [Vagrant download page](http://www.vagrantup.com/downloads.html). Ubuntu packages for Ansible can be installed from a PPA:

    sudo add-apt-repository ppa:rquillo/ansible
    sudo apt-get update
    sudo apt-get install ansible

The only remaining step is to install the virtual machine:

    vagrant up

This will automatically download and provision the virtual machine. After the command completes (it will take a while), you may SSH into your VM and start the Django server:

    vagrant ssh
    cd /vagrant
    ./manage.py runserver

Now you should be able to point your browser to the VM webserver at [http://192.168.107.2/](http://192.168.107.2/). Your project directory will be shared to the VM (in /vagrant), so any changes you make on your host machine will be reflected immediately to the VM.

## Manual method

### Dependencies

- virtualenvwrapper
- python-imaging
- python-lxml
- mysql-server or postgresql
- python-mysqldb *or* python-psycopg2
- gettext
- libnode-less
- python-numpy
- subversion
- git
- opensp
- tidy
- libmalaga7

#### LESS and Coffee Script

If you don't have the libnode-less package, you need to install less
manually. First we need to install node.js, fetch source package
from http://nodejs.org/

Then you could install it with

    ./configure --prefix=/usr/local
    make
    make install


After that we can install less and coffee

    # sudo npm install -g less
    # sudo npm install -g coffee-script

### Commands

First, you need to install the .deb dependencies. You can do that by running
(as root) setup-root.sh.

If you just installed virtualenvwrapper, you need to logout and login for
the new bash aliases to kick in.

#### virtualenv

    $ mkvirtualenv kamu
    $ workon kamu
    $ python setup-site.py


#### Postgres

    $ su - postgres
    $ psql
    CREATE USER kamu WITH PASSWORD 'kamu';
    CREATE DATABASE kamu ENCODING 'utf-8' OWNER kamu;

In order to use Postgres, you need to set the right database backend in
settings_local.py. You can do that by copying the DATABASES setting from
settings.py and setting the value of ENGINE to
'django.db.backends.postgresql_psycopg2'.

#### MySQL

    CREATE DATABASE kamu CHARACTER SET utf8 COLLATE utf8_swedish_ci;
    CREATE USER 'kamu'@'localhost' IDENTIFIED BY 'kamu';
    GRANT ALL PRIVILEGES ON kamu.* TO 'kamu'@'localhost';

If your existing database is in latin1, you can convert to utf-8
like this:

ALTER DATABASE kamu DEFAULT CHARACTER SET utf8 COLLATE utf8_swedish_ci;

    echo "show tables" | ./manage.py dbshell > /tmp/tables
    for a in $(cat /tmp/tables) ; do
    	echo $a
    	ALT="alter table $a convert to character set utf8 collate utf8_swedish_ci"
    	echo $ALT | ./manage.py dbshell
    done

### The rest

First test your DB connection by:

    $ python manage.py dbshell

If everything goes well, you're ready to download and install the initial
contents:

    $ ./setup-db.sh

    $ django-admin.py compilemessages	# create the compiled locale files
    $ django-admin.py index --rebuild	# generate the search index

Varnish configuration
=====================

During development, it can be useful to apply caching similar to production.
First, install the `varnish` package. Modify `/etc/default/varnish` as follows:

    DAEMON_OPTS="-a localhost:8100 \
             -T localhost:6082 \
             -f /etc/varnish/default.vcl \
             -S /etc/varnish/secret \
             -s malloc,256m"

Next, modify `/etc/varnish/default.vcl`:

    backend default {
        .host = "127.0.0.1";
        .port = "8000";
    }

    sub vcl_recv {
        if (req.url ~ "^/api/") {
            remove req.http.cookie;
        }
    }

    sub vcl_fetch {
        if (req.url ~ "^/api/") {
            unset beresp.http.set-cookie;
        }
    }

This will instruct Varnish to use your development server as the backend
and disregard HTTP cookies when accessing the REST API.

You can now point your browser to `http://localhost:8100/` for the cached
version of the site.

Unit testing
============

To run the integrated unit tests make sure the access rights are set up
for the test framework:

    GRANT ALL PRIVILEGES ON `test_kamu`.* TO 'kamu'@'localhost';

Then just run

    ./manage.py test votes

or specify any of the other kamu applications instead of 'votes'.

If it's not important to run the tests on the mysql backend, you can
speed up the tests considerably by setting up fast testing mode. This
will use the sqlite3 backend keeping the DB in memory and use the faster
syncdb method instead of south migration.

Add to settings_local.py:

    FAST_TEST = True

Create an sqlite3 database and bring its tables synchronized to the
django models. The test framework will clone and populate this database
during test execution:

    ./manage.py syncdb
    ./manage.py migrate votes

optionally migrate also all other kamu applications besides 'votes' that
you want to test.

Then run the tests normally as described above.
