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
from flask_apispec import MethodResource, doc, marshal_with

from memote_webservice.celery import celery_app
from memote_webservice.schemas import StatusResponse


__all__ = ("Status",)

LOGGER = logging.getLogger(__name__)


class Status(MethodResource):
    """Query the queue for a particular result status."""

    @doc(description="Return queue information about a task.")
    @marshal_with(StatusResponse, code=200)
    def get(self, uuid):
        result = AsyncResult(id=uuid, app=celery_app)
        return {
            "finished": result.ready(),
            "status": result.state,
        }
