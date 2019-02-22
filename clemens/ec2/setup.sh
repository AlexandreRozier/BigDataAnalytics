#!/bin/bash

# Install python modules.
sudo apt-get update
sudo apt-get install python-pip python-dev build-essential -y
sudo pip install --upgrade pip
sudo pip install --upgrade virtualenv
sudo pip install boto3
# sudo pip install pymongo
sudo pip install tqdm
sudo apt-get install tmux -y

# sudo pip install tornado
# sudo pip install requests
# sudo apt-get install libcurl4-openssl-dev -y
# sudo apt-get install libssl-dev -y
# sudo pip install pycurl


echo "Setup done." |& tee -a output_console.txt

tmux new -s session1
