#!/bin/bash
# Generate certificates for WebSocket server secure connections (WSS)
# This script creates self-signed certificates for development and testing

set -e  # Exit on any error

# Create directory for certificates
CERT_DIR="$(dirname "$0")/certs"
mkdir -p "$CERT_DIR"

echo "Generating self-signed certificates for WebSocket server..."

# Generate private key
openssl genrsa -out "$CERT_DIR/server.key" 2048

# Generate certificate signing request
openssl req -new -key "$CERT_DIR/server.key" -out "$CERT_DIR/server.csr" \
  -subj "/C=US/ST=State/L=City/O=RFM Architecture/OU=Development/CN=localhost"

# Generate self-signed certificate
openssl x509 -req -days 365 -in "$CERT_DIR/server.csr" \
  -signkey "$CERT_DIR/server.key" -out "$CERT_DIR/server.crt"

# Verify certificate
openssl x509 -in "$CERT_DIR/server.crt" -text -noout

echo "Certificate generation complete! Files created:"
echo "- $CERT_DIR/server.key (private key)"
echo "- $CERT_DIR/server.crt (certificate)"
echo "- $CERT_DIR/server.csr (certificate signing request)"

echo "WARNING: These are self-signed certificates suitable only for development."
echo "For production, use certificates from a trusted certificate authority."