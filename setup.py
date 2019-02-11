from setuptools import find_packages, setup

LONG_DESCRIPTION = open('README.md').read()

INSTALL_REQUIRES = [
    'requests',
    'requests-html',
    'python-dateutil'
]

setup(
    name='timepro-timesheet',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description='Utility for programmatically getting and submitting data to Intertec TimePro (timesheets.com.au)',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='http://github.com/christippett/timepro-timesheet',
    author='Chris Tippett',
    author_email='c.tippett@gmail.com',
    license='MIT',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    entry_points = {
        'console_scripts': ['timepro=timepro_timesheet.cli:main'],
    },
    install_requires=INSTALL_REQUIRES,
    classifiers=[
        'Environment :: Web Environment',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    zip_safe=False
)
