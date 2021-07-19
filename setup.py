from setuptools import find_packages
from setuptools import setup

setup(
    name='dh_network_simulator',
    version='0.1.3',
    url='https://github.com/cwowi/dh_network_simulator',
    license='BSD 3-Clause License',
    author='Christopher W. Wild',
    author_email='cwowi@elektro.dtu.dk',
    description='A pipeflow simulation tool that complements pandapipes and enables static and dynamic heat transfer simulation in district heating systems.',
    install_requires=["pandapipes>=0.3.0", "numpy", "pandas", "dataclasses", "simple_pid"],
    extras_require={"docs": ["numpydoc", "sphinx", "sphinxcontrib.bibtex"],
                    "plotting": ["matplotlib"],
                    "test": ["pytest"]},
    python_requires='>=3, <4',
    packages=find_packages(),
)
