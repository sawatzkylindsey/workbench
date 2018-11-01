### Workbench
Not really a meaningful name.
Project for exploring termnets in the context of educational tasks.

### Development
Requirements:

    # Python 3
    python3 -m venv p3
    source ./p3/bin/activate
    # Libraries (pip based)
    pip install nltk
    pip install rake_nltk
    pip install requests
    pip install networkx
    pip install textrank
    pip install sphinx
    pip install numpy
    # Libraries (custom)
    curl -LO https://github.com/sawatzkylindsey/pytils/archive/master.zip
    unzip master.zip
    cd pytils-master/
    make install
    curl -LO https://github.com/sawatzkylindsey/Wikipedia-API/archive/master.zip
    unzip master.zip
    cd Wikipedia-API-master/
    python setup.py install

Running:

    python dev-server.py -v

