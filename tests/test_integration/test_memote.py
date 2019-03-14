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

"""Ensure that memote returns a well-defined JSON snapshot result."""

import json
from os.path import dirname, join, pardir

import memote
import pytest
from cobra.io import read_sbml_model
from jsonschema import Draft4Validator


DATA_PATH = join(dirname(__file__), pardir, "data")


@pytest.fixture(scope="module", params=[
    join(DATA_PATH, "EcoliCore.xml"),
])
def model(request):
    """Provide a model for testing that automatically resets."""
    model = read_sbml_model(request.param)
    with model:
        yield model


@pytest.mark.xfail(strict=True, reason="Schema is not up-to-date.")
def test_snapshot(model):
    """Expect the OpenAPI docs to be served at root."""
    with open(join(DATA_PATH, "store.json")) as file_handle:
        validator = Draft4Validator(json.load(file_handle))
    code, result = memote.test_model(
        model=model, results=True, pytest_args=["--tb", "no"])
    assert validator.is_valid(result)
    config = memote.ReportConfiguration.load()
    report = memote.SnapshotReport(result=result, configuration=config)
    obj = report.render_json()
    assert validator.is_valid(obj)
