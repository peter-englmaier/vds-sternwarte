# Install python environment

We can use `pyenv` to install specific python versions and setup a python environment for the python application folder.

First, install some requirements for python
```shell
sudo apt install libreadline-dev libsqlite3-dev tk-dev
```

And install [pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#linuxunix)

```shell
sudo apt install pyenv
```

Setup shell for pyenv

```shell
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init - bash)"' >> ~/.bashrc
source ~/.bashrc
```

Next, restart your shell and install python version required, see [python versions](https://www.python.org/downloads/)

```shell
pyenv install 3.14
```

Create your virtual environment as usual, i.e.:

```shell
$ pyenv local 3.14
$ python --version
Python 3.14.3
$ python -m venv venv
$ source venv/bin/activate
$ pip install --upgrade pip
$ pip install -r requirements.txt
```

# Update python version

To update python version:

```shell
$ pyenv install 3.14
$ cat .python-version 
3.14
$ python --version
Python 3.14.10
```

To update the python environment, remove the venv folder and start again.

```shell
$ rm -fr venv
$ python -m venv venv
$ source venv/bin/activate
$ pip install --upgrade pip
$ pip install -r requirements.txt
```
