import os
import sys
import flask
import argparse
from flask.ext import admin

import taskpy.views
from taskpy.models import db
from taskpy.worker import celery

def make_app():
	# Setup flask and settings
	app = flask.Flask(__name__)
	app.secret_key = 'taskpy123'
	app.config['TASKPY_BASE'] = os.path.expanduser(os.path.join('~', '.taskpy'))
	app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % os.path.join(app.config['TASKPY_BASE'], 'main.db')

	print "Base directory: %s" % app.config['TASKPY_BASE']
	print "Database: %s" % app.config['SQLALCHEMY_DATABASE_URI']

	# Make sure TASKPY_BASE exists
	if not os.path.exists(app.config['TASKPY_BASE']):
		os.mkdir(app.config['TASKPY_BASE'])

	# Init database
	db.init_app(app)
	db.app = app
	db.create_all()

	# Add views
	index_view = taskpy.views.JobsView(name="Jobs", endpoint="jobs", url='/')
	admin_app = admin.Admin(app, name='Taskpy', index_view=index_view, base_template='admin_base.html')
	admin_app.add_view(taskpy.views.TasksView(name="Tasks", endpoint="tasks"))

	# Static bootstrap files (required by flask-admin)
	admin_app.add_view(taskpy.views.AdminStatic(url='/_'))

	return app

def main():
	# Setup argument parser
	parser = argparse.ArgumentParser()
	parser.add_argument("--host"
				, required=False, default='127.0.0.1'
				, help="Host interface to bind to")
	args = parser.parse_args()
	app = make_app()
	app.run(debug=True, host=args.host)

def celery_main():
	# Setup argv to add the 'worker' command for celery
	argv = sys.argv
	argv.insert(1, 'worker')

	# Run celery under the flask context
	# to allow it to access the database
	app = make_app()
	with app.app_context():
		celery.start(argv)

if __name__ == "__main__":
	main()
