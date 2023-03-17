"""TODO"""
import logging
import sys

from io import StringIO
from flask import Flask
from urllib.parse import urlencode
from werkzeug.wrappers import Request as BaseRequest

from backend.config import LOG_LEVEL


logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)


def make_environ(event):
    environ = {}

    # TODO Seems to be outdated.
    qs = event["queryStringParameters"]

    environ["REQUEST_METHOD"] = event["requestContext"]["http"]["method"]
    environ["PATH_INFO"] = event["requestContext"]["http"]["path"]
    environ["QUERY_STRING"] = urlencode(qs) if qs else ""
    environ["REMOTE_ADDR"] = event["requestContext"]["http"]["sourceIp"]
    environ["HOST"] = "{}:{}".format(event["headers"]["x-forwarded-for"], event["headers"]["x-forwarded-port"])
    environ["SCRIPT_NAME"] = ""

    environ["SERVER_PORT"] = event["headers"]["x-forwarded-port"]
    environ["SERVER_PROTOCOL"] = event["requestContext"]["http"]["protocol"]

    # TODO Additional work is needed
    body = event.get("body", "")
    environ["CONTENT_LENGTH"] = str(
        len(body) if body else ""
    )

    environ["wsgi.url_scheme"] = event["requestContext"]["http"]["protocol"]
    environ["wsgi.input"] = StringIO(body)
    environ["wsgi.version"] = (1, 0)
    environ["wsgi.errors"] = sys.stderr
    environ["wsgi.multithread"] = False
    environ["wsgi.run_once"] = True
    environ["wsgi.multiprocess"] = False

    BaseRequest(environ)

    return environ


class LambdaResponse(object):
    def __init__(self):
        self.status = None
        self.response_headers = None

    def start_response(self, status, response_headers, exc_info=None):
        self.status = int(status[:3])
        self.response_headers = dict(response_headers)


class FlaskLambda(Flask):
    def __call__(self, event, context):
        logger.debug(f"Got event: {event}")

        if "http" not in event.get("requestContext", []):
            # In this "context" `event` is `environ` and
            # `context` is `start_response`, meaning the request didn"t
            # occur via API Gateway and Lambda
            return super(FlaskLambda, self).__call__(event, context)

        response = LambdaResponse()

        environ = make_environ(event)

        body = next(self.wsgi_app(
            environ,
            response.start_response
        ))

        return {
            "statusCode": response.status,
            "headers": response.response_headers,
            "body": body
        }
