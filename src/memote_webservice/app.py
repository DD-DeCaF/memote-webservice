# Copyright (c) 2018, Novo Nordisk Foundation Center for Biosustainability,
# Technical University of Denmark.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Expose the main Flask application."""

import logging
import logging.config
import os

import structlog
from flask import Flask
from flask_cors import CORS
from pythonjsonlogger import jsonlogger
from raven.contrib.flask import Sentry
from werkzeug.contrib.fixers import ProxyFix

from . import errorhandlers


LOGGER = structlog.get_logger(__name__)

app = Flask(__name__)


def init_app(application):
    """Initialize the main app with config information and routes."""
    if os.environ["ENVIRONMENT"] == "production":
        from memote_webservice.settings import Production
        application.config.from_object(Production())
    elif os.environ["ENVIRONMENT"] == "testing":
        from memote_webservice.settings import Testing
        application.config.from_object(Testing())
    else:
        from memote_webservice.settings import Development
        application.config.from_object(Development())

    # Configure logging
    logging.config.dictConfig(application.config["LOGGING"])
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(jsonlogger.JsonFormatter())
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.render_to_log_kwargs,
        ],
        # comment
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure Sentry
    if application.config["SENTRY_DSN"]:
        sentry = Sentry(dsn=application.config["SENTRY_DSN"], logging=True,
                        level=logging.ERROR)
        sentry.init_app(application)

    # Add routes and resources.
    from memote_webservice import resources
    resources.init_app(application)

    # Add CORS information for all resources.
    CORS(application)

    # Register error handlers
    errorhandlers.init_app(application)

    # Please keep in mind that it is a security issue to use such a middleware
    # in a non-proxy setup because it will blindly trust the incoming headers
    # which might be forged by malicious clients.
    application.wsgi_app = ProxyFix(application.wsgi_app)

    LOGGER.debug("Successfully initialized the app.")
