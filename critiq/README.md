# Critiq - self-code review for your development environment
Critiq's aim is to be the one place to organize your development 
environment. It combines the power of git with a nice web interface,
 and scans for issues in your codebase before submitting for a code 
 review. It answers the following use cases, among others:
  
  * What issues am I assigned to on remote repo?
  * What branch am I currently on? 
  * What other branches am I working and are they in sync with repo?
  * What is the current test coverage?
  * What lines of code have I written since last commit and not covered
  yet?
  * What lines contain linting errors in various languages?

## Install
There are two ways to install the project - with vagrant or standalone.

### With Vagrant
If you have never touched Linux or don't like it, don't worry. The 
development environment setup assumes you may have a different OS so we 
try to isolate it using [Vagrant](https://www.vagrantup.com/) virtual 
machine management and [Virtualbox](https://www.virtualbox.org/). 
However, the setup has not been tested thoroughly and it might be a 
bit harder.

Download and install the following programs for your OS:

* [Vagrant](https://www.vagrantup.com/downloads.html) (ver >= 1.8.4)
* [VirtualBox](https://www.virtualbox.org/wiki/Downloads) (ver >= 5.1)
* [Git](https://git-scm.com/)

Open a terminal (on Windows - best open **Git Bash**) and type the 
commands below:

**Start virtual machine:**

    host $ cd critiq
    host $ vagrant up

This will start the vagrant machine and install the needed packages.
This may take a while especially the first time as vagrant will need
to download a compressed version of Ubuntu.

**Connect to virtual machine:**

    host $ vagrant ssh
    guest $

### Standalone
The setup has been tested on Ubuntu 14.04 and up. The following lines
install the needed packages and creates a python virtual environment:

```bash
sudo apt-get update
sudo apt-get install -y python-virtualenv python-pip git python-dev
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

If you are using a different Linux distribution, you might need to 
adjust the setup.

## Run
Once inside vagrant (`vagrant ssh`) you should be automatically in the
`/vagrant` folder and the python virtual environment activated. If not,
just `cd /vagrant && source venv/bin/activate`

Once there, you should be able to execute `./webapp.py` to run the web
application. On your host, you can see the server running on 
[http://localhost:5001](http://localhost:5001) 

## Test
To run the tests:

`./tests.py`

## Frameworks and tools used
### Dev Tools
* [git](https://git-scm.com/docs/gittutorial) - version controll
* [gitlab](https://gitlab.com) - for issue tracking, repository management, merge requests, code review
* [pypi](https://pypi.python.org/pypi) - Python package manager
* [Vagrant](https://www.vagrantup.com/) - reproducible dev environments
* [Virtualbox](https://www.virtualbox.org/) - virtualization

### Web
* [flask](http://flask.pocoo.org) - micro web framework
* [Jinja2](http://jinja.pocoo.org) - Templating language

### Python
* [gitpython](http://gitpython.readthedocs.io/en/stable/) - git python wrapper
* [requests](http://docs.python-requests.org/en/master/) - executing http requests
* [unittest](https://docs.python.org/2/library/unittest.html)
* [coverage](https://coverage.readthedocs.io/en/coverage-4.2/)
* [prospector](http://prospector.landscape.io/en/master/) - python static analysis

### APIs
* [GitLab API](https://docs.gitlab.com/ce/api/)