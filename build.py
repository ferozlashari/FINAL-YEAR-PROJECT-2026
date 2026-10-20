"""Vercel build step.

1. collectstatic  - so WhiteNoise can serve /static/ even if the CDN step is skipped.
2. (optional) migrate + seed_roles against the production database when
   VERCEL_RUN_MIGRATIONS=1. Leave it off if you prefer to run migrations by hand.
"""
import os
import subprocess
import sys


def run(*args):
    print('>>', ' '.join(args), flush=True)
    subprocess.run([sys.executable, 'manage.py', *args], check=True)


def main():
    run('collectstatic', '--noinput')
    if os.environ.get('VERCEL_RUN_MIGRATIONS') == '1':
        if not os.environ.get('DATABASE_URL'):
            sys.exit('VERCEL_RUN_MIGRATIONS=1 but DATABASE_URL is not set.')
        run('migrate', '--noinput')
        run('seed_roles')
    else:
        print('Skipping migrations (set VERCEL_RUN_MIGRATIONS=1 to run them during the build).')


if __name__ == '__main__':
    main()
