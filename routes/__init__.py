from flask import Blueprint
from .game_routes import game_routes

def register_blueprints(app):
    """Register all blueprints to the Flask app."""
    app.register_blueprint(game_routes, url_prefix="/games")