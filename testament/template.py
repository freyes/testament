#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jinja2 import Environment, PackageLoader

__author__ = 'Jorge Niedbalski R. <jnr@metaklass.org>'


env = Environment()
env.loader = PackageLoader('testament', 'templates')


def load(name, params):
    """
    Load a template from the maasive.templates package
    :param name: template name
    :type name: string
    """
    return env.get_template(name + ".tpl").render(**params)
