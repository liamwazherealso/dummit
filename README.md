# dummit
## ML / DS dockerfile maker

Users of ML/DS docker, especially when cuda is involved, feel the pain of mixing and matching dockerfies until it works. Especially when dependencies are beyond something that can be completed solely through conda/pip.

This app takes in a simple YAML file list and concatenates the listed requirements to create a docker file.

The goal of this project is to create simple dockerfiles from a small range of well used projects. It is not scoped to complete the larger (and ludicrous goal) of a "dockerfile creator from python dependencies". 
## Setup
```sh
# Install dependencies
pipenv install --dev

# Setup pre-commit and pre-push hooks
pipenv run pre-commit install -t pre-commit
pipenv run pre-commit install -t pre-push
```

## Credits
This package was created with Cookiecutter and the [sourcery-ai/python-best-practices-cookiecutter](https://github.com/sourcery-ai/python-best-practices-cookiecutter) project template.

Named after David S. Dummit. 