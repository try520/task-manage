from setuptools import setup,find_packages
setup(
    name='task-manage',
    version='1.0',
    author = "tianling",  
    author_email = "34492114@qq.com",
    license='MIT',
    keywords='cron task cmd',
    package_dir = {'':'src'},
    packages=find_packages(
        where="src",
        exclude=[],
    ),
    # py_modules=['main'],
    package_data = {
        '': ['*.cfg','*.sh']
    },
    install_requires=[
        'click','requests','prettytable','APScheduler','bottle','configParser'
    ],
    entry_points = {
        'console_scripts': [
            'tm = client.main:tm',
            'runtaskmanageserver = server.main'
        ]
    },
    zip_safe=False,
    python_requires='>=3'
)
# -*- coding:UTF-8 -*-