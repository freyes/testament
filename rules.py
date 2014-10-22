import re
import sys

from checks import available_checks

available_rules = {}

def rule(definition):
    def wrapper(wrapped, *args, **kwargs):
        compiled = re.compile(".*%s$" % definition)
        if not compiled.pattern in available_rules.keys():
            available_rules[compiled.pattern] = {
                'pattern': compiled,
                'handler': wrapped
            }
        else:
            raise Exception('Expression: "%s", already exists' % (
                    definition))
        return wrapped
    return wrapper


@rule("Given the (.*) provider")
def provider(context, provider):
    context.provider = provider

@rule("I want to deploy ([1-9])+ unit[s]* of ([a-zA-Z]+)")
def deploy(context, units, charm):
    print "juju deploy -n %s %s" % (units, charm)

@rule("I want to relate ([a-zA-Z]+) and ([a-zA-Z]+)")
def relate(context, first, second):
    print "juju add-relation %s %s" % (first, second)

@rule("Check that ([a-zA-Z]+) unit['s']* (.*)")
def check_rule(context, unit, condition):
    for i, v in available_checks.items():
        matched = re.match(v['pattern'], condition)
        if matched:
            context.append_check(
                v['handler'],
                unit,
                *matched.groups()
            )
    
def parse(context, line):
    for i, v in available_rules.items():
        matched = re.match(v['pattern'], line)
        if matched:
            return v['handler'](context, *matched.groups())

class Context(object):
    valid_providers = ( 'local', )

    def __init__(self, *args, **kwargs):
        self.checks = {}
    
    @property
    def provider(self):
        return self._provider

    @provider.setter
    def provider(self, value):
        if not value in self.valid_providers:
            raise Exception('Invalid specified provider')
        self._provider = value

    @property
    def deployment(self, value):
        pass

    def append_check(self, handler, unit, *args):
        if handler not in self.checks.keys():
            self.checks[handler] = []
        self.checks[handler].append((unit, args, ))
 
    def run_checks(self):
        for handler, checks in self.checks.items():
            for params in checks:
                (unit, argv) = (params)
                try:
                    assert handler(unit, *argv) == True
                except AssertionError:
                    print "Check %s on unit %s failed" % (handler.__name__,
                                                          unit)
                    sys.exit(-1)
def main():
    with open(sys.argv[1]) as fd:
        context = Context()
        for line in fd.readlines():
            if not line.startswith('#'):
                parse(context, line)
        context.run_checks()

if __name__ == "__main__":
    main()
