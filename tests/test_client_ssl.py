import importlib
import os
import unittest

import certifi


class ClientSSLTests(unittest.TestCase):
    def test_get_client_sets_ssl_cert_file_from_certifi_when_missing(self):
        previous = os.environ.pop("SSL_CERT_FILE", None)
        try:
            client = importlib.import_module("client")
            client = importlib.reload(client)
            client.reset_client()

            client.get_client()

            self.assertEqual(os.environ.get("SSL_CERT_FILE"), certifi.where())
        finally:
            client.reset_client()
            if previous is None:
                os.environ.pop("SSL_CERT_FILE", None)
            else:
                os.environ["SSL_CERT_FILE"] = previous


if __name__ == "__main__":
    unittest.main()
