# Response logging for Flask applications with InfluxDB
This extension is useful to logging responses from Flask applications with InfluxDB as storage.

## Features
The extension saves all requests and responses for Flask applications. Measurement structure in InfluxDB include the following tags and fields:

### Tags
|Name|Description|
|---|---|
|time|Request time (UTC)|
|namespace|Namespace for response. This value is useful whenever there is one measurement that tracks different applications|
|path|Accessed resource (without base URL nor query string)|
|method|Method used to access resource (POST, GET, PUT, DELETE, PATCH)|


### Fields
|Name|Description|
|---|---|
|remote_addr|IP address from remote access|
|headers|Headers set on request. JSON string|
|full_path|Full path for resource (without base URL, only query string added)|
|query_string|Query string for path|
|payload|Data sent on request|
|status_code|HTTP status code for response |
|response|Response content|
|response_content_type|Content type for response|
|response_time|Execution time for request -> response|

It is also possible to define: 
- a custom decorator whenever there is a problem with connection and writing points on InfluxDB;
- a filter of response status codes to keep in log. 

## Requirements
* Python >= 3
* Flask
* [flask-influxdb-client](https://github.com/aaronestrada/flask-influxdb-client) >= v0.2

## Installation
Install the extension via *pip*:

```
$ pip install git@github.com/aaronestrada/flask-influxdb-response-log.git@0.1
```

## Example
The library can be accessed via ``FlaskInfluxDBResponseLog`` class:

```python
from flask import Flask
from flask_influxdb_response_log import FlaskInfluxDBResponseLog

app = Flask(__name__)

response_log = FlaskInfluxDBResponseLog(app=app)

# Custom decorator for error during writing values in InfluxDB
@response_log.error_write
def error_write(error):    
    print(error)
```

Delayed application configuration of ``FlaskInfluxDBResponseLog`` is also supported using the **init_app** method:

```python

from flask import Flask
from flask_influxdb_response_log import FlaskInfluxDBResponseLog

app = Flask(__name__)
response_log = FlaskInfluxDBResponseLog()
# ...
response_log.init_app(app=app)
```

## Configuration values

### Set connection to InfluxDB
```
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
```

### Logging
```
RESPONSE_LOG_INFLUXDB_MEASUREMENT    Measurement name to store response logging
RESPONSE_LOG_INFLUXDB_NAMESPACE      Namespace associated to a response logging.
                                     Namespaces are useful in case you use the same measurement for different applications.
RESPONSE_LOG_STATUS_CODE_ONLY        List of status codes to keep in log. If empty or not found, all status codes will be saved.
```                                        

## Testing
To run the example code:
```
$ FLASK_APP=test.py FLASK_DEBUG=1 FLASK_ENV=development flask run
```

Execute the following test using cURL:

```bash
curl -d "{\"a\":1}" -H "Content-Type: application/json" -X POST http://127.0.0.1:5000/check
```

You should have the following item in the measurement "response_log" on your local InfluxDB instance. **Note**: you must create the database "mydb" before testing the resource.

```
time                    <UTC time for request + response> 
namespace               test
path                    /check
method                  POST
remote_addr             127.0.0.1
full_path               /check?       
query_string            <empty>                                                                                                                                                                                                                                                 
headers                 {"Host":"127.0.0.1:5000","User-Agent":"curl/7.54.0","Accept":"*/*","Content-Type":"application/json","Content-Length":"10"}
payload                 {"a":2}
status_code             200
response                {"status":"ok"}
response_content_type   application/json
response_time           <request -> response execution time>
```
