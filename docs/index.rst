Docroot
=======

.. admonition:: MVP Release
   :class: caution

   This is an early MVP release.  The API, file layout, and
   configuration keys may change between releases without a
   compatibility guarantee.  Review the changelog before
   upgrading.

Docroot is a lightweight, self-hosted documentation host.
Upload versioned documentation archives (ZIP files containing
``index.html``) and browse them through a web UI or REST API.

.. toctree::
   :hidden:
   :maxdepth: 2

   user/index
   operator/index
   developer/index

----

Installation
------------

Create a ``docker-compose.yml`` and start the stack:

.. code-block:: yaml

   services:
     api:
       image: ghcr.io/exhuma/docroot/backend:latest
       environment:
         DOCROOT_API_DATA_ROOT: /data
         DOCROOT_API_OAUTH_JWKS_URL: "https://your-idp/jwks.json"
         DOCROOT_API_OAUTH_AUDIENCE: "docroot-api"
       volumes:
         - docroot_data:/data
     web:
       image: ghcr.io/exhuma/docroot/nginx:latest
       ports:
         - "80:80"
       environment:
         DOCROOT_WEB_OIDC_ISSUER: "https://your-idp"
         DOCROOT_WEB_OIDC_CLIENT_ID: "docroot-web"
       volumes:
         - docroot_data:/data
   volumes:
     docroot_data:

.. code-block:: shell

   docker compose up -d

Open ``http://localhost`` in a browser.

See :doc:`operator/index` for all environment variables and
provider-specific OIDC configuration guides.

----

Who Are You?
------------

* **Reading documentation** → :doc:`user/reader`
* **Publishing documentation** → :doc:`user/author`
* **Automating via API / CI-CD** → :doc:`user/integrator`
* **Deploying this service** → :doc:`operator/index`
* **Contributing code** → :doc:`developer/index`
