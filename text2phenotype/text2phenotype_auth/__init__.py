import os
import sys


if 'setup.py' in sys.argv and 'test' in sys.argv:
    from django.core.management.utils import get_random_secret_key

    from text2phenotype.constants.environment import Environment

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "text2phenotype.text2phenotype_auth.settings")
    os.environ.setdefault("MDL_COMN_DJANGO_SECRET_KEY", get_random_secret_key())

    Environment.load()
