#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script prepares python enviroment for deploying into OpenShift cloud.
Heavily inspired by virtualenv code (actually using some parts of it).
For more see README
"""

import subprocess
import os
import sys
import stat
import optparse
try:
    import virtualenv
except ImportError:
    print "You don't have virtualenv installed!"
    print "Try pip install virtualenv or easy_install virtualenv"
    exit()

def after_install(home_dir, options):
    """
    After install steps - copying files and creating application
    script

    @param home_dir: virtualenv location
    @param options: passed commandline options
    """

    if options.app_name == None:
        app_name = "application"
    else:
        app_name = options.app_name

    # you need Python2.6 package folder (for server side)
    if sys.version_info[1] == 7:
        python27 = os.path.join('.', 'python2.7')
        python26 = os.path.join(home_dir, 'lib', 'python2.6')
        os.symlink(python27, python26)

    pip = os.path.join(home_dir, 'bin', 'pip')

    if options.framework.lower() == "flask":
        install_flask(home_dir, app_name, pip)
    elif options.framework.lower() == "django":
        install_django(home_dir, app_name, pip)

    gitignore = os.path.join(home_dir, '..', '.gitignore')
    file(gitignore, 'w').write("""\
*.pyc
*.org
*.bak
*.old
*.sw[po]
""")

def install_flask(home_dir, app_name, pip):
    """
    Installs basic Flask stack for OpenShift
     
    @param home_dir: virtualenv location
    @param app_name: Inner name of application
    @param pip: Location of pip
    """

    subprocess.call([pip, 'install', 'flask'])
    app_dir = os.path.join(home_dir, '..', 'libs', app_name)
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
        <footer>Generated by <a href = 'https://github.com/sputnikus/openshift-python-bootstrap'>OpenShift bootstrap for Python</a>, which is unofficial tool created by Martin Putniorz</footer>
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
    <li>I don't recommend to change <code>&lt;project home&gt;/wsgi/application</code></li>
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

sys.path.append(flaskapp)
execfile(activate, dict(__file__=activate))
os.environ["PYTHON_EGG_CACHE"] = pythoneggs

from """+app_name+""" import app as application

sys.stdout = sys.stderr

# For local testing

if __name__ == '__main__':
    application.run()
""")
    os.chmod(application, stat.S_IRWXU|stat.S_IRGRP|stat.S_IROTH)

def install_django(home_dir, app_name, pip):
    """
    Installs basic Django stack for OpenShift

    @param home_dir: virtualenv location
    @param app_name: Inner name of application
    @param pip: Location of pip
    """

    subprocess.call([pip, 'install', 'django'])
    libs = os.path.join(home_dir, '..', 'libs')
    root = os.getcwd()
    # django-admin.py needs to be executed in destinated directory
    os.chdir(libs)
    admin = os.path.join('..', home_dir, 'bin', 'django-admin.py')
    subprocess.call([admin, 'startproject', app_name])
    os.chdir(root)
    application = os.path.join(home_dir, '..', 'wsgi', 'application')
    os.remove(application)
    file(application, 'w').write("""\
#!/usr/bin/env python

import os
import sys

here = os.path.dirname(os.path.abspath(__file__))

djangoapp = os.path.join(here, '..', 'libs')
activate = os.path.join(here, '..', 'env', 'bin', 'activate_this.py')
pythoneggs = os.path.join(here, '..', 'data', 'python-eggs')

sys.path.append(djangoapp)
execfile(activate, dict(__file__=activate))
os.environ["PYTHON_EGG_CACHE"] = pythoneggs

os.environ['DJANGO_SETTINGS_MODULE'] = '"""+app_name+""".settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
""")
    os.chmod(application, stat.S_IRWXU|stat.S_IRGRP|stat.S_IROTH)

def main():
    parser = optparse.OptionParser(
        usage = "%prog [OPTIONS] DEST_DIR")

    parser.add_option(
        '-f', '--framework',
        action = 'store',
        dest = 'framework',
        help = "Specifies used framework (flask | django)")

    parser.add_option(
        '-n', '--name',
        action = 'store',
        dest = 'app_name',
        help = "Name of your application folder ('application' is default)")

    options, args = parser.parse_args()

    if options.framework == None:
        print "No framework specified!"
        parser.print_help()
        sys.exit(2)
    elif options.framework.lower() not in ("flask", "django"):
        print "Invalid framework specified!"
        parser.print_help()
        sys.exit(2)

    if not args:
        print "No DEST_DIR specified!"
        parser.print_help()
        sys.exit(2)
    if len(args) > 1:
        print "Invalid DEST_DIR given!"
        parser.print_help()
        sys.exit(2)

    home_dir = args[0]

    virtualenv.create_environment(home_dir, site_packages=False,
                                  use_distribute=True)

    after_install(home_dir, options)

if __name__ == '__main__':
    main()

