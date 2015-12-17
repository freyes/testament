import subprocess
import os
import shlex
import yaml


def run(cmd):
    return subprocess.check_output(shlex.split(cmd), stderr=subprocess.PIPE)


def juju_run_unit(unit, cmd):
    output = load_yaml(
        "juju run --unit %s --format=yaml %s" % (unit, cmd))
    return output[0]


def check_call(cmd):
    return subprocess.check_call(shlex.split(cmd))


def load_yaml(cmd):
    return yaml.load(run(cmd))


def get_environment():
    environment = os.environ.get("JUJU_ENV", None)
    if not environment:
        try:
            environment = run("juju env").strip()
        except:
            environment = None
    return environment
