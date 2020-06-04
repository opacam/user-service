# user-service

[![CI](https://github.com/opacam/user-service/workflows/CI/badge.svg?branch=develop)](https://github.com/opacam/user-service/actions/)
[![codecov](https://codecov.io/gh/opacam/user-service/branch/develop/graph/badge.svg?token=Mh57rCB7hI)](https://codecov.io/gh/opacam/user-service)
[![Python versions](https://img.shields.io/badge/Python-3.6+-brightgreen.svg?style=flat)](https://www.python.org/downloads/)
[![GitHub release](https://img.shields.io/github/release/opacam/user-service.svg)](https://gitHub.com/opacam/user-service/releases/)
[![GitHub tag](https://img.shields.io/github/tag/opacam/user-service.svg)](https://gitHub.com/opacam/user-service/tags/)
[![GitHub license](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/opacam/user-service/blob/develop/LICENSE.md)


A **RESTful** API to manage users accounts which registers all user
calls to the API. This API has been wrote thinking in microservices, so
it should be extended to store user preferences defined by the frontend
app.

It implements several endpoints, most of them only available for
authenticated users. It basically allows you to create an account via an
username and a password and from that point on, it will register all the
user queries to the API. All this `user actions` can be consulted by the
owner of the account and also we provide endpoints to retrieve histograms
where we collect all users data.

You can test/explore the API functionality with the deployed demo
app at [heroku](https://ms-user-service.herokuapp.com/):

- [swagger-ui](https://ms-user-service.herokuapp.com/docs): you can
  interact with the API as well as read the API docs.
- [ReDoc](https://ms-user-service.herokuapp.com/redoc): Or if you prefer
  ...in `ReDoc` format.


**Road map:**

- extend/enhance the documentation
- extend the API to support store user preferences (tied to the target
  frontend app, but we could store some user preferences regarding the
  user API queries...like default period for histogram or the preferred
  sorting order for the user API calls)
- add support for `PostgreSQL` database (our default is sqlite3)


*This project has been made with Python 3, FastAPI and love*

## Getting Started

These instructions will get you a copy of the project up and running on your
local machine for development and testing purposes. See deployment for notes on
how to deploy the project on a live system.

### Prerequisites

You also need python >= 3.6 up and running. If you OS does not have the
appropriate python version, you could install [pyenv](https://github.com/pyenv/pyenv) 
and create a virtual environment with the proper python version. Also you will
need an up to date pip installation (version `20.1.1` or greater is our
recommendation). So once you have `pyenv` installed
(see [pyenv install instructions](https://github.com/pyenv/pyenv#installation)), 
make an virtual environment for the project (we will use python version 3.8):

```
pyenv virtualenv 3.8.1 user-service
```

Enter inside the python environment we recently created (`user-service`):
```
pyenv activate user-service
```

Upgrade `pip/setuptools` packages:
```
pip install --upgrade pip
pip install --upgrade setuptools
```

Install `poetry` package:
```
pip install poetry
```

### Installing

Once you have the prerequisites installed, you can proceed installing the
project. The project uses an `pyproject.toml` file to manage the installation
(PEP517) and also we will make use of the python package
[poetry](https://github.com/python-poetry/poetry) as our `build-system`
(PEP518):

Run the install of the dependencies via `poetry` command:

```
poetry install
```


## Running the tests

To run our project tests you can use `pytest` with coverage:

```
PYTHONPATH=. pytest --cov app/
```


## Running the server

To run our project you should enter to the `user-service` directory:

```
PYTHONPATH=. uvicorn app.main:app --reload
```

Then you can access the app from http://127.0.0.1:8000. To access the
documentation, head over to http://127.0.0.1:8000/docs.

## Docker

This project can be used via docker, the following sections describes
the build/run/stop instructions.

### Build image

You can build the docker image with the command:

```
docker build -t user-service:latest ./
```

### Run image

To run the image, use command:

```
docker run -d --name ms-user-service -p 80:80 user-service
```

---
**NOTE**

To run docker image in a testing machine, you may need to map ports
differently:

```
docker run -d --name ms-user-service -p 5000:80 user-service
```

---

### Stop Docker container

To stop the docker container:

```
docker stop ms-user-service
```

## Built With

* [Python 3](https://docs.python.org/3/) - The programming language
* [FastAPI](https://fastapi.tiangolo.com/) - FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints.
* [Poetry](https://python-poetry.org/docs/) - Dependency Management

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of
conduct, and the process for submitting pull requests to us.

## Versioning

We use [CalVer](https://calver.org/) for versioning. For the versions available,
see the [tags on this repository](https://github.com/opacam/user-service/tags).


## Authors

* **Pol Canelles** - *Initial API work* - [opacam](https://github.com/opacam)

See also the list of [contributors](https://github.com/opacam/user-service/contributors)
who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* [FastAPI Docs](https://fastapi.tiangolo.com/)
* [Developing and Testing an Asynchronous API with FastAPI and Pytest](https://testdriven.io/blog/fastapi-crud/)
* [Microservice in Python using FastAPI](https://dev.to/paurakhsharma/microservice-in-python-using-fastapi-24cc)
