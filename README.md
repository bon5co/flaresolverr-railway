# flaresolverr-railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/flaresolverr-or-just-updated-cloudflare-?referralCode=Z1xivh&utm_medium=integration&utm_source=template&utm_campaign=generic)

**Deploy on Railway:** [FlareSolverr template](https://railway.com/deploy/flaresolverr-or-just-updated-cloudflare-?referralCode=Z1xivh&utm_medium=integration&utm_source=template&utm_campaign=generic)

Railway wrapper for [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) 3.5.2.

Stock FlareSolverr has no authentication. This image binds it to loopback and serves a
key-checking proxy on `$PORT`; it refuses to boot without `API_KEY` (16+ characters).

- `Authorization: Bearer <API_KEY>`, `X-API-Key: <API_KEY>`, or a leading path segment `/<API_KEY>/v1`
- `GET /health` is open
- no volume needed: sessions live in memory

Image: `ghcr.io/bon5co/flaresolverr-railway:3.5.2`, built by `.github/workflows/publish.yml`.
