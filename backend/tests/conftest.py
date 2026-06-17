"""Fixtures compartilhadas para testes do backend."""

import pytest
from app import app as flask_app


@pytest.fixture
def app():
    """Retorna a Flask app configurada para teste."""
    flask_app.config.update({"TESTING": True})
    return flask_app
