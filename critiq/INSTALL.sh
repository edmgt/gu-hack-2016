sudo apt-get update
sudo apt-get install -y python-virtualenv python-pip git python-dev
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
cat >> ~/.bashrc <<EOF
cd /vagrant
source venv/bin/activate
alias a='source venv/bin/activate'
EOF
