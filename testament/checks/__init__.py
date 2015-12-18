import re


def check(definition):
    def wrapper(wrapped, *args, **kwargs):
        compiled = re.compile(".*%s$" % definition)
        if compiled.pattern not in available_checks.keys():
            checks[compiled.pattern] = {
                'pattern': compiled,
                'handler': wrapped
            }
        else:
            raise Exception('Check: "%s", already exists' % definition)
        return wrapped
    return wrapper
