
[[_TOC_]]

<img width="128" src="https://gitlab.com/pencillabs/ej/ej-application/-/raw/develop/src/ej/static/ej/assets/img/logo/logo-dark.png?ref_type=heads" align="left" style="margin-right:15px"/>

**Pushing Together** is an open-source web platform to manage participative opinion research, 
with bult-in machine learning algorithm to generate opinion groups from participation data. 
You can visit EJ at [https://www.ejplatform.org](https://www.ejplatform.org).
For detailed information on developing and using our system, please refer to the [documentation](https://www.ejplatform.org/docs/).
For contributions, issues or feature requests join us on [https://gitlab.com/pencillabs/ej/ej-application](https://gitlab.com/pencillabs/ej/ej-application).

## Getting started with Docker

**1. Clone de repository**

    $ git clone https://gitlab.com/pencillabs/ej/ej-application
    $ cd ej-application

**2. Install [docker compose plugin](https://docs.docker.com/compose/install/linux/#install-using-the-repository)**

The following instructions works properly with compose plugin version `v2.21.0` and Docker Engine version `24.0`.

**3. Run inv tasks**

    $ pip3 install invoke==2.0.0 django-environ --user
    $ inv docker-up

This will deploy EJ using **docker/docker-compose.yml** file.
Every code change will be synchronized with `docker_server` container. After `inv docker-up`, you can access EJ on `http://localhost:8000` url.

If you are creating a clean instance, you can populate the database with some fake data:

    $ inv docker-exec "inv db-fake"

Alternatively, if you wish to clean your database and repopulate it using the
script, you'll need to remove `docker_backups` volume.  After that, run `inv docker-up` command and then
`inv docker-exec "inv db-fake"`, as mentioned previously.

To rebuild the server image, you can run `inv docker-build --no-cache`.

Some useful commands to manage docker environment:

| Command           | Description                                      |
|-------------------|--------------------------------------------------|
| inv docker-up     | Creates EJ containers and run the application    |
| inv docker-build  | Builds EJ server Docker image                    |
| inv docker-logs   | Shows django logs                                |
| inv docker-stop   | Stops EJ containers                              |
| inv docker-rm     | Removes EJ containers                            |
| inv docker-attach | Connects to django container                     |
| inv docker-exec   | Executes a shell command inside django container |

Some useful commands to manage the application **(run this inside django container)**:

| Command          | Description                                                    |
| ---------------- | -------------------------------------------------------------- |
| inv i18n         | Extracts messages from Jinja templates for translation         |
| inv i18n -c      | Compile .po files                                              |
| inv sass         | Compile .sass files for all EJ apps.                           |
| inv sass --watch | Watch changes on code, and compile .sass files for all EJ apps |
| inv collect      | Moves compiled files (css, js) to Django static folder         |
| inv db           | Prepare database and run migrations                            |
| inv shell        | Executs django shell with ipython                              |
| inv db           | Prepare database and run migrations                            |
| inv docs         | Compile .rst documentation to generates .html files            |


## Tests

If you are making changes to EJ codebase, do not forget to run tests frequently.
EJ uses Pytest_:

    $ inv docker-test

Beyond unit and integration tests, EJ also has e2e tests implemented with [Cypress](https://www.cypress.io/).
Check `src/ej/tests/e2e/README.md` for more informations.

## Documentation

After configuring local environment, the next step is reading our documentation. It can be generated with:

    $ inv docker-exec "inv docs"

and will be available at the [http://localhost:8000/docs](http://localhost:8000/docs) url.
