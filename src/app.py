from src.handler import FlaskLambda


def create_app(test_config=None):
    # create and configure the app
    app = FlaskLambda(__name__)

    # a simple page that says hello
    @app.route("/hello")
    def hello():
        return "Hello, World!"

    return app


app = create_app()
