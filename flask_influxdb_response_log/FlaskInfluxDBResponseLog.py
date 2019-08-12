import json
from datetime import datetime
from flask import Flask, request, g
from flask_influxdb_client import InfluxDB
from flask_influxdb_client.flask_influxdb_client import influxdb


class FlaskInfluxDBResponseLog:
    """
    Logging response for Flask applications using InfluxDB as storage.

    -----------------------------------------------------------
    Flask configuration variables to set connection to InfluxDB
    -----------------------------------------------------------
    RESPONSE_LOG_INFLUXDB_HOST           Host for the InfluxDB host. Default is localhost.
    RESPONSE_LOG_INFLUXDB_PORT           InfluxDB HTTP API port. Default is 8086.
    RESPONSE_LOG_INFLUXDB_USER           InfluxDB server username. Default is root.
    RESPONSE_LOG_INFLUXDB_PASSWORD       InfluxDB server password. Default is root.
    RESPONSE_LOG_INFLUXDB_DATABASE       Optional database to connect.  Defaults to None.
    RESPONSE_LOG_INFLUXDB_SSL            Enables using HTTPS instead of HTTP. Defaults to False.
    RESPONSE_LOG_INFLUXDB_VERIFY_SSL     Enables checking HTTPS certificate. Defaults to False.
    RESPONSE_LOG_INFLUXDB_RETRIES        Number of retries the client will try before aborting, 0 indicates try until success.
                                         Defaults to 3
    RESPONSE_LOG_INFLUXDB_TIMEOUT        Sets request timeout. Defaults to None.
    RESPONSE_LOG_INFLUXDB_USE_UDP        Use the UDP interfaces instead of http. Defaults to False.
    RESPONSE_LOG_INFLUXDB_UDP_PORT       UDP api port number. Defaults to 4444.
    RESPONSE_LOG_INFLUXDB_PROXIES        HTTP(S) proxy to use for Requests. Defaults to None.
    RESPONSE_LOG_INFLUXDB_POOL_SIZE      urllib3 connection pool size. Defaults to 10.


    --------------------------------------------
    Flask configuration variables to set logging
    --------------------------------------------
    RESPONSE_LOG_INFLUXDB_MEASUREMENT    Measurement name to store response logging
    RESPONSE_LOG_INFLUXDB_NAMESPACE      Namespace associated to a response logging.
                                         Namespaces are useful in case you use the same measurement for different applications.
    RESPONSE_LOG_STATUS_CODE_ONLY        List of status codes to keep in log. If empty or not found, all status codes will be saved.
    """

    __error_write_callback__ = None

    def __init__(self, app: Flask = None):
        """
        Class constructor
        :param app: Flask application to configure
        """
        if app is not None:
            self.init_app(app=app)

    def error_write(self, f):
        """
        Write error function decorator
        :param f: Function to set as abort function
        :return:
        """
        self.__error_write_callback__ = f

    def _error_write_raise(self, error: Exception):
        """
        Execute decorated function from writing error
        :param error: Error retrieved
        :return:
        """
        if self.__error_write_callback__ is not None:
            self.__error_write_callback__(error=error)

    def init_app(self, app: Flask):
        """
        Initialize application with logging configuration
        :param app: Flask application to configure
        :return:
        """
        status_code_only = app.config.get('RESPONSE_LOG_STATUS_CODE_ONLY')
        if type(status_code_only) != list:
            status_code_only = []

        # Flag to indicate there is at least one filter on status codes
        filter_status_code = len(status_code_only) > 0

        influx_db_connection = InfluxDB(app=app, prefix='RESPONSE_LOG')

        # Set measurement name to store response logging
        measurement = app.config.get('RESPONSE_LOG_INFLUXDB_MEASUREMENT')
        if measurement == '':
            measurement = 'response_log'

        """
        Namespace value associated to each response logging.
        You can define a namespace in case you use the same measurement
        for different applications.
        """
        # Set namespace value from configuration
        namespace = app.config.get('RESPONSE_LOG_INFLUXDB_NAMESPACE')

        class MeasurementResponseLog(influxdb.SeriesHelper):
            """
            Class to define measurement structure for response logging
            """

            class Meta:
                # Meta class stores time series helper configuration.
                series_name = measurement
                tags = [
                    'namespace',  # Namespace for response
                    'path',  # Path (without base_url or query string)
                    'method'  # Request method
                ]

                fields = [
                    'remote_addr',  # Remote IP address
                    'headers',  # Headers from request
                    'full_path',  # Full path (only with query string)
                    'query_string',  # Query string from path
                    'payload',  # Payload data
                    'status_code',  # Status code for response
                    'response',  # Response value
                    'response_content_type',  # Content type for response
                    'response_time'  # Response time
                ]

        @app.before_request
        def before_request():
            """
            Processing before accepting request
            :return:
            """
            # Keep UTC time instead of local time
            g.start_time = datetime.utcnow()

        @app.after_request
        def after_request(response):
            """
            Logging after processing request
            :param response: Response from request
            :return: Response to output to user
            """
            # Check if there is a filter list and if status code is in filter
            status_code = response.status_code  # integer type
            if filter_status_code is False:
                log_response = True
            else:
                log_response = False if status_code not in status_code_only else True

            if log_response is True:
                json_separators = (',', ':')

                # Request execution time (UTC)
                start_time = g.start_time
                response_time = str(datetime.utcnow() - start_time)
                start_time_iso = start_time.isoformat(sep=' ')

                # Store headers as JSON
                headers = request.headers.to_wsgi_list()
                headers_js = {header[0]: header[1] for header in headers if len(header) == 2}
                json_expected = True \
                    if 'Content-Type' in headers_js and headers_js['Content-Type'] == 'application/json' \
                    else False

                # Payload data from request
                if json_expected:
                    payload = request.get_json(silent=True)
                    if payload is not None:
                        try:
                            # Remove spaces prior to store in database
                            payload = json.dumps(payload, separators=json_separators)
                        except json.JSONDecodeError:
                            payload = ''
                else:
                    try:
                        payload = request.get_data().decode('utf-8')
                    except UnicodeEncodeError:
                        payload = ''

                # Get response data
                response_content_type = response.content_type

                try:
                    response_data = response.get_data(as_text=True)
                except RuntimeError:
                    # For files that are not possible to convert as text, a RuntimeError exception is thrown
                    response_data = ''

                if response_content_type == 'application/json':
                    try:
                        response_data = json.dumps(json.loads(response_data), separators=json_separators)
                    except json.JSONDecodeError:
                        pass

                try:
                    headers_data = json.dumps(headers_js, separators=json_separators)
                except json.JSONDecodeError:
                    headers_data = ''

                # Query string decoding
                try:
                    query_string = request.query_string.decode('utf-8')
                except UnicodeEncodeError:
                    query_string = ''

                # Create and write response on InfluxDB
                MeasurementResponseLog(
                    time=start_time_iso,
                    namespace=namespace,
                    path=request.path,
                    method=request.method,
                    remote_addr=request.remote_addr,
                    full_path=request.full_path,
                    payload=payload,
                    headers=headers_data,
                    status_code=status_code,
                    query_string=query_string,
                    response=response_data,
                    response_time=response_time,
                    response_content_type=response_content_type
                )

                try:
                    MeasurementResponseLog.commit(client=influx_db_connection.connection)
                except Exception as error:
                    # In case of error, execute decorated function
                    self._error_write_raise(error=error)

            return response
