import logging

logging.basicConfig(level=logging.DEBUG)

requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)
