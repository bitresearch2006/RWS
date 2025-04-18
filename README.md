# RWS
Web server to connect the different services

Folder Structure
RWS/
├── Main/
├── Doc/
└── Test/

Main will have original code for work
Doc will have documents related to test , requirement 
Test will have test app, depency code for testing

Deploy the RWS
Step1:
cd platform                                 # as all services run from 'platform'
Step2:
git clone https://github.com/bitresearch2006/RWS.git
Step3:
cd RWS
Step4: 
virtualenv --system-site-packages pyenv     # Create a virtual environment named 'pyenv' with system site packages
Step4_1: 
source /home/bitresearch/platform/py_env/bin/activate   # optional step, if required to install any python pkg by 'pip install pkg'
Step4_2:
to run RWS in here for test: python RWS.py <port> <config_file> <database_path> --diagnostics
Step5:
mv RWS.service /etc/systemd/system/RWS.service  # if required server with feature diagnostics, use RWS_debug.service
Step6:
sudo systemctl stop RWS.service         # Stop the service, if it is run already
Step7:
sudo systemctl start RWS.service        # Start the service
Step8:
sudo systemctl status RWS.service       # to fine the status running service
Step8:
sudo systemctl enable RWS.service       #Enable service for when system boot up
Step9:
sudo systemctl disable RWS.service      # disble in boot, if required 

Access the micro services
Http request using POST method

payload = {
    "X-API-Key": "9f081bdf8c7679fbd9cfa499cd1da70892ed0d18c208dd602f0d9d20931b5589" # zero key
    "request_type": "INLINE",
    "service_name": "add",
    "sub_json": {"a": 10, "b": 30}
}




