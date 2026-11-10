"""Spending Tracker: a small Flask app for logging and reviewing expenses."""

import os

from flask import Flask

from . import budgets, dashboard, db, routes


def create_app(test_config=None):
    """Application factory. Tests pass test_config to get an isolated app."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # The default is for local development only. Set SECRET_KEY in production.
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        DATABASE=os.path.join(app.instance_path, "tracker.sqlite"),
    )
    if test_config is not None:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    app.register_blueprint(routes.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(budgets.bp)
    return app
