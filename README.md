# Share Link - 셰어 링크

Another '[shaarli](https://sebsauvage.net/wiki/doku.php?id=php:shaarli)' made with [FastAPI](https://fastapi.tiangolo.com/)

I rewrote [shaarpy](https://github.com/foxmask/shaarpy/) I coded with Django

# Install

## :package: Installation

### Requirements

* Python from 3.10+
* FastApi
* Pandoc

### Installation

system requirement : pandoc

```bash
sudo apt install pandoc
```

create a virtualenv

```bash
python3 -m venv sharelink
cd sharelink
source bin/activate
```

install the project

```bash
git clone https://github.com/foxmask/sharelink.git
cd sharelink
pip install -r requirements.txt
```

##  :wrench: Settings

To set your own ShareLink customisation, create a `.env`  file, and change thoses default values

```bash
DATABASE_URL="sqlite:///db.sqlite3"
LANGUAGE_CODE="fr-fr"

# SHARELINK variables
SHARELINK_NAME="ShareLink - 셰어 링크"
SHARELINK_AUTHOR="FoxMaSk"
SHARELINK_DESCRIPTION="Share link, thoughts, ideas and more"

# ALLOW ROBOT to index the content of the website
SHARELINK_ROBOT="index, follow"
SHARELINK_URL="http://localhost:8000"
SHARELINK_TZ="Europe/Paris"
# APP Pagination
LINKS_PER_PAGE=5
DAILY_PER_PAGE=10

# CSRF
SECRET_KEY="itsuptousofcourse"
COOKIE_SAMESITE="none"
COOKIE_SECURE=True
TOKEN_LOCATION="body"
TOKEN_KEY="csrf-token"
CSRF_TRUSTED_ORIGINS="http://127.0.0.1:8000,http://localhost:8000,http://127.0.0.1"

# TRUSTED HOST
ALLOWED_HOST="127.0.0.1:8000,localhost:8000,127.0.0.1,localhost"

```

## :mega: Running the Server

### start the project

```bash
fastapi run main.py
```

then, access the project with your browser http://127.0.0.1:8000/


## Test

```
python -m pytest sharelink/tests/
```

or

```
tox -r
```