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

"""Provide a resource for retrieving test results."""

import logging

from celery.result import AsyncResult
from flask import jsonify, make_response, render_template, request
from flask_apispec import MethodResource, doc, marshal_with

from memote_webservice.celery import celery_app


__all__ = ("Report",)

LOGGER = logging.getLogger(__name__)


class Report(MethodResource):
    """Provide endpoints for metabolic model testing."""

    @doc(description="Return a snapshot report as JSON or HTML based on Accept "
                     "headers.")
    @marshal_with(None, code=200)
    @marshal_with(None, code=404)
    def get(self, uuid):
        result = AsyncResult(id=uuid, app=celery_app)
        if not result.ready():
            LOGGER.info(f"Result {uuid} is pending; assuming it is expired.")
            return make_response(render_template('404.html'), 404)
        elif result.failed():
            exception = result.get(propagate=False)
            return jsonify({
                'status': result.state,
                'exception': type(exception).__name__,
                'message': str(exception),
            })
        else:
            try:
                _, report = result.get()
            except TypeError:
                # Expected for results generated before the result type changed.
                # When those results expire (about 2 weeks from 2019-03-27
                # assuming this commit is deployed today), this handler can be
                # removed.
                report = result.get()

            mime_type = request.accept_mimetypes.best_match([
                'text/html',
                'application/json',
            ])
            if mime_type == 'text/html':
                LOGGER.debug("Rendering HTML report based on mime type.")
                return make_response(report.render_html())
            else:
                LOGGER.debug("Rendering JSON report based on mime type.")
                return make_response(report.render_json())
