import certifi
import ssl
import os

print(f"Current certificates path: {ssl.get_default_verify_paths().cafile}")
os.environ['SSL_CERT_FILE'] = certifi.where()
print(f"New certificates path: {certifi.where()}")