from setuptools import setup, find_packages

dependencies = []

setup(
    name="testament",
    version="0.0.1",
    packages=find_packages(),
    install_requires=dependencies,
    author="Jorge Niedbalski R.",
    author_email="jnr@metaklass.org",
    description="A descriptive test framework for juju environments",
    keywords="juju testing framework",
    include_package_data=True,
    license="BSD",
    entry_points={
        'console_scripts': [
            'testament = testament:main'
        ]
    },

    classifiers=['Development Status :: 3 - Alpha',
                 'Intended Audience :: Developers',
                 'Operating System :: Unix ']
)
