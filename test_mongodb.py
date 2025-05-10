#!/usr/bin/env python
import sys
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import ssl
import certifi

# Base connection string
base_uri = "mongodb+srv://hhirawat2006:gHUaAP6LduXoThsC@cluster0.5zr5sli.mongodb.net/product_reviews"

# Different connection options to try
connection_options = [
    "?retryWrites=true&w=majority",
    "?retryWrites=true&w=majority&ssl=true",
    "?retryWrites=true&w=majority&ssl=true&tlsAllowInvalidCertificates=true",
    "?retryWrites=true&w=majority&ssl=true&tlsInsecure=true",
    "?retryWrites=true&w=majority&ssl=true&tlsCAFile=" + certifi.where(),
    "?retryWrites=true&w=majority&authSource=admin"
]

# Try each connection option
for options in connection_options:
    uri = base_uri + options
    print(f"\nTrying connection with options: {options}")
    try:
        # Set a short timeout for faster testing
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Force a connection to verify it works
        client.admin.command('ping')
        print("✅ Connection successful!")
        print(f"Working URI: {uri}")
        # Write the working URI to a file
        with open('working_mongodb_uri.txt', 'w') as f:
            f.write(uri)
        sys.exit(0)
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"❌ Connection failed: {str(e)}")

print("\nAll connection attempts failed. Trying with direct SSL context configuration...")

# Try with explicit SSL context
try:
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    uri = base_uri + "?retryWrites=true&w=majority"
    client = MongoClient(uri, ssl=True, ssl_cert_reqs=ssl.CERT_NONE, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✅ Connection successful with custom SSL context!")
    print(f"Working URI: {uri} (with custom SSL context)")
    sys.exit(0)
except Exception as e:
    print(f"❌ Custom SSL context connection failed: {str(e)}")

print("\nAll connection attempts failed.")
sys.exit(1)
