import os

FRONTENDS = (
    'ams-1.a.desec.io',
    'dfw-1.a.desec.io',
    'fra-1.a.desec.io',
    'hkg-1.a.desec.io',
    'jnb-1.a.desec.io',
    'sao-1.a.desec.io',
    'syd-1.a.desec.io',

    'dxb-1.c.desec.io',
    'fra-1.c.desec.io',
    'lax-1.c.desec.io',
    'lga-1.c.desec.io',
    'lhr-1.c.desec.io',
    'scl-1.c.desec.io',
    'sin-1.c.desec.io',
    'tyo-1.c.desec.io',
)

HOSTNAME_DISPLAY_TRIM = 7

DNS_REQUEST_TIMEOUT = 2.0

DESEC_TOKEN = os.getenv('DESEC_TOKEN')
assert DESEC_TOKEN

DESEC_DOMAIN = os.getenv('DESEC_DOMAIN')
assert DESEC_DOMAIN

DESEC_SUBNAME = os.getenv('DESEC_SUBNAME')
assert DESEC_SUBNAME
