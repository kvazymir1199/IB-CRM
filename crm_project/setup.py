from setuptools import setup, find_packages

setup(
    name="crm_project",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'django>=4.2.0',
        'ib_insync>=0.9.70',
        'celery>=5.3.6',
        'redis>=5.0.1',
    ],
) 