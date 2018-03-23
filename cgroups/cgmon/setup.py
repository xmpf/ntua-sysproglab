from setuptools import setup, find_packages

INSTALL_REQUIRES = [
    'lockfile==0.12.2',
    'argparse',
    'python-daemon<2.1',
    'jsonrpclib',
    'cliff<2',
]

ENTRY_POINTS = {
    'console_scripts': [
        'cgmond = cgmond.daemon.monitor:entry_point',
        'cgmon = cgmond.client.client:main',
        'cgmon-cgroup-cb = cgmond.scripts.cb:main',
    ]
}

setup(name='cgmond',
            version='1.0',
            description='Cgroups monitoring daemon',
            author='Filippos Giannakos',
            author_email='philipgian@grnet.gr',
            url='',
            install_requires=INSTALL_REQUIRES,
            package_dir={'': '.'},
            packages=find_packages('.'),
            entry_points=ENTRY_POINTS,
           )
