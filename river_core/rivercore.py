# See LICENSE file for details
""" Main file containing all functions of river_core """
import sys
import os
import glob
import shutil
import datetime
import importlib
import configparser
import filecmp
import json

from river_core.log import *
import river_core.utils as utils
from river_core.constants import *
from river_core.__init__ import __version__
from river_core.sim_hookspecs import *
from envyaml import EnvYAML
from jinja2 import Template

from cerberus import Validator
from ruamel.yaml import YAML
yaml = YAML(typ="rt")
yaml.default_flow_style = False
yaml.allow_unicode = True
yaml.compact(seq_seq=False, seq_map=False)


# Misc Helper Functions
def sanitise_pytest_json(json):
    '''
        Function to sanitise pytest JSONs, removes uncessary logs. 

        :param json: JSON to sanitise 

        :type json: list  

        :return: A list of important json_data 

        :rtype: dict
    '''
    return_data = []
    for json_row in json:
        # NOTE: Playing with fire here, pytest developers could (potentially) change this
        if json_row.get('$report_type', None) == 'TestReport':
            return_data.append(json_row)

    return return_data


def generate_coverage_report(output_dir, config, coverage_report,
                             coverage_rank_report, db_files):
    '''
        Function to generate coverage reports after merging databases. 

        :param json: JSON to sanitise 

        :param config: RiverCore config.ini object 

        :param coverage_report: Final HTML report containing coverage info 

        :param coverage_rank_report: Final Rank HTML report containing containing ranked cverage info 


        :param db_files: List of db_files that are merged 

        :type json: list  

        :type config: configparser.SectionProxy 

        :type coverage_report: str 

        :type coverage_rank_report: str 

        :type db_files: list 

        :return: Final HTML path

        :rtype: str 
    '''
    root = os.path.abspath(os.path.dirname(__file__))
    str_report_template = root + '/templates/coverage_report.html'
    str_css_template = root + '/templates/style.css'
    report_file_name = 'coverage_report.html'
    report_dir = output_dir + '/reports/'
    html_objects = {}
    html_objects['name'] = "RiVer Core Coverage Report"
    html_objects['date'] = (datetime.datetime.now().strftime("%d-%m-%Y"))
    html_objects['time'] = (datetime.datetime.now().strftime("%H:%M"))
    html_objects['version'] = __version__
    html_objects['isa'] = config['river_core']['isa']
    html_objects['dut'] = config['river_core']['target']
    html_objects['generator'] = config['river_core']['generator']
    html_objects['coverage_report'] = coverage_report
    html_objects['coverage_rank_report'] = coverage_rank_report
    html_objects['db_files'] = db_files

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(str_report_template, "r") as report_template:
        template = Template(report_template.read())

    output = template.render(html_objects)

    shutil.copyfile(str_css_template, output_dir + '/style.css')

    report_file_path = output_dir + '/' + report_file_name
    with open(report_file_path, "w") as report:
        report.write(output)

    logger.info('Final coverage report saved at {0}!'.format(report_file_path))

    return report_file_path


def generate_report(output_dir, gen_json_data, target_json_data, ref_json_data,
                    config, test_dict):
    '''
        Function to create an HTML report from the JSON files generated by individual plugins

        :param output_dir: Output directory for programs generated

        :param gen_json_data: JSON data from Generator Plugin 

        :param target_json_data: JSON data from Target Plugin 

        :param ref_json_data: JSON data from Reference Plugin 

        :param config: Config ini with the loaded by the configparser module

        :param test_dict: Test List YAML 

        :type output_dir: str

        :type gen_json_data: dict 

        :type target_json_data: dict 

        :type ref_json_data: dict 

        :type config: configparser.SectionProxy 

        :type test_list: dict 

        :return: Final HTML path

        :rtype: str 
    '''

    # Filter JSON files
    if gen_json_data:
        gen_json_data = sanitise_pytest_json(gen_json_data)
    if target_json_data:
        target_json_data = sanitise_pytest_json(target_json_data)
    if ref_json_data:
        ref_json_data = sanitise_pytest_json(ref_json_data)

    ## Get the proper stats about passed and failed test
    # NOTE: This is the place where you determine when your test passed fail, just add extra things to compare in the if condition if the results become to high
    num_passed = num_total = num_unav = num_failed = 0
    for test in test_dict:
        num_total = num_total + 1
        try:
            if test_dict[test]['result'] == 'Unavailable':
                num_unav = num_unav + 1
                continue
            elif test_dict[test]['result'] == 'Passed':
                num_passed = num_passed + 1
            else:
                num_failed = num_failed + 1
        except:
            logger.warning("Couldn't get a result from the Test List Dict")

    root = os.path.abspath(os.path.dirname(__file__))
    str_report_template = root + '/templates/report.html'
    str_css_template = root + '/templates/style.css'
    report_file_name = 'report.html'
    report_dir = output_dir + '/reports/'
    html_objects = {}
    html_objects['name'] = "RiVer Core Verification Report"
    html_objects['date'] = (datetime.datetime.now().strftime("%d-%m-%Y"))
    html_objects['time'] = (datetime.datetime.now().strftime("%H:%M"))
    html_objects['version'] = __version__
    html_objects['isa'] = config['river_core']['isa']
    html_objects['dut'] = config['river_core']['target']
    html_objects['generator'] = config['river_core']['generator']
    html_objects['reference'] = config['river_core']['reference']
    html_objects['test_dict'] = test_dict
    html_objects['target_data'] = target_json_data
    html_objects['ref_data'] = ref_json_data
    html_objects['gen_data'] = gen_json_data
    html_objects['num_passed'] = num_passed
    html_objects['num_failed'] = num_failed
    html_objects['num_unav'] = num_unav

    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    with open(str_report_template, "r") as report_template:
        template = Template(report_template.read())

    output = template.render(html_objects)

    shutil.copyfile(str_css_template, report_dir + 'style.css')

    report_file_path = report_dir + '/' + report_file_name
    with open(report_file_path, "w") as report:
        report.write(output)

    logger.info('Final report saved at {0}'.format(report_file_path))

    return report_file_path


def confirm():
    """
    Ask user to enter Y or N (case-insensitive).

    :return: True if the answer is Y.
    :rtype: bool
    """
    answer = ""
    while answer not in ["y", "n"]:
        answer = input("Type [Y/N] to continue execution ? ").lower()
    return answer == "y"


def rivercore_clean(config_file, verbosity):
    '''
        Helper function to clear the work_dir 

        :param config_file: Config file for the river_core.ini 

        :param verbosity: Verbosity Level for the logger 

        :type config_file: click.Path 

        :type verbosity: str 

    '''

    config = configparser.ConfigParser()
    config.read(config_file)
    output_dir = config['river_core']['work_dir']
    logger.level(verbosity)
    logger.info('****** RiVer Core {0} *******'.format(__version__))
    logger.info('****** Cleaning Mode ****** ')
    logger.info('Copyright (c) 2021, InCore Semiconductors Pvt. Ltd.')
    logger.info('All Rights Reserved.')

    suite = config['river_core']['generator']
    target = config['river_core']['target']
    ref = config['river_core']['reference']

    if not os.path.exists(output_dir):
        logger.info(output_dir + ' directory does not exist. Nothing to delete')
        return
    else:
        logger.info('The following directory will be removed : ' +
                    str(output_dir))
        logger.info('Hope you took a backup of the reports')
        res = confirm()
        if res:
            shutil.rmtree(output_dir)
            logger.info(output_dir + ' directory deleted')


def rivercore_generate(config_file, verbosity):
    '''
        Function to generate the assembly programs using the plugin as configured in the config.ini.

        :param config_file: Config.ini file for generation

        :param verbosity: Verbosity level for the framework

        :type config_file: click.Path

        :type verbosity: str
    '''

    logger.level(verbosity)
    config = configparser.ConfigParser()
    config.read(config_file)
    logger.debug('Read file from {0}'.format(config_file))

    output_dir = config['river_core']['work_dir']

    logger.info('****** Generation Mode ****** ')

    # TODO Test multiple plugin cases
    # Current implementation is using for loop, which might be a bad idea for parallel processing.

    suite_list = config['river_core']['generator'].replace(' ', '').split(',')

    logger.info(
        "The river_core is currently configured to run with following parameters"
    )
    logger.info("The Output Directory (work_dir) : {0}".format(output_dir))
    logger.info("ISA : {0}".format(config['river_core']['isa']))
    test_list = {}

    for suite in suite_list:

        # Give Plugin Info
        logger.info("Plugin Jobs : {0}".format(config[suite]['jobs']))
        logger.info("Plugin Seed : {0}".format(config[suite]['seed']))
        logger.info("Plugin Count (Times to run the test) : {0}".format(
            config[suite]['count']))
        generatorpm = pluggy.PluginManager("generator")
        generatorpm.add_hookspecs(RandomGeneratorSpec)

        path_to_module = config['river_core']['path_to_suite']
        plugin_suite = suite + '_plugin'

        # Get ISA and pass to plugin
        isa = config['river_core']['isa']
        config[suite]['isa'] = isa
        logger.info('Now loading {0} Suite'.format(suite))
        abs_location_module = path_to_module + '/' + plugin_suite + '/' + plugin_suite + '.py'
        logger.debug("Loading module from {0}".format(abs_location_module))
        try:
            generatorpm_spec = importlib.util.spec_from_file_location(
                plugin_suite, abs_location_module)
            generatorpm_module = importlib.util.module_from_spec(
                generatorpm_spec)
            generatorpm_spec.loader.exec_module(generatorpm_module)
            plugin_class = "{0}_plugin".format(suite)
            class_to_call = getattr(generatorpm_module, plugin_class)
            # TODO:DOC: Naming for class in plugin
            generatorpm.register(class_to_call())

        except FileNotFoundError as txt:
            logger.error(suite + " not found at : " + path_to_module + ".\n" +
                         str(txt))
            raise SystemExit

        generatorpm.hook.pre_gen(spec_config=config[suite],
                                 output_dir='{0}/{1}'.format(output_dir, suite))
        test_list.update(
            generatorpm.hook.gen(module_dir=path_to_module,
                                 output_dir=output_dir)[0])
        if not isinstance(test_list, dict):
            logger.error(
                'Test List returned by the gen hook of Generator is of type: ' +
                str(type(test_list)) + '. Expected Dict')
            raise SystemExit

        generatorpm.hook.post_gen(
            output_dir='{0}/{1}'.format(output_dir, suite))

    test_list_file = output_dir + '/test_list.yaml'
    logger.info('Dumping generated Test-List at: ' + str(test_list_file))
    testfile = open(test_list_file, 'w')
    utils.yaml.dump(test_list, testfile)
    testfile.close()

    logger.info('Validating Generated Test-List')
    testschema = yaml.load(testlist_schema)
    validator = YamlValidator(testschema)
    validator.allow_unknown = False
    for test, fields in test_list.items():
        valid = validator.validate(fields)
        if not valid:
            logger.error('Test List Validation failed:')
            error_list = validator.errors
            for x in error_list:
                logger.error('{0} [ {1} ] : {2}'.format(test, x, error_list[x]))
            raise SystemExit
    logger.info('Test List Validated successfully')

    # Open generation report in browser
    for suite in suite_list:
        report_html = str(output_dir) + '/reports/{0}.html'.format(suite)
        if utils.str_2_bool(config['river_core']['open_browser']):
            try:
                import webbrowser
                logger.info(
                    "Openning test report for {0} in web-browser".format(suite))
                webbrowser.open(report_html)
            except:
                return 1


def rivercore_compile(config_file, test_list, coverage, verbosity, dut_flags,
                      ref_flags, compare):
    '''

        Function to compile generated assembly programs using the plugin as configured in the config.ini.

        :param config_file: Config.ini file for generation

        :param test_list: Test List exported from generate sub-command 

        :param coverage: Enable coverage merge and stats from the reports 

        :param verbosity: Verbosity level for the framework

        :param dut_flags: Verbosity level for the framework

        :param ref_flags: Verbosity level for the framework

        :param compare: Verbosity level for the framework

        :type config_file: click.Path

        :type test_list: click.Path

        :type coverage: bool 

        :type verbosity: str

        :type dut_flags: click.Choice 

        :type ref_flags: click.Choice 

        :type compare: bool 
    '''
    logger.level(verbosity)
    config = configparser.ConfigParser()
    config.read(config_file)
    logger.debug('Read file from {0}'.format(config_file))

    logger.info('****** Compilation Mode ******')

    output_dir = config['river_core']['work_dir']
    asm_gen = config['river_core']['generator']
    target_list = config['river_core']['target'].split(',')
    ref_list = config['river_core']['reference'].split(',')

    logger.info(
        "The river_core is currently configured to run with following parameters"
    )
    logger.info("The Output Directory (work_dir) : {0}".format(output_dir))
    logger.info("ISA : {0}".format(config['river_core']['isa']))
    logger.info("Generator Plugin : {0}".format(asm_gen))
    logger.info("Target Plugin : {0}".format(target_list))
    logger.info("Reference Plugin : {0}".format(ref_list))

    # Set default values:
    target_json = None
    ref_json = None
    # Load coverage stats
    if coverage:
        logger.info("Coverage mode is enabled")
        coverage_config = config['coverage']
    else:
        coverage_config = None
    if '' in target_list:
        logger.info('No targets configured, so moving on the reference')
    else:
        for target in target_list:
            if dut_flags:
                logger.info("DuT Info")
                logger.info("DuT Jobs : {0}".format(config[target]['jobs']))
                logger.info("DuT Count (Times to run) : {0}".format(
                    config[target]['count']))

                dutpm = pluggy.PluginManager('dut')
                dutpm.add_hookspecs(DuTSpec)

                isa = config['river_core']['isa']
                config[target]['isa'] = isa
                path_to_module = config['river_core']['path_to_target']
                plugin_target = target + '_plugin'
                logger.info('Now running on the Target Plugins')
                logger.info('Now loading {0}-target'.format(target))

                abs_location_module = path_to_module + '/' + plugin_target + '/' + plugin_target + '.py'

                try:
                    logger.debug(
                        "Loading module from {0}".format(abs_location_module))
                    dutpm_spec = importlib.util.spec_from_file_location(
                        plugin_target, abs_location_module)
                    dutpm_module = importlib.util.module_from_spec(dutpm_spec)
                    dutpm_spec.loader.exec_module(dutpm_module)

                    # DuT Plugins
                    # TODO:DOC: Naming for class in plugin
                    plugin_class = "{0}_plugin".format(target)
                    class_to_call = getattr(dutpm_module, plugin_class)
                    dutpm.register(class_to_call())
                except:
                    logger.error(
                        "Sorry, loading the requested plugin has failed, please check the configuration"
                    )
                    logger.debug(
                        'Hello, it seems you are debugging, this usually indicates that the loading failed.\nCheck whether Python file being loaded is fine i.e. no errors and warnings. etc'
                    )
                    raise SystemExit
            if dut_flags == 'init':
                logger.debug('Single mode flag detected\nRunning init')
                dutpm.hook.init(ini_config=config[target],
                                test_list=test_list,
                                work_dir=output_dir,
                                coverage_config=coverage_config,
                                plugin_path=path_to_module)
            elif dut_flags == 'build':
                logger.debug('Single mode flag detected\nRunning build')
                dutpm.hook.init(ini_config=config[target],
                                test_list=test_list,
                                work_dir=output_dir,
                                coverage_config=coverage_config,
                                plugin_path=path_to_module)
                dutpm.hook.build()
            elif dut_flags == 'run':
                logger.debug('All modes enabled\nRunning run')
                dutpm.hook.init(ini_config=config[target],
                                test_list=test_list,
                                work_dir=output_dir,
                                coverage_config=coverage_config,
                                plugin_path=path_to_module)
                dutpm.hook.build()
                target_json = dutpm.hook.run(module_dir=path_to_module)
            else:
                logger.warning('DuT plugin disabled')

    if '' in ref_list:
        logger.info('No references, so exiting the framework')
        raise SystemExit
    else:
        for ref in ref_list:
            if ref_flags:
                logger.info("Reference Info")
                logger.info("Reference Jobs : {0}".format(config[ref]['jobs']))
                logger.info(
                    "Reference Count (Times to run the test) : {0}".format(
                        config[ref]['count']))
                refpm = pluggy.PluginManager('dut')
                refpm.add_hookspecs(DuTSpec)

                path_to_module = config['river_core']['path_to_ref']
                plugin_ref = ref + '_plugin'
                logger.info('Now loading {0}-target'.format(ref))
                # Get ISA from river
                isa = config['river_core']['isa']
                config[ref]['isa'] = isa

                abs_location_module = path_to_module + '/' + plugin_ref + '/' + plugin_ref + '.py'

                try:
                    logger.debug(
                        "Loading module from {0}".format(abs_location_module))
                    refpm_spec = importlib.util.spec_from_file_location(
                        plugin_ref, abs_location_module)
                    refpm_module = importlib.util.module_from_spec(refpm_spec)
                    refpm_spec.loader.exec_module(refpm_module)

                    # DuT Plugins
                    # TODO:DOC: Naming for class in plugin
                    plugin_class = "{0}_plugin".format(ref)
                    class_to_call = getattr(refpm_module, plugin_class)
                    refpm.register(class_to_call())
                except:
                    logger.error(
                        "Sorry, requested plugin not found at location, please check config.ini"
                    )
                    raise SystemExit

            if ref_flags == 'init':
                logger.debug('Single mode flag detected\nRunning init')
                refpm.hook.init(ini_config=config[ref],
                                test_list=test_list,
                                work_dir=output_dir,
                                coverage_config=coverage_config,
                                plugin_path=path_to_module)
            elif ref_flags == 'build':
                logger.debug('Single mode flag detected\nRunning build')
                refpm.hook.init(ini_config=config[ref],
                                test_list=test_list,
                                work_dir=output_dir,
                                coverage_config=coverage_config,
                                plugin_path=path_to_module)
                refpm.hook.build()
            elif ref_flags == 'run':
                logger.debug('All modes detected\nRunning build')
                refpm.hook.init(ini_config=config[ref],
                                test_list=test_list,
                                work_dir=output_dir,
                                coverage_config=coverage_config,
                                plugin_path=path_to_module)
                refpm.hook.build()
                ref_json = refpm.hook.run(module_dir=path_to_module)
            else:
                logger.warning('Ref Plugin disabled')

        ## Comparing Dumps
        if compare:
            result = 'Unavailable'
            test_dict = utils.load_yaml(test_list)
            gen_json_data = []
            target_json_data = []
            ref_json_data = []
            for test, attr in test_dict.items():
                test_wd = attr['work_dir']
                if not os.path.isfile(test_wd + '/dut.dump'):
                    logger.error(
                        'Dut dump for Test: {0} is missing'.format(test))
                    continue
                if not os.path.isfile(test_wd + '/ref.dump'):
                    logger.error(
                        'Ref dump for Test: {0} is missing'.format(test))
                    continue
                filecmp.clear_cache()
                result = filecmp.cmp(test_wd + '/dut.dump',
                                     test_wd + '/ref.dump')
                test_dict[test]['result'] = 'Passed' if result else 'Failed'
                utils.save_yaml(test_dict, test_list)
                if not result:
                    logger.error(
                        "Dumps for test {0}. Do not match. TEST FAILED".format(
                            test))
                else:
                    logger.info(
                        "Dumps for test {0} Match. TEST PASSED".format(test))

            # Start checking things after running the commands
            # Report generation starts here
            # Target
            # Move this into a function
            if target_json:
                json_file = open(target_json[0] + '.json', 'r')
                target_json_list = json_file.readlines()
                json_file.close()
                for line in target_json_list:
                    target_json_data.append(json.loads(line))
            else:
                logger.debug('Could not find a target_json file')
                for test, attr in test_dict.items():
                    test_dict[test]['result'] = 'Unavailable'
                    logger.debug(
                        'Resetting values in test_dict; Triggered by the lack of DuT values'
                    )
            if ref_json:
                json_file = open(ref_json[0] + '.json', 'r')
                ref_json_list = json_file.readlines()
                json_file.close()
                for line in ref_json_list:
                    ref_json_data.append(json.loads(line))
            else:
                logger.debug('Could not find a reference_json file')
                for test, attr in test_dict.items():
                    test_dict[test]['result'] = 'Unavailable'
                    logger.debug(
                        'Resetting values in test_dict; Triggered by the lack of Ref values'
                    )

            # Need to an Gen json file for final report
            # TODO:CHECK: Only issue is that this can ideally be a wrong approach

            try:
                logger.info(
                    "Checking for a generator json to create final report")
                json_files = glob.glob(output_dir + '/.json/{0}*.json'.format(
                    config['river_core']['generator']))
                logger.debug(
                    "Detected generated JSON Files: {0}".format(json_files))

                # Can only get one file back
                gen_json_file = max(json_files, key=os.path.getctime)
                json_file = open(gen_json_file, 'r')
                target_json_list = json_file.readlines()
                json_file.close()
                for line in target_json_list:
                    gen_json_data.append(json.loads(line))

            except:
                logger.warning("Couldn't find a generator JSON file")
                gen_json_data = []
                gen_json_file = []

            if (target_json and ref_json and gen_json_file):
                # See if space saver is enabled when we have all the data
                dutpm.hook.post_run(test_dict=test_dict, config=config)
                refpm.hook.post_run(test_dict=test_dict, config=config)

        else:
            logger.info(
                'Comparison was disabled\nHence no diff would be available')
            result = 'Unavailable'
            test_dict = utils.load_yaml(test_list)
            logger.debug('Resetting values in test_dict')
            for test, attr in test_dict.items():
                test_dict[test]['result'] = 'Unavailable'
            gen_json_data = []
            target_json_data = []
            ref_json_data = []

        logger.info("Now generating some good HTML reports for you")
        report_html = generate_report(output_dir, gen_json_data,
                                      target_json_data, ref_json_data, config,
                                      test_dict)

        # Check if web browser
        if utils.str_2_bool(config['river_core']['open_browser']):
            try:
                import webbrowser
                logger.info("Openning test report in web-browser")
                webbrowser.open(report_html)
            except:
                return 1


def rivercore_merge(verbosity, db_folders, output, config_file):
    '''
        Work in Progress

        Function to merge coverage databases

        :param verbosity: Verbosity level for the framework

        :param db_folders: Tuple containing list of testlists to merge 
        
        :param output: Final output database name 

        :param config_file: Config.ini file for generation

        :type verbosity: str

        :type db_folders: tuple 
        
        :type output: str 

        :type config_file: click.Path
    '''

    logger.level(verbosity)
    config = configparser.ConfigParser()
    config.read(config_file)
    logger.debug('Read file from {0}'.format(config_file))
    target = config['river_core']['target']

    logger.info('****** Merge Mode ******')

    output = os.path.abspath(output)
    if os.path.exists(output):
        logger.info('Previous directory with same name detected\nOverwrite?')
        res = confirm()
        if res:
            shutil.rmtree(output)
            logger.info(output + ' directory deleted')
        else:
            logger.info('Alright\nBailing out.')
            raise SystemExit
    os.makedirs(output)
    asm_dir = output + '/asm'
    common_dir = output + '/common'
    coverage_dir = output + '/final_coverage'
    report_dir = output + '/reports'
    # Create the ASM dir
    os.makedirs(asm_dir)
    # Create the Common dir
    os.makedirs(common_dir)
    # Create the Common dir
    os.makedirs(coverage_dir)
    # Create the Report dir
    os.makedirs(report_dir)
    # Create the final test_list dict
    test_list = {}
    # Coverage DB list
    coverage_database = []
    coverage_html = []
    coverage_ranked_html = []
    # Copy the files
    # TODO: Check this
    for db_folder in db_folders:
        file_path = os.path.abspath(db_folder)
        folder_yaml = utils.load_yaml(file_path + '/test_list.yaml')
        for test in folder_yaml.keys():
            test_list[test] = {}
            test_asm = asm_dir + '/' + test
            test_common = common_dir + '/' + test
            # Copy the ASM folder
            ret_val = os.system('cp -r -f {0} {1}'.format(
                folder_yaml[test]['work_dir'], test_asm))
            if ret_val != 0:
                logger.error('Failed to copy files\nFiles donot exist')
                raise SystemExit
            # Check if something common is there
            if folder_yaml[test].get('extra_compile'):
                for extra in range(0, len(folder_yaml[test]['extra_compile'])):
                    # Keep this seperate right now
                    shutil.copy(folder_yaml[test]['extra_compile'][extra],
                                common_dir)
                test_list[test]['extra_compile'] = glob.glob(common_dir + '/*')
            # Copying things from test_list
            test_list[test]['cc'] = folder_yaml[test]['cc']
            test_list[test]['cc_args'] = folder_yaml[test]['cc_args']
            test_list[test]['isa'] = folder_yaml[test]['isa']
            test_list[test]['linker_args'] = folder_yaml[test]['linker_args']
            test_list[test]['mabi'] = folder_yaml[test]['mabi']
            test_list[test]['march'] = folder_yaml[test]['march']
            test_list[test]['result'] = folder_yaml[test]['result']
            test_list[test]['asm_file'] = test_asm + '/' + test + '.S'
            test_list[test]['linker_file'] = test_asm + '/' + test + '.ld'
            test_list[test]['work_dir'] = test_asm

        logger.info('Copied ASM and other necessary files')

        # Check coverage info
        # The plugins should probably take care of this part, they'll get aresultess to the dbs_folder
        if 'cadence' in target:
            coverage_directory = file_path + '/reports/final_coverage'
        else:
            coverage_directory = file_path + '/final_coverage'
        if os.path.exists(coverage_directory):
            # Cadence
            if 'cadence' in target:
                coverage_database.append(
                    os.path.abspath(
                        glob.glob(file_path +
                                  '/reports/final_coverage/*.ucd')[0]))
                coverage_html.append(
                    os.path.abspath(
                        glob.glob(file_path +
                                  '/reports/final_coverage_html/*.html')[0]))
            # Questa
            elif 'questa' in target:
                coverage_database.append(
                    os.path.abspath(
                        glob.glob(file_path + '/final_coverage/*.ucdb')[0]))
                coverage_html.append(
                    os.path.abspath(
                        glob.glob(file_path + '/cov_html/*.html')[0]))
            # Verilator
            elif 'verilator' in target:
                coverage_database.append(
                    os.path.abspath(
                        glob.glob(file_path + '/final_coverage/*.dat')[0]))
        else:
            logger.warning('No DB files found in {0}'.format(file_path))

    dutpm = pluggy.PluginManager('dut')
    dutpm.add_hookspecs(DuTSpec)

    path_to_module = config['river_core']['path_to_target']
    plugin_target = target + '_plugin'
    logger.info('Now running on the Target Plugins')
    logger.info('Now loading {0}-target'.format(target))

    abs_location_module = path_to_module + '/' + plugin_target + '/' + plugin_target + '.py'
    logger.debug("Loading module from {0}".format(abs_location_module))

    try:
        dutpm_spec = importlib.util.spec_from_file_location(
            plugin_target, abs_location_module)
        dutpm_module = importlib.util.module_from_spec(dutpm_spec)
        dutpm_spec.loader.exec_module(dutpm_module)

        plugin_class = "{0}_plugin".format(target)
        class_to_call = getattr(dutpm_module, plugin_class)
        dutpm.register(class_to_call())
    except:
        logger.error(
            "Sorry, loading the requested plugin has failed, please check the configuration"
        )
        raise SystemExit

    # Perform Merge only if coverage enabled
    if (utils.str_2_bool(config['coverage']['code']) or
            utils.str_2_bool(config['coverage']['functional'])):
        final_html = dutpm.hook.merge_db(db_files=coverage_database,
                                         config=config,
                                         output_db=output)

    # Create final test list
    test_list_file = output + '/test_list.yaml'
    testfile = open(test_list_file, 'w')
    utils.yaml.dump(test_list, testfile)
    testfile.close()
    logger.info('Merged Test list is generated and available at {0}'.format(
        test_list_file))

    # Remove existing files
    logger.info('The following directories will be removed : ' +
                str(db_folders))
    logger.info('Hope you have took everything you want')
    res = confirm()
    if res:
        for db_file in db_folders:
            shutil.rmtree(db_file)
            logger.info(db_file + ' directory deleted')
    else:
        logger.info('Exiting framework.\nIndividual folders still exist')

    # Coverage Report Generations
    if (utils.str_2_bool(config['coverage']['code']) or
            utils.str_2_bool(config['coverage']['functional'])):
        report_html = generate_coverage_report(report_dir, config,
                                               final_html[0][0],
                                               final_html[0][1], coverage_html)

        try:
            import webbrowser
            logger.info("Opening test report in web-browser")
            webbrowser.open(report_html)
        except:
            logger.info("Couldn't open the browser")


def rivercore_setup(config, dut, gen, ref, verbosity):
    '''
        Function to generate sample plugins 

        :param config: Flag to create a sample config.ini 
        
        :param dut: Flag to create a sample DuT plugin

        :param gen: Flag to create a sample Generator Plugin

        :param ref: Flag to create a sample Reference Plugin

        :param verbosity: Verbosity level for the logger

        :type config bool:
        
        :type dut bool:

        :type gen bool:
 
        :type ref bool:

        :type verbosity str:

    '''

    logger.level(verbosity)
    cwd = os.getcwd()
    if config:

        logger.info('Creating sample config file: "river_core.ini"')
        with open('river_core.ini', 'w') as file:
            file.write(sample_config)
        logger.info('river_core.ini file created successfully')

    if gen:
        logger.info(
            "Creating sample Plugin directory for Generator with name:" +
            str(gen))
        root = os.path.abspath(os.path.dirname(__file__))
        src = os.path.join(root, "templates/setup/generator/")
        dest = os.path.join(cwd, gen)
        logger.debug('Copy files')
        shutil.copytree(src, dest)

        # Rename stuff
        logger.debug('Renaming files')
        os.rename(cwd + '/' + gen + '/sample_gen_config.yaml',
                  cwd + '/' + gen + '/' + gen + '_gen_config.yaml')
        os.rename(cwd + '/' + gen + '/sample_plugin.py',
                  cwd + '/' + gen + '/' + gen + '_plugin.py')

        # Plugin.py
        with open(cwd + '/' + gen + '/' + gen + '_plugin.py', 'r') as file:
            filedata = file.read()

        # Replace the target string
        logger.debug('Replacing names')
        filedata = filedata.replace('sample', gen.lower())

        # Write the file out again
        with open(cwd + '/' + gen + '/' + gen + '_plugin.py', 'w') as file:
            file.write(filedata)

        # conftest
        with open(cwd + '/' + gen + '/' + 'conftest.py', 'r') as file:
            filedata = file.read()

        # Replace the target string
        logger.debug('Replacing names')
        filedata = filedata.replace('sample', gen.lower())

        # Write the file out again
        with open(cwd + '/' + gen + '/' + 'conftest.py', 'w') as file:
            file.write(filedata)

        logger.info(
            'Created {0} Plugin in the current working directory'.format(gen))

    if dut:
        logger.info("Creating sample Plugin directory for DuT Type with name:" +
                    str(dut))
        root = os.path.abspath(os.path.dirname(__file__))
        src = os.path.join(root, "templates/setup/dut/")
        dest = os.path.join(cwd, dut)
        logger.debug('Copy files')
        shutil.copytree(src, dest)

        # Rename stuff
        logger.debug('Renaming files')
        os.rename(cwd + '/' + dut + '/sample_plugin.py',
                  cwd + '/' + dut + '/' + dut + '_plugin.py')

        # Plugin.py
        with open(cwd + '/' + dut + '/' + dut + '_plugin.py', 'r') as file:
            filedata = file.read()

        # Replace the target string
        logger.debug('Replacing names')
        filedata = filedata.replace('sample', dut.lower())

        # Write the file out again
        with open(cwd + '/' + dut + '/' + dut + '_plugin.py', 'w') as file:
            file.write(filedata)

        # conftest
        with open(cwd + '/' + dut + '/' + 'conftest.py', 'r') as file:
            filedata = file.read()

        # Replace the target string
        logger.debug('Replacing names')
        filedata = filedata.replace('sample', dut.lower())

        # Write the file out again
        with open(cwd + '/' + dut + '/' + 'conftest.py', 'w') as file:
            file.write(filedata)

        logger.info(
            'Created {0} Plugin in the current working directory'.format(dut))

    if ref:
        logger.info(
            "Creating sample Plugin directory for Reference Type with name:" +
            str(ref))
        root = os.path.abspath(os.path.dirname(__file__))
        src = os.path.join(root, "templates/setup/reference/")
        dest = os.path.join(cwd, ref)
        logger.debug('Copy files')
        shutil.copytree(src, dest)

        # Rename stuff
        logger.debug('Renaming files')
        os.rename(cwd + '/' + ref + '/sample_plugin.py',
                  cwd + '/' + ref + '/' + ref + '_plugin.py')

        # Plugin.py
        with open(cwd + '/' + ref + '/' + ref + '_plugin.py', 'r') as file:
            filedata = file.read()

        # Replace the target string
        logger.debug('Replacing names')
        filedata = filedata.replace('sample', ref.lower())

        # Write the file out again
        with open(cwd + '/' + ref + '/' + ref + '_plugin.py', 'w') as file:
            file.write(filedata)

        # conftest
        with open(cwd + '/' + ref + '/' + 'conftest.py', 'r') as file:
            filedata = file.read()

        # Replace the target string
        logger.debug('Replacing names')
        filedata = filedata.replace('sample', ref.lower())

        # Write the file out again
        with open(cwd + '/' + ref + '/' + 'conftest.py', 'w') as file:
            file.write(filedata)

        logger.info(
            'Created {0} Plugin in the current working directory'.format(ref))
