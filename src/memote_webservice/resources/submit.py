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

"""Provide a resource to submit models for testing."""

import tempfile
from bz2 import BZ2File
from gzip import GzipFile
from io import BytesIO
from itertools import chain
from uuid import uuid4

import memote
import structlog
import werkzeug
from cobra.io import load_json_model
from cobra.io.sbml import CobraSBMLError
from flask import abort
from flask_apispec import MethodResource, doc, marshal_with, use_kwargs

from memote_webservice.exceptions import SBMLValidationError
from memote_webservice.schemas import SubmitRequest, SubmitResponse
from memote_webservice.tasks import model_snapshot


__all__ = ("Submit",)

LOGGER = structlog.get_logger(__name__)


class Submit(MethodResource):
    """Submit a metabolic model for testing."""

    JSON_TYPES = {
        "application/json",
        "text/json"
    }
    XML_TYPES = {
        "application/xml",
        "text/xml"
    }

    @doc(description="Load a metabolic model and submit it for testing by "
                     "memote.")
    @use_kwargs(SubmitRequest, locations=('files',))
    @marshal_with(SubmitResponse, code=202)
    @marshal_with(None, code=400)
    @marshal_with(None, code=415)
    def post(self, model):
        # Save the uploaded models on the local filesystem, for easier debugging
        # of any potential issues with testing the model.
        filename = werkzeug.secure_filename(model.filename)
        path = f"models/{str(uuid4())}_{filename}"
        LOGGER.info(f"Dumping uploaded model to: {path}")
        with open(path, "wb") as file_:
            file_.write(model.read())
            model.stream.seek(0)

        model = self._load_model(model)
        job_id = self._submit(model)

        # Show which submitted job id relates to which model file.
        LOGGER.info(f"Job ID {job_id} was queued from model file: {path}")
        return {"uuid": job_id}, 202

    def _submit(self, model):
        result = model_snapshot.delay(model)
        LOGGER.debug(f"Successfully submitted job '{result.id}'.")
        return result.id

    def _load_model(self, file_storage):
        try:
            filename, content = self._decompress(file_storage.filename.lower(),
                                                 file_storage)
        except IOError as err:
            msg = f"Failed to decompress file: {str(err)}"
            LOGGER.exception(msg)
            abort(400, msg)
        try:
            if file_storage.mimetype in self.JSON_TYPES or \
                    filename.endswith("json"):
                LOGGER.debug("Loading model from JSON using cobrapy.")
                model = load_json_model(content)
            elif file_storage.mimetype in self.XML_TYPES or \
                    filename.endswith("xml") or filename.endswith("sbml"):
                LOGGER.debug("Loading model from SBML using memote.")
                # Memote accepts only a file path, so write to a temporary file.
                with tempfile.NamedTemporaryFile() as file_:
                    file_.write(content.getvalue())
                    file_.seek(0)
                    model, sbml_ver, notifications = memote.validate_model(
                        file_.name,
                    )
                if model is None:
                    LOGGER.info("SBML validation failure")
                    raise SBMLValidationError(
                        code=400,
                        warnings=notifications['warnings'],
                        errors=notifications['errors'],
                    )
            else:
                mime_types = ', '.join((chain(self.JSON_TYPES, self.XML_TYPES)))
                msg = (
                    f"'{file_storage.mimetype}' is an unhandled MIME type. "
                    f"Recognized MIME types are: {mime_types}"
                )
                LOGGER.warning(msg)
                abort(415, msg)
        except (CobraSBMLError, ValueError) as err:
            msg = f"Failed to parse model: {str(err)}"
            LOGGER.exception(msg)
            abort(400, msg)
        finally:
            content.close()
            file_storage.close()
        return model

    @staticmethod
    def _decompress(filename, content):
        if filename.endswith(".gz"):
            filename = filename[:-3]
            LOGGER.debug("Unpacking gzip compressed file.")
            with GzipFile(fileobj=content, mode="rb") as zipped:
                content = BytesIO(zipped.read())
        elif filename.endswith(".bz2"):
            filename = filename[:-4]
            LOGGER.debug("Unpacking bzip2 compressed file.")
            with BZ2File(content, mode="rb") as zipped:
                content = BytesIO(zipped.read())
        else:
            content = BytesIO(content.read())
        return filename, content
