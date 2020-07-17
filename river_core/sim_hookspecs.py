# See LICENSE for details

import importlib
import sys

import pluggy

gen_hookspec = pluggy.HookspecMarker("generator")
compile_hookspec = pluggy.HookspecMarker("compile")
model_hookspec = pluggy.HookspecMarker("model")

class RandomGeneratorSpec(object):
    """ Test generator specification"""

#    @gen_hookspec
#    def load_config(self, isa, platform):
#        """ loads riscv_config"""

    @gen_hookspec
    def pre_gen(self, gendir):
        """ before random generation"""

    @gen_hookspec
    def gen(self, gen_config):
        """ generation step"""

    @gen_hookspec
    def post_gen(self, gendir, regressfile):
        """ after generation steps """

### creation of regress list into parameterize of tests: D
### simulate_test fixture in pytest calls compilespec plugin and model plugin and dut plugin

class CompileSpec(object):
    """ Program compilation specification"""

    #@compile_hookspec
    #def load_config(self, isa, platform):
    #    """ loads riscv_config"""

    @compile_hookspec
    def pre_compile(self, compile_config):
        """ gets tool chain config from yaml"""
        # should create test dir
        # should set all gcc etc configs

    @compile_hookspec
    def compile(regress_list, command_line_args):
        """ compiles all tests in the regress list"""

    @compile_hookspec
    def post_compile():
        """ post compile step"""

class ModelSpec(object):

    """Model hook specification"""

    @model_hookspec
    def load_config(self, isa, platform):
        """ loads riscv_config"""

    @model_hookspec
    def load_elf(self, test_elf):
        """ loads test elf"""

    @model_hookspec
    def get_state(self):
        """ get processor state"""

    @model_hookspec
    def step(self, count=1):
        """ step count instructions"""