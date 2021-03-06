""" Tests of the command-line interface

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-10-29
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from biosimulators_boolnet import __main__
from biosimulators_boolnet import core
from biosimulators_utils.combine import data_model as combine_data_model
from biosimulators_utils.combine.io import CombineArchiveWriter
from biosimulators_utils.report import data_model as report_data_model
from biosimulators_utils.report.io import ReportReader
from biosimulators_utils.simulator.exec import exec_sedml_docs_in_archive_with_containerized_simulator
from biosimulators_utils.simulator.specs import gen_algorithms_from_specs
from biosimulators_utils.sedml import data_model as sedml_data_model
from biosimulators_utils.sedml.io import SedmlSimulationWriter
from biosimulators_utils.sedml.utils import append_all_nested_children_to_doc
from unittest import mock
import datetime
import dateutil.tz
import json
import numpy
import numpy.testing
import os
import shutil
import tempfile
import unittest


class CliTestCase(unittest.TestCase):
    EXAMPLE_MODEL_FILENAME = os.path.join(os.path.dirname(__file__), 'fixtures', 'example-model.xml')
    SPECIFICATIONS_FILENAME = os.path.join(os.path.dirname(__file__), '..', 'biosimulators.json')
    DOCKER_IMAGE = 'ghcr.io/biosimulators/biosimulators_boolnet/boolnet:latest'
    NAMESPACES = {
        'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
        'qual': 'http://www.sbml.org/sbml/level3/version1/qual/version1',
    }

    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_exec_sed_task_successfully(self):
        task = sedml_data_model.Task(
            model=sedml_data_model.Model(
                source=self.EXAMPLE_MODEL_FILENAME,
                language=sedml_data_model.ModelLanguage.SBML.value,
            ),
            simulation=sedml_data_model.UniformTimeCourseSimulation(
                initial_time=0,
                output_start_time=10,
                output_end_time=15,
                number_of_points=5,
                algorithm=sedml_data_model.Algorithm(
                    kisao_id='KISAO_0000449',
                    changes=[
                        sedml_data_model.AlgorithmParameterChange(
                            kisao_id='KISAO_0000572',
                            new_value='0.0',
                        ),
                    ],
                ),
            ),
        )

        variables = [
            sedml_data_model.Variable(
                id='Time',
                symbol=sedml_data_model.Symbol.time,
                task=task),
            sedml_data_model.Variable(
                id='G0',
                target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='G0']/@level",
                target_namespaces=self.NAMESPACES,
                task=task),
            sedml_data_model.Variable(
                id='G1',
                target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='G1']/@level",
                target_namespaces=self.NAMESPACES,
                task=task),
        ]

        # synchronous method
        task.simulation.algorithm.kisao_id = 'KISAO_0000449'
        variable_results, _ = core.exec_sed_task(task, variables)
        self.assertEqual(set(variable_results.keys()), set(['Time', 'G0', 'G1']))
        for variable_result in variable_results.values():
            self.assertFalse(numpy.any(numpy.isnan(variable_result)))
        numpy.testing.assert_allclose(variable_results['Time'], numpy.linspace(10, 15, 6))

        # asynchronous method
        task.simulation.algorithm.kisao_id = 'KISAO_0000450'
        task.simulation.algorithm.changes.append(sedml_data_model.AlgorithmParameterChange(
            kisao_id='KISAO_0000574',
            new_value=json.dumps({'G0': 0.2, 'G1': 0.3, 'G2': 0.5}),
        ))
        variable_results, _ = core.exec_sed_task(task, variables)
        self.assertEqual(set(variable_results.keys()), set(['Time', 'G0', 'G1']))
        for variable_result in variable_results.values():
            self.assertFalse(numpy.any(numpy.isnan(variable_result)))
        numpy.testing.assert_allclose(variable_results['Time'], numpy.linspace(10, 15, 6))

        # probabilstic method
        task.simulation.algorithm.kisao_id = 'KISAO_0000573'
        task.simulation.algorithm.changes.pop()
        variable_results, _ = core.exec_sed_task(task, variables)
        self.assertEqual(set(variable_results.keys()), set(['Time', 'G0', 'G1']))
        for variable_result in variable_results.values():
            self.assertFalse(numpy.any(numpy.isnan(variable_result)))
        numpy.testing.assert_allclose(variable_results['Time'], numpy.linspace(10, 15, 6))

        # error handling: invalid algorithm
        task.simulation.algorithm.kisao_id = 'KISAO_0000001'
        with self.assertRaises(NotImplementedError):
            core.exec_sed_task(task, variables)

    def test_exec_sedml_docs_in_combine_archive_successfully(self):
        doc, archive_filename = self._build_combine_archive()

        out_dir = os.path.join(self.dirname, 'out')
        core.exec_sedml_docs_in_combine_archive(archive_filename, out_dir,
                                                report_formats=[
                                                    report_data_model.ReportFormat.h5,
                                                ],
                                                bundle_outputs=True,
                                                keep_individual_outputs=True)

        self._assert_combine_archive_outputs(doc, out_dir)

    def _build_combine_archive(self, algorithm=None):
        doc = self._build_sed_doc(algorithm=algorithm)

        archive_dirname = os.path.join(self.dirname, 'archive')
        if not os.path.isdir(archive_dirname):
            os.mkdir(archive_dirname)

        model_filename = os.path.join(archive_dirname, 'model_1.xml')
        shutil.copyfile(self.EXAMPLE_MODEL_FILENAME, model_filename)

        sim_filename = os.path.join(archive_dirname, 'sim_1.sedml')
        SedmlSimulationWriter().run(doc, sim_filename)

        updated = datetime.datetime(2020, 1, 2, 1, 2, 3, tzinfo=dateutil.tz.tzutc())
        archive = combine_data_model.CombineArchive(
            contents=[
                combine_data_model.CombineArchiveContent(
                    'model_1.xml', combine_data_model.CombineArchiveContentFormat.SBML.value, updated=updated),
                combine_data_model.CombineArchiveContent(
                    'sim_1.sedml', combine_data_model.CombineArchiveContentFormat.SED_ML.value, updated=updated),
            ],
            updated=updated,
        )
        archive_filename = os.path.join(self.dirname, 'archive.omex')
        CombineArchiveWriter().run(archive, archive_dirname, archive_filename)

        return (doc, archive_filename)

    def _build_sed_doc(self, algorithm=None):
        if algorithm is None:
            algorithm = sedml_data_model.Algorithm(
                kisao_id='KISAO_0000449',
                changes=[
                    sedml_data_model.AlgorithmParameterChange(
                        kisao_id='KISAO_0000572',
                        new_value='0.0',
                    ),
                ],
            )

        doc = sedml_data_model.SedDocument()
        doc.models.append(sedml_data_model.Model(
            id='model_1',
            source='model_1.xml',
            language=sedml_data_model.ModelLanguage.SBML.value,
        ))
        doc.simulations.append(sedml_data_model.UniformTimeCourseSimulation(
            id='sim_1_time_course',
            initial_time=0,
            output_start_time=0,
            output_end_time=10,
            number_of_points=10,
            algorithm=algorithm,
        ))
        doc.tasks.append(sedml_data_model.Task(
            id='task_1',
            model=doc.models[0],
            simulation=doc.simulations[0],
        ))

        doc.data_generators.append(sedml_data_model.DataGenerator(
            id='data_gen_time',
            variables=[
                sedml_data_model.Variable(
                    id='var_time',
                    symbol=sedml_data_model.Symbol.time,
                    task=doc.tasks[0],
                ),
            ],
            math='var_time',
        ))
        doc.data_generators.append(sedml_data_model.DataGenerator(
            id='data_gen_G1',
            variables=[
                sedml_data_model.Variable(
                    id='var_G1',
                    target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='G1']",
                    target_namespaces=self.NAMESPACES,
                    task=doc.tasks[0],
                ),
            ],
            math='var_G1',
        ))
        doc.data_generators.append(sedml_data_model.DataGenerator(
            id='data_gen_G2',
            variables=[
                sedml_data_model.Variable(
                    id='var_G2',
                    target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='G2']/@level",
                    target_namespaces=self.NAMESPACES,
                    task=doc.tasks[0],
                ),
            ],
            math='var_G2',
        ))

        doc.outputs.append(sedml_data_model.Report(
            id='report_1',
            data_sets=[
                sedml_data_model.DataSet(id='data_set_time', label='Time', data_generator=doc.data_generators[0]),
                sedml_data_model.DataSet(id='data_set_G1', label='G1', data_generator=doc.data_generators[1]),
                sedml_data_model.DataSet(id='data_set_G2', label='G2', data_generator=doc.data_generators[2]),
            ],
        ))

        append_all_nested_children_to_doc(doc)

        return doc

    def _assert_combine_archive_outputs(self, doc, out_dir):
        self.assertEqual(set(['reports.h5']).difference(set(os.listdir(out_dir))), set())

        report = ReportReader().run(doc.outputs[0], out_dir, 'sim_1.sedml/report_1', format=report_data_model.ReportFormat.h5)

        self.assertEqual(sorted(report.keys()), sorted([d.id for d in doc.outputs[0].data_sets]))

        sim = doc.tasks[0].simulation
        self.assertEqual(len(report[doc.outputs[0].data_sets[0].id]), sim.number_of_points + 1)

        for data_set_result in report.values():
            self.assertFalse(numpy.any(numpy.isnan(data_set_result)))

        numpy.testing.assert_allclose(report[doc.outputs[0].data_sets[0].id],
                                      numpy.linspace(sim.output_start_time, sim.output_end_time, sim.number_of_points + 1))

    def test_exec_sedml_docs_in_combine_archive_with_all_algorithms(self):
        for alg in gen_algorithms_from_specs(self.SPECIFICATIONS_FILENAME).values():
            doc, archive_filename = self._build_combine_archive(algorithm=alg)
            out_dir = os.path.join(self.dirname, alg.kisao_id)
            core.exec_sedml_docs_in_combine_archive(archive_filename, out_dir,
                                                    report_formats=[
                                                        report_data_model.ReportFormat.h5,
                                                    ],
                                                    bundle_outputs=True,
                                                    keep_individual_outputs=True)

            self._assert_combine_archive_outputs(doc, out_dir)

    def test_raw_cli(self):
        with mock.patch('sys.argv', ['', '--help']):
            with self.assertRaises(SystemExit) as context:
                __main__.main()
                self.assertRegex(context.Exception, 'usage: ')

    def test_exec_sedml_docs_in_combine_archive_with_cli(self):
        doc, archive_filename = self._build_combine_archive()
        out_dir = os.path.join(self.dirname, 'out')
        env = self._get_combine_archive_exec_env()

        with mock.patch.dict(os.environ, env):
            with __main__.App(argv=['-i', archive_filename, '-o', out_dir]) as app:
                app.run()

        self._assert_combine_archive_outputs(doc, out_dir)

    def _get_combine_archive_exec_env(self):
        return {
            'REPORT_FORMATS': 'h5'
        }

    def test_exec_sedml_docs_in_combine_archive_with_docker_image(self):
        doc, archive_filename = self._build_combine_archive()
        out_dir = os.path.join(self.dirname, 'out')
        docker_image = self.DOCKER_IMAGE
        env = self._get_combine_archive_exec_env()

        exec_sedml_docs_in_archive_with_containerized_simulator(
            archive_filename, out_dir, docker_image, environment=env, pull_docker_image=False)

        self._assert_combine_archive_outputs(doc, out_dir)
