import logging
import threading

from .handler import CaptureRequestHandler, create_custom_capture_request_handler
from .server import ProxyHTTPServer

log = logging.getLogger(__name__)

DEFAULT_BACKEND = 'default'


def create(addr='127.0.0.1', port=0, options=None):
    """Create a new proxy backend.

    The type of backend created depends on the 'backend' option. Supported types
    are 'default' and 'mitmproxy'. When not specified, the default backend will
    be used. The mitmproxy backend is dependent on the mitmproxy package being
    installed.

    Args:
        addr: The address the proxy server will listen on. Default 127.0.0.1.
        port: The port the proxy server will listen on. Default 0 - which means
            use the first available port.
        options: Additional options to configure the proxy.

    Returns:
        An instance of the proxy backend.
    """
    if options is None:
        options = {}

    backend = options.get('backend', DEFAULT_BACKEND)

    if backend == DEFAULT_BACKEND:
        # Use the default backend
        # Note that the use of custom_response_handler is deprecated.
        custom_response_handler = options.pop('custom_response_handler', None)
        if custom_response_handler is not None:
            capture_request_handler = create_custom_capture_request_handler(custom_response_handler)
        else:
            capture_request_handler = CaptureRequestHandler
            # Set the timeout here before the handler starts executing
            capture_request_handler.timeout = options.get('connection_timeout', 5)

        proxy = ProxyHTTPServer(addr, port, capture_request_handler, options=options)
    elif backend == 'mitmproxy':
        # Use mitmproxy if installed
        from . import mitmproxy

        proxy = mitmproxy.MitmProxy(addr, port, options)
    else:
        raise TypeError(
            "Invalid backend '{}'. "
            "Valid values are 'default' or 'mitmproxy'."
            .format(options['backend'])
        )

    t = threading.Thread(name='Selenium Wire Proxy Server', target=proxy.serve_forever)
    t.daemon = not options.get('standalone')
    t.start()

    log.info('Created proxy listening on {}:{}'.format(*proxy.address()))

    return proxy
