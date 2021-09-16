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
from biosimulators_utils.config import get_config
from biosimulators_utils.report import data_model as report_data_model
from biosimulators_utils.report.io import ReportReader
from biosimulators_utils.simulator.exec import exec_sedml_docs_in_archive_with_containerized_simulator
from biosimulators_utils.simulator.specs import gen_algorithms_from_specs
from biosimulators_utils.sedml import data_model as sedml_data_model
from biosimulators_utils.sedml.io import SedmlSimulationWriter
from biosimulators_utils.sedml.utils import append_all_nested_children_to_doc
from biosimulators_utils.warnings import BioSimulatorsWarning
from kisao.exceptions import AlgorithmCannotBeSubstitutedException
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
import yaml


class CliTestCase(unittest.TestCase):
    EXAMPLE_MODEL_FILENAME = os.path.join(os.path.dirname(__file__), 'fixtures', 'example-model.xml')
    SPECIFICATIONS_FILENAME = os.path.join(os.path.dirname(__file__), '..', 'biosimulators.json')
    DOCKER_IMAGE = 'ghcr.io/biosimulators/biosimulators_boolnet/boolnet:latest'
    NAMESPACES = {
        None: 'http://sed-ml.org/sed-ml/level1/version3',
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
        variable_results, log = core.exec_sed_task(task, variables)
        self.assertEqual(set(variable_results.keys()), set(['Time', 'G0', 'G1']))
        for variable_result in variable_results.values():
            self.assertFalse(numpy.any(numpy.isnan(variable_result)))
        numpy.testing.assert_allclose(variable_results['Time'], numpy.linspace(10, 15, 6))

        # check that log can be serialized to JSON
        json.dumps(log.to_json())

        log.out_dir = self.dirname
        log.export()
        with open(os.path.join(self.dirname, get_config().LOG_PATH), 'rb') as file:
            log_data = yaml.load(file, Loader=yaml.Loader)
        json.dumps(log_data)

        # error handling: invalid algorithm
        task.simulation.algorithm.kisao_id = 'KISAO_0000019'
        with self.assertRaises(AlgorithmCannotBeSubstitutedException):
            core.exec_sed_task(task, variables)

        task.simulation.algorithm.kisao_id = 'KISAO_0000449'
        task.simulation.algorithm.changes = [
            sedml_data_model.AlgorithmParameterChange(
                kisao_id='KISAO_0000572',
                new_value='not a number',
            ),
        ]
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            with self.assertRaisesRegex(ValueError, 'is not a valid'):
                core.exec_sed_task(task, variables)

        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'SIMILAR_VARIABLES'}):
            with self.assertWarnsRegex(BioSimulatorsWarning, 'Unsuported value'):
                core.exec_sed_task(task, variables)

        task.simulation.algorithm.changes[0].kisao_id = 'KISAO_0000531'
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
                core.exec_sed_task(task, variables)

        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'SIMILAR_VARIABLES'}):
            with self.assertWarnsRegex(BioSimulatorsWarning, 'Unsuported algorithm parameter'):
                core.exec_sed_task(task, variables)

    def test_exec_sed_task_with_model_changes(self):
        task = sedml_data_model.Task(
            model=sedml_data_model.Model(
                source=os.path.join(os.path.dirname(__file__), 'fixtures', 'irons.xml'),
                language=sedml_data_model.ModelLanguage.SBML.value,
            ),
            simulation=sedml_data_model.UniformTimeCourseSimulation(
                initial_time=0,
                output_start_time=0,
                output_end_time=100,
                number_of_points=100,
                algorithm=sedml_data_model.Algorithm(
                    kisao_id='KISAO_0000449',
                ),
            ),
        )
        model = task.model
        sim = task.simulation

        variable_ids = [
            'Cln3', 'SMBF', 'Cln2', 'Clb5', 'Yhp1', 'Clb2', 'SFF', 'Cdc20', 'FEAR',
            'MEN', 'Cdc14', 'Swi5', 'CKI', 'Cdh1', 'S', 'B', 'M', 'CD',
        ]

        variables = []
        for variable_id in variable_ids:
            variables.append(sedml_data_model.Variable(
                id=variable_id,
                target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='{}']/@level".format(
                    variable_id),
                target_namespaces=self.NAMESPACES,
                task=task,
            ))

        preprocessed_task = core.preprocess_sed_task(task, variables)

        model.changes = []
        results, _ = core.exec_sed_task(task, variables, preprocessed_task=preprocessed_task)

        model.changes = [
            sedml_data_model.ModelAttributeChange(
                target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='Cln2']/@qual:initialLevel",
                target_namespaces=self.NAMESPACES,
                new_value=0,
            ),
            sedml_data_model.RemoveElementModelChange(
                target="/sbml:sbml/sbml:model/qual:listOfTransitions/qual:transition[@qual:id='tr_Cln2']",
                target_namespaces=self.NAMESPACES,
            ),
        ]
        preprocessed_task = core.preprocess_sed_task(task, variables)
        results2, _ = core.exec_sed_task(task, variables, preprocessed_task=preprocessed_task)

        model.changes = [
            sedml_data_model.ModelAttributeChange(
                target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='Cln3']/@qual:initialLevel",
                target_namespaces=self.NAMESPACES,
                new_value=0,
            ),
            sedml_data_model.RemoveElementModelChange(
                target="/sbml:sbml/sbml:model/qual:listOfTransitions/qual:transition[@qual:id='tr_Cln3']",
                target_namespaces=self.NAMESPACES,
            ),
        ]
        preprocessed_task = core.preprocess_sed_task(task, variables)
        results3, _ = core.exec_sed_task(task, variables, preprocessed_task=preprocessed_task)

        end_results = {}
        end_results_2 = {}
        end_results_3 = {}
        end_results_minus_1 = {}
        end_results_minus_1_2 = {}
        end_results_minus_1_3 = {}
        for variable_id in variable_ids:
            end_results[variable_id] = results[variable_id][-1].tolist()
            end_results_2[variable_id] = results2[variable_id][-1].tolist()
            end_results_3[variable_id] = results3[variable_id][-1].tolist()

            end_results_minus_1[variable_id] = results[variable_id][-2].tolist()
            end_results_minus_1_2[variable_id] = results2[variable_id][-2].tolist()
            end_results_minus_1_3[variable_id] = results3[variable_id][-2].tolist()

        self.assertNotEqual(end_results_minus_1, end_results)
        self.assertNotEqual(end_results_minus_1_2, end_results_2)
        self.assertEqual(end_results_minus_1_3, end_results_3)

    # Fails because BoolNet doesn't capture initial conditions
    @unittest.expectedFailure
    def test_exec_sed_task_multistep_simulation_using_model_changes(self):
        task = sedml_data_model.Task(
            model=sedml_data_model.Model(
                source=os.path.join(os.path.dirname(__file__), 'fixtures', 'BIOMD0000000562_url.xml'),
                language=sedml_data_model.ModelLanguage.SBML.value,
            ),
            simulation=sedml_data_model.UniformTimeCourseSimulation(
                initial_time=0,
                output_start_time=0,
                output_end_time=10,
                number_of_points=10,
                algorithm=sedml_data_model.Algorithm(
                    kisao_id='KISAO_0000450',
                ),
            ),
        )
        model = task.model
        sim = task.simulation

        variable_ids = [
            'erk', 'ikk', 'gsk3', 'nfkb', 'ask1', 'ras', 'egf', 'egfr', 'traf2', 'ikb', 'map3k1', 'tnfr',
            'ap1', 'mek', 'mkk4', 'ex', 'tnfa', 'raf1', 'map3k7', 'mkk7', 'cjun', 'sos', 'jnk', 'pi3k',
            'p38', 'akt', 'ph', 'nik'
        ]

        variables = []
        for variable_id in variable_ids:
            model.changes.append(sedml_data_model.ModelAttributeChange(
                target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='{}']/@initialLevel".format(
                    variable_id),
                target_namespaces=self.NAMESPACES,
                new_value=None,
            ))
            variables.append(sedml_data_model.Variable(
                id=variable_id,
                target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='{}']/@level".format(
                    variable_id),
                target_namespaces=self.NAMESPACES,
                task=task,
            ))

        preprocessed_task = core.preprocess_sed_task(task, variables)

        model.changes = []
        results, _ = core.exec_sed_task(task, variables, preprocessed_task=preprocessed_task)
        self.assertEqual(
            results['nik'][0:int(sim.number_of_points / 2 + 1)].shape,
            results['nik'][-int(sim.number_of_points / 2 + 1):].shape,
        )
        with self.assertRaises(AssertionError):
            numpy.testing.assert_allclose(
                results['nik'][0:int(sim.number_of_points / 2 + 1)],
                results['nik'][-int(sim.number_of_points / 2 + 1):],
            )

        sim.output_end_time = sim.output_end_time / 2
        sim.number_of_points = int(sim.number_of_points / 2)
        preprocessed_task = core.preprocess_sed_task(task, variables)
        results2, _ = core.exec_sed_task(task, variables, preprocessed_task=preprocessed_task)
        numpy.testing.assert_allclose(
            results2['nik'],
            results['nik'][0:sim.number_of_points + 1],
        )

        for variable_id in variable_ids:
            model.changes.append(sedml_data_model.ModelAttributeChange(
                target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='{}']/@initialLevel".format(
                    variable_id),
                target_namespaces=self.NAMESPACES,
                new_value=results2[variable_id][-1],
            ))

        results3, _ = core.exec_sed_task(task, variables, preprocessed_task=preprocessed_task)
        numpy.testing.assert_allclose(
            results3['nik'],
            results['nik'][-(sim.number_of_points + 1):],
        )

    def test_exec_sedml_docs_in_combine_archive_successfully(self):
        doc, archive_filename = self._build_combine_archive()

        out_dir = os.path.join(self.dirname, 'out')

        config = get_config()
        config.REPORT_FORMATS = [report_data_model.ReportFormat.h5]
        config.BUNDLE_OUTPUTS = True
        config.KEEP_INDIVIDUAL_OUTPUTS = True

        _, log = core.exec_sedml_docs_in_combine_archive(archive_filename, out_dir, config=config)
        if log.exception:
            raise log.exception

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

        archive = combine_data_model.CombineArchive(
            contents=[
                combine_data_model.CombineArchiveContent(
                    'model_1.xml', combine_data_model.CombineArchiveContentFormat.SBML.value),
                combine_data_model.CombineArchiveContent(
                    'sim_1.sedml', combine_data_model.CombineArchiveContentFormat.SED_ML.value),
            ],
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

            config = get_config()
            config.REPORT_FORMATS = [report_data_model.ReportFormat.h5]
            config.BUNDLE_OUTPUTS = True
            config.KEEP_INDIVIDUAL_OUTPUTS = True

            _, log = core.exec_sedml_docs_in_combine_archive(archive_filename, out_dir, config=config)
            if log.exception:
                raise log.exception

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
