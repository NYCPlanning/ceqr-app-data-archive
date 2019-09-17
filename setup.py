from setuptools import setup, find_packages

setup(
        name='ceqr',
        version='0.1',
        description='cooking recipes ...',
        license='MIT',
        pacakges=find_packages(),
        install_requires=[
            'click',
            'psycopg2-binary',
            'sqlalchemy',
            'pandas',
            'python-dotenv'],
        entry_points='''
        [console_scripts]
        ceqr=ceqr.cli:cli
      '''
    )