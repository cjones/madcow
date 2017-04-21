# This file is exec'd from settings.py, so it has access to and can
# modify all the variables in settings.py.

DEBUG = True

# Make these unique, and don't share it with anybody.
SECRET_KEY = "(1rw=+w%@$6=dimny0fuog**k03j&+qq+k)g#&w)jw@be-()@x"
NEVERCACHE_KEY = "jti0yeil*zmw1!jkh(v9&%s!b#c@eku_6#=mu+fixgf_=3^xbd"

DATABASES = {
    "default": {
        # Ends with "postgresql_psycopg2", "mysql", "sqlite3" or "oracle".
        "ENGINE": "django.db.backends.sqlite3",
        # DB name or path to database file if using sqlite3.
        "NAME": "dev.db",
        # Not used with sqlite3.
        "USER": "",
        # Not used with sqlite3.
        "PASSWORD": "",
        # Set to empty string for localhost. Not used with sqlite3.
        "HOST": "",
        # Set to empty string for default. Not used with sqlite3.
        "PORT": "",
    }
}

###################
# DEPLOY SETTINGS #
###################

# Domains for public site
ALLOWED_HOSTS = ["*"]

