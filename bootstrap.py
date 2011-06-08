#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script prepares python enviroment for deploying into OpenShift cloud.
For more see README
"""

import subprocess
import os
import sys
import stat
try:
    import virtualenv
except ImportError:
    print "You don't have virtualenv installed!"
    print "Try pip install virtualenv or easy_install virtualenv"
    exit()

def after_install(options, home_dir):
    """
    After install steps - copying files and creating application
    script
    """
    if sys.version_info[1] == 7:
        python27 = os.path.join(home_dir, 'lib', 'python2.7')
        python26 = os.path.join(home_dir, 'lib', 'python2.6')
        os.symlink(python27, python26)
    pip = os.path.join(home_dir, 'bin', 'pip')
    subprocess.call([pip, 'install', 'flask'])
    app_dir = os.path.join(home_dir, '..', 'libs', 'application')
    os.makedirs(app_dir)
    # basic Flask application
    init = os.path.join(app_dir, '__init__.py')
    file(init, 'w').write("""\
from flask import Flask, render_template
app = Flask(__name__)

DEBUG = True

@app.route("/")
def index():
    return render_template("index.html")
""")
    # Some templates, just to prove
    templates = os.path.join(app_dir, 'templates')
    os.makedirs(templates)
    base = os.path.join(templates, 'base.html')
    file(base, 'w').write("""\
<!DOCTYPE html>
<html>
    <head>
        <title>It works!</title>
    </head>
    <body>
        <h1>This is generated testing page</h1>
        <div id = 'content'>{% block content %}{% endblock %}</div>
        <footer>Created by OpenShift bootstrap for Python, which is unofficial tool created by Martin Putniorz</footer>  
    </body>
</html>
""")
    index = os.path.join(templates, 'index.html')
    file(index, 'w').write("""\
{% extends "base.html" %}
{% block content %}
Hi, some instructions for you:
<ul>
    <li>Your app goes to <code>&lt;project home&gt;/libs/application</code></li>
    <li>I don't recommend changing <code>&lt;project home&gt;/wsgi/application</code></li>
{% endblock %}
""")
    # and, of course, wsgi script
    application = os.path.join(home_dir, '..', 'wsgi', 'application')
    os.remove(application)
    file(application, 'w').write("""\
#!/usr/bin/env python

import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
flaskapp = os.path.join(here, "../libs")
activate = os.path.join(here, "../env/bin/activate_this.py")
pythoneggs = os.path.join(here, "../data/python-eggs")

sys.path.insert(0, flaskapp)
execfile(activate, dict(__file__=activate))
os.environ["PYTHON_EGG_CACHE"] = pythoneggs

from application import app as application

sys.stdout = sys.stderr

# For local testing

if __name__ == '__main__':
    application.run()
""")
    os.chmod(application, stat.S_IRWXU|stat.S_IRGRP|stat.S_IROTH)
virtualenv.after_install = after_install

def adjust_options(options, args):
    """
    Force no site packages option and distribute option 
    """
    options.no_site_packages = True
    options.use_distribute = True
virtualenv.adjust_options = adjust_options

if __name__ == '__main__':
    virtualenv.main()
