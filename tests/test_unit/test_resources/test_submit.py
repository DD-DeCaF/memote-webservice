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

"""Test expected functioning of the resources."""

from os.path import dirname, join

import pytest
# from cobra.io.sbml3 import CobraSBMLError
from werkzeug.datastructures import FileStorage

from memote_webservice.resources.submit import Submit


DATA_PATH = join(dirname(__file__), "..", "..", "data")


@pytest.mark.parametrize("filename", [
    join(DATA_PATH, "EcoliCore.xml"),
    join(DATA_PATH, "EcoliCore.xml.gz"),
    join(DATA_PATH, "EcoliCore.xml.bz2"),
    # pytest.mark.raises(join(DATA_PATH, "half.xml"), exception=CobraSBMLError),
    # pytest.mark.raises(join(DATA_PATH, "notgzip.xml.gz"),
    #                    exception=ValueError),
    # pytest.mark.raises(join(DATA_PATH, "notbzip2.xml.bz2"),
    #                    exception=ValueError),
])
def test__decompress(filename):
    """Ensure that the app is in testing mode."""
    with open(filename, mode="rb") as file_handle:
        name, content = Submit._decompress(filename, file_handle)
    assert name.endswith("EcoliCore.xml")
    assert len(content.read()) >= 494226


@pytest.mark.parametrize("filename", [
    join(DATA_PATH, "EcoliCore.xml"),
    join(DATA_PATH, "EcoliCore.xml.gz"),
    join(DATA_PATH, "EcoliCore.xml.bz2"),
    # pytest.mark.raises(join(DATA_PATH, "half.xml"), exception=CobraSBMLError),
    # pytest.mark.raises(join(DATA_PATH, "notgzip.xml.gz"),
    #                    exception=ValueError),
    # pytest.mark.raises(join(DATA_PATH, "notbzip2.xml.bz2"),
    #                    exception=ValueError),
])
def test__load_model(filename):
    """Ensure that the app is in testing mode."""
    file_storage = FileStorage(stream=open(filename, mode="rb"),
                               filename=filename, name="model")
    model = Submit()._load_model(file_storage)
    assert len(model.reactions) == 95
    assert len(model.metabolites) == 72
    assert file_storage.closed
