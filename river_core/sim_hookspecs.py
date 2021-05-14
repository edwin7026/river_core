# See LICENSE for details

import importlib
import sys

import pluggy

gen_hookspec = pluggy.HookspecMarker("generator")
dut_hookspec = pluggy.HookspecMarker("dut")


class RandomGeneratorSpec(object):
    """ Test generator specification"""

    @gen_hookspec
    def pre_gen(self, spec_config, output_dir):
        """ Before random generation of ASM begins

            :param spec_config: Config specific to the Plugin 

            :param output_dir:  Output directory for the generated test cases

            :type spec_config: dict 

            :type output_dir: str 
        """

    @gen_hookspec
    def gen(self, gen_config, module_dir, output_dir):
        """ Generation (command execution, file generation etc)

            :param gen_config: Config YAML file path specific to the Plugin 

            :param module_dir:  Module directory location of the module to be loaded 

            :param output_dir:  Output directory for the generated test cases

            :type gen_config: str 

            :type module_dir: str 

            :type output_dir: str 

            :return: Test List basically containing the info about the tests generated and required compiler options

            :rtype: dict
        """

    @gen_hookspec
    def post_gen(self, output_dir):
        """ Post generation operations
            :param output_dir:  Output directory for the generated test cases

            :type output_dir: str 
        """


### creation of regress list into parameterize of tests: D
### simulate_test fixture in pytest calls compilespec plugin and model plugin and dut plugin
# DUT Class Specification
class DuTSpec(object):
    """ DuT plugin specification"""

    @dut_hookspec
    def init(self, ini_config, test_list, work_dir, coverage_config,
             plugin_path):
        """ Get the plugin up and ready 

            :param ini_config: Plugin specific configuration dictionary. 

            :param test_list: Path to the Test List YAML generated by Generator Plugin 

            :param work_dir: Path to the file where the output (files, logs, binaries, etc.) will be generated  

            :param coverage_config: Configuration options for coverage. 

            :param plugin_path: Path to the plugin module to be loaded  

            :type ini_config: dict 

            :type test_list: click.Path  

            :type work_dir: str  

            :type coverage_config: dict 

            :type plugin_path: str  

        """

    @dut_hookspec
    def build(self):
        """ Alright, let's get module running; Basically get things compiled and ready to be loaded onto the core """

    @dut_hookspec
    def run(self, module_dir):
        """ Running things on the core 

            :param module_dir: Path to the module to be loaded. 

            :type module_dir: str 

            :return: Location of the JSON report generated by Pytest used for the final HTML report.

            :rtype: str
        """

    @dut_hookspec
    def post_run(self, test_dict, config):
        """ Perform post run operations, clean-up and others 

            :param test_dict: The test-list YAML 

            :param config: Config.ini configuration options 

            :type test_dict: dict 

            :type config: dict 

        """

    @dut_hookspec
    def merge_db(self, db_files, output_db, config):
        """ Merging different databases together 
            
            :param db_files: List of coverage files detected. 

            :param output_db: Final output name 

            :param config: Config file for RiVerCore

            :type db_files: list 

            :type output_db: str 

            :type config: str 

            :return: HTML files generated by merge 

            :rtype: list 
            """
