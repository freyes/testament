from testament.utils import check_call, juju_run_unit

import re

__author__ = "Jorge Niedbalski <jnr@metaklass.org>"

checks = {}


def check(definition):
    def wrapper(wrapped, *args, **kwargs):
        compiled = re.compile(".*%s$" % definition)
        if compiled.pattern not in checks.keys():
            checks[compiled.pattern] = {
                'pattern': compiled,
                'handler': wrapped
            }
        else:
            raise Exception('Check: "%s", already exists' % definition)
        return wrapped
    return wrapper


@check("have port ([0-9]+)+ opened")
def has_port_open(unit, port):
    try:
        check_call("nc -z %s %s" % (unit.public_address, port))
    except:
        assert False is True


@check("agent-state is (.*)")
def agent_state_status(unit, status):
    assert unit.agent_state == status


@check("agent-version is (.*)")
def agent_version(unit, version):
    assert unit.agent_version == version


@check("command (.*) returns ([0-9]+)+")
def command_returns(unit, command, code):
    output = juju_run_unit(unit.name, command)
    return_code = output.get("ReturnCode", 0)
    assert return_code == int(code)
