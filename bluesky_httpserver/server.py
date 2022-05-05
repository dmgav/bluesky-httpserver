import argparse
import logging
import os

import bluesky_httpserver

from .app import build_app

logger = logging.getLogger(__name__)

qserver_version = bluesky_httpserver.__version__

default_http_server_host = "localhost"
default_http_server_port = 60610


def start_server():

    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("bluesky_httpserver").setLevel("INFO")

    def formatter(prog):
        # Set maximum width such that printed help mostly fits in the RTD theme code block (documentation).
        return argparse.RawDescriptionHelpFormatter(prog, max_help_position=20, width=90)

    parser = argparse.ArgumentParser(
        description="Start Bluesky HTTP Server.\n" f"bluesky-httpserver version {qserver_version}.\n",
        formatter_class=formatter,
    )

    parser.add_argument(
        "--http-server-host",
        dest="http_server_host",
        action="store",
        default=None,
        help="HTTP server host name, e.g. '127.0.0.1' or 'localhost' " f"(default: {default_http_server_host!r}).",
    )

    parser.add_argument(
        "--http-server-port",
        dest="http_server_port",
        action="store",
        default=None,
        help="HTTP server port, e.g. '127.0.0.1' or 'localhost' " f"(default: {default_http_server_port!r}).",
    )

    args = parser.parse_args()

    http_server_host = args.http_server_host
    http_server_host = http_server_host or os.getenv("QSERVER_HTTP_SERVER_HOST", None)
    http_server_host = http_server_host or default_http_server_host

    http_server_port = args.http_server_port
    http_server_port = http_server_port or os.getenv("QSERVER_HTTP_SERVER_PORT", None)
    http_server_port = http_server_port or default_http_server_port

    logger.info("Preparing to starting Bluesky HTTP Server ...")

    web_app = build_app({}, {})

    logger.info("Starting Bluesky HTTP Server at {http_server_host}:{http_server_port} ...")

    import uvicorn

    uvicorn.run(web_app, host=http_server_host, port=http_server_port)


def app_factory():
    """
    Return an ASGI app instance.

    Use a configuration file at the path specified by the environment variable
    QSERVER_HTTP_SERVER_CONFIG or, if unset, at the default path "./config.yml".

    This is intended to be used for horizontal deployment (using gunicorn, for
    example) where only a module and instance or factory can be specified.
    """
    # config_path = os.getenv("QSERVER_HTTP_SERVER_CONFIG", "config.yml")
    # logger.info(f"Using configuration from {Path(config_path).absolute()}")

    # from ..config import construct_build_app_kwargs, parse_configs

    # parsed_config = parse_configs(config_path)

    # # This config was already validated when it was parsed. Do not re-validate.
    # kwargs = construct_build_app_kwargs(parsed_config, source_filepath=config_path)
    kwargs = {}
    web_app = build_app(**kwargs)
    # uvicorn_config = parsed_config.get("uvicorn", {})
    # print_admin_api_key_if_generated(
    #     web_app, host=uvicorn_config.get("host"), port=uvicorn_config.get("port")
    # )
    return web_app


def __getattr__(name):
    """
    This supports tiled.server.app.app by creating app on demand.
    """
    if name == "app":
        try:
            return app_factory()
        except Exception as err:
            raise Exception("Failed to create app.") from err
    raise AttributeError(name)
