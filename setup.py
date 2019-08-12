from distutils.core import setup

setup(
    name='flask-influxdb-response-log',
    version='0.1.1',
    description='Extension to logging response from Flask applications using InfluxDB.',
    license='BSD',
    author='Aaron Estrada Poggio',
    author_email='aaron.estrada.poggio@gmail.com',
    url='https://github.com/aaronestrada/flask-influxdb-response-log',
    packages=['flask_influxdb_response_log'],
    include_package_data=True,
    python_requires='>=3',
    install_requires=[
        'Flask>=1.1.0',
        'flask-influxdb-client @ git+https://git@github.com/aaronestrada/flask-influxdb-client.git@v0.2'
    ]
)
