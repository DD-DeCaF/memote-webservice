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

"""Provide settings for different deployment scenarios."""

import logging
import os

import werkzeug.exceptions


__all__ = ("Development", "Testing", "Production")


class Default:
    """Set the default configuration for all environments."""

    def __init__(self):
        """
        Initialize the default configuration.

        We chose configuration by instances in order to avoid ``KeyError``s
        from environments that are not active but access
        ``os.environ.__getitem__``.
        """
        self.DEBUG = True
        self.APISPEC_TITLE = "Memote Webservice"
        self.APISPEC_SWAGGER_UI_URL = "/"
        # 25 MB default limit (size of Recon3D).
        self.MAX_CONTENT_LENGTH = int(os.environ.get(
            "MAX_CONTENT_LENGTH", 25 * 1024 * 1024))
        self.SECRET_KEY = os.urandom(24)
        self.BUNDLE_ERRORS = True
        self.CORS_ORIGINS = os.environ['ALLOWED_ORIGINS'].split(',')
        self.REDIS_URL = os.environ['REDIS_URL']
        self.SENTRY_DSN = os.environ.get('SENTRY_DSN')
        self.SENTRY_CONFIG = {
            'ignore_exceptions': [
                werkzeug.exceptions.BadRequest,
                werkzeug.exceptions.Unauthorized,
                werkzeug.exceptions.Forbidden,
                werkzeug.exceptions.NotFound,
                werkzeug.exceptions.MethodNotAllowed,
            ]
        }

        # Add a specific log filter to exclude a log statement by cobrapy which
        # seems to repeat for all/most metabolites when loading certain models:
        # 'Foo' is not a valid SBML 'SId'.
        class CobraFilter(logging.Filter):
            def filter(self, record):
                return "is not a valid SBML 'SId'" not in record.msg
        self.LOGGING = {
            'version': 1,
            'disable_existing_loggers': False,
            'filters': {
                'cobrapy': {
                    '()': CobraFilter,
                }
            },
            'formatters': {
                'simple': {
                    'format': (
                        "%(asctime)s [%(levelname)s] [%(name)s] %(filename)s:%("
                        "funcName)s:%(lineno)d | %(message)s"
                    )
                },
            },
            'handlers': {
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'simple'
                },
            },
            'loggers': {
                # All loggers will by default use the root logger below (and
                # hence be very verbose). To silence spammy/uninteresting log
                # output, add the loggers here and increase the loglevel.
                'pip': {
                    'level': 'INFO',
                },
                'cobra.io.sbml': {
                    'level': 'DEBUG',
                    'handlers': ['console'],
                    'propagate': True,
                    'filters': ['cobrapy'],
                }
            },
            'root': {
                'level': 'DEBUG',
                'handlers': ['console'],
                'propagate': True,
            },
        }


class Development(Default):
    """Development environment configuration."""

    pass


class Testing(Default):
    """Testing environment configuration."""

    def __init__(self):
        """Initialize the testing environment configuration."""
        super().__init__()
        self.TESTING = True


class Production(Default):
    """Production environment configuration."""

    def __init__(self):
        """
        Initialize the production environment configuration.

        Require a secret key to be defined and make logging slightly less
        verbose.
        """
        super().__init__()
        self.DEBUG = False
        self.SECRET_KEY = os.environ['SECRET_KEY']
        self.LOGGING['root']['level'] = 'INFO'
