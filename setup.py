
from setuptools import setup,find_packages
setup(
    name='task-manage',
    version='1.0.0',
    metadata_version='2.1',
    description="A lightweight timed task execution system, supporting python, nodejs, and all command-line tasks",
    author = "tianling",  
    author_email = "34492114@qq.com",
    license='MIT Licence',
    keywords=("cron" , "task", "cmd"),
    url="https://packaging.python.org/specifications/core-metadata",
    home_page="https://packaging.python.org/specifications/core-metadata",
    package_dir = {'':'src'},  # 告诉distutils包都在src下
    packages=find_packages(
        where="src",
        exclude=[],
    ),
    # py_modules=['main'],
    package_data = {
        # 任何包中含有.txt文件，都包含它
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
