import re
import sys

from utils import run, load_yaml, get_environment

from testament.checks.units import checks as unit_checks
from testament.checks.services import checks as service_checks

available_rules = {}


class Unit:

    def __init__(self, name, data, service, environment):
        self.name = name
        self.service = service
        self.environment = environment

        for k, v in data.items():
            setattr(self, k.replace("-", "_"), v)


class Service:

    def __init__(self, name, environment,
                 skip_relations=["cluster", ]):
        self.name = name
        self.skip_relations = skip_relations
        self.status = environment.environment.get("services")[self.name]
        self.environment = environment

    def to_dict(self):
        r = {
            'num_units': self.units,
            'charm': self.charm,
        }

        if self.constraints:
            r.update({
                'constraints': self.constraints,
            })

        if len(self.options):
            r.update({
                'options': self.options,
            })

        r.update({
            'to': self.placement,
        })

        return r

    @property
    def constraints(self):
        try:
            return run("juju get-constraints %s" % self.name).strip("\n")
        except:
            return None

    @property
    def options(self):
        config = load_yaml("juju get %s" % self.name)
        options = {}
        inc_defaults = True
        for k, v in config.get('settings').items():
            if 'value' in v and (not v.get('default', False) or inc_defaults):
                options[k] = v['value']
        return options

    @property
    def relations(self):
        if 'relations' in self.status:
            for name, items in self.status.get('relations').items():
                if name not in self.skip_relations:
                    for item in items:
                        if self.name != item:
                            yield sorted([self.name, item])

    @property
    def units(self):
        if 'units' in self.status:
            return len(self.status.get("units"))
        return 1

    @property
    def charm(self):
        def r(m):
            return m.groups()[0]

        format = self.environment.options.location_format

        if self.environment.options.include_charm_versions:
            charm = self.status.get('charm')
        else:
            charm = re.sub("(.*)(\-[0-9]+)", r,
                           self.status.get('charm'))

        if format == "cs" and charm.startswith("local"):
            return charm.replace("local", "cs")
        elif format == "local" and charm.startswith("cs"):
            return charm.replace("cs", "local")
        else:
            return charm

    @property
    def placement(self):
        units = self.status.get('units', None)
        if units:
            if len(units) > 1:
                return map(lambda x: x.get('machine'), units.values())
            else:
                return units[units.keys()[0]].get('machine')
        return None


class Environment:

    def __init__(self):
        self.environment = load_yaml("juju status -e %s --format=yaml" %
                                     get_environment())

    @property
    def services(self):
        services = []
        for service in self.environment.get('services').keys():
            services.append(Service(service, self))
        return services

    @property
    def units(self):
        units = []
        for name, service in self.environment.get('services').items():
            for unit_name, unit in service.get("units").items():
                units.append(Unit(unit_name, unit,
                                  self.get_service(service), self))
        return units

    def get_unit(self, name):
        for unit in self.units:
            if unit.name == name:
                return unit
        return None

    def get_service(self, name):
        for service in self.services:
            if service.name == name:
                return service
        return None


def check(definition):
    def wrapper(wrapped, *args, **kwargs):
        compiled = re.compile(".*%s$" % definition)
        if compiled.pattern not in available_checks.keys():
            available_checks[compiled.pattern] = {
                'pattern': compiled,
                'handler': wrapped
            }
        else:
            raise Exception('Check: "%s", already exists' % (
                    definition))
        return wrapped
    return wrapper


def rule(definition):
    def wrapper(wrapped, *args, **kwargs):
        compiled = re.compile(".*%s$" % definition)
        if compiled.pattern not in available_rules.keys():
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


@rule("Check unit ([a-zA-Z-/0-9]+) (.*)")
def unit_check_rule(context, unit_name, condition):
    for i, v in unit_checks.items():
        matched = re.match(v['pattern'], condition)
        if matched:
            unit = context.environment.get_unit(unit_name)
            if not unit:
                raise Exception(
                    "Unit %s not found on the environment" % unit_name)
            context.append_check(
                v['handler'],
                unit,
                *matched.groups()
            )


@rule("Check service ([a-zA-Z-/0-9]+) (.*)")
def service_check_rule(context, unit_name, condition):
    for i, v in service_checks.items():
        matched = re.match(v['pattern'], condition)
        if matched:
            unit = context.environment.get_unit(unit_name)
            if not unit:
                raise Exception(
                    "Unit %s not found on the environment" % unit_name)
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
    valid_providers = ('local', )

    def __init__(self, *args, **kwargs):
        self.checks = {}
        self.environment = Environment()

    def append_check(self, handler, unit, *args):
        if handler not in self.checks.keys():
            self.checks[handler] = []
        self.checks[handler].append((unit, args, ))

    def run_checks(self):
        for handler, checks in self.checks.items():
            for params in checks:
                (unit, argv) = (params)
                try:
                    handler(unit, *argv)
                except AssertionError as ex:
                    print "Check %s (params: %s) on unit %s failed, %s" % (
                        handler.__name__, argv,
                        unit.name, ex)
                    sys.exit(-1)
                else:
                    print "Check %s (params: %s) on unit %s passed :)" % (
                        handler.__name__, argv, unit.name)
        sys.exit(0)


def main():
    with open(sys.argv[1]) as fd:
        context = Context()
        for line in fd.readlines():
            if not line.startswith('#'):
                parse(context, line)
        context.run_checks()
