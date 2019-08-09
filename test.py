from flask import Flask, jsonify
from flask_influxdb_response_log import FlaskInfluxDBResponseLog

app = Flask(__name__)
app.config.from_pyfile('test.cfg')
response_log = FlaskInfluxDBResponseLog()
response_log.init_app(app=app)


@response_log.error_write
def error_write(error):
    print(error)


@app.route('/check', methods=['get', 'post'])
def check():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run()
