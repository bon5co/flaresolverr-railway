# Railway wrapper for FlareSolverr: the upstream API locked behind a key from boot.
#
# Source of truth: https://github.com/bon5co/flaresolverr-railway
# Published image:  ghcr.io/bon5co/flaresolverr-railway:3.5.2
#
# Stock FlareSolverr has NO authentication: anyone who finds the URL can make
# your container drive Chromium at any site they name. This image binds the
# upstream server to loopback and puts a small key-checking proxy on $PORT.
FROM ghcr.io/flaresolverr/flaresolverr:v3.5.2

USER root
COPY railway_proxy.py /app/railway_proxy.py
RUN chmod 0644 /app/railway_proxy.py
USER flaresolverr

ENV LOG_LEVEL=info \
    HEADLESS=true \
    HOST=127.0.0.1 \
    UPSTREAM_PORT=8191

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["/usr/local/bin/python", "-u", "/app/railway_proxy.py"]
