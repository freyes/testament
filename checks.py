import re

available_checks = {}

def check(definition):
    def wrapper(wrapped, *args, **kwargs):
        compiled = re.compile(".*%s$" % definition)
        if not compiled.pattern in available_checks.keys():
            available_checks[compiled.pattern] = {
                'pattern': compiled,
                'handler': wrapped
            }
        else:
            raise Exception('Check: "%s", already exists' % (
                    definition))
        return wrapped
    return wrapper

@check("has port ([0-9]+)+ opened")
def has_port_open(unit, port):
    print "juju status | grep %s | grep %s" % (unit, port)
    return True

@check("command (.*) returns ([0-9]+)+")
def command_returns(unit, command, code):
    print "juju ssh --unit %s/0 '%s'" % (unit, command.strip('"'))
    return False
