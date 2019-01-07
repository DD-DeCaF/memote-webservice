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

"""Define individual jobs."""

import cobra
import memote

from .celery import celery_app


@celery_app.task
def model_snapshot(model):
    """Run memote on the given model and create a snapshot report."""
    configuration = cobra.Configuration()
    configuration.processes = 1
    _, result = memote.test_model(model, results=True,
                                  pytest_args=["-vv", "--tb", "long"])
    config = memote.ReportConfiguration.load()
    return memote.SnapshotReport(result=result, configuration=config)
