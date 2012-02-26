Dependencies
============
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

LESS and Coffee Script
====================

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

Commands
========

First, you need to install the .deb dependencies. You can do that by running
(as root) setup-root.sh.

If you just installed virtualenvwrapper, you need to logout and login for
the new bash aliases to kick in.

virtualenv
----------

    $ mkvirtualenv kamu
    $ workon kamu
    $ python setup-site.py


Postgres
========

    $ su - postgres
    $ psql
    CREATE USER kamu WITH PASSWORD 'kamu';
    CREATE DATABASE kamu ENCODING 'utf-8' OWNER kamu;

In order to use Postgres, you need to set the right database backend in
settings_local.py. You can do that by copying the DATABASES setting from
settings.py and setting the value of ENGINE to
'django.db.backends.postgresql_psycopq2'.

MySQL
=====

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

The rest
========

First test your DB connection by:

    $ python manage.py dbshell

If everything goes well, you're ready to download and install the initial
contents:

    $ ./setup-db.sh
    
    $ django-admin.py compilemessages	# create the compiled locale files
    $ django-admin.py index --rebuild	# generate the search index

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
