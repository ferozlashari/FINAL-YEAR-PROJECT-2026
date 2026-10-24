"""Vercel build step.

1. collectstatic  - so WhiteNoise can serve /static/ even if the CDN step is skipped.
2. (optional) migrate + seed_roles against the production database when
   RUN_MIGRATIONS=1 (or VERCEL_RUN_MIGRATIONS=1). Leave it off if you prefer to run migrations by hand.
"""
import os
import subprocess
import sys


def run(*args):
    print('>>', ' '.join(args), flush=True)
    subprocess.run([sys.executable, 'manage.py', *args], check=True)


def create_first_admin():
    """Create the first System Administrator from Vercel environment variables.

    Needs DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD (and optionally
    DJANGO_SUPERUSER_EMAIL). Safe to run on every deploy: an existing user is left
    untouched. Remove the PASSWORD variable from Vercel after the first login.
    """
    if not (os.environ.get('DJANGO_SUPERUSER_USERNAME') and os.environ.get('DJANGO_SUPERUSER_PASSWORD')):
        print('No DJANGO_SUPERUSER_* variables set: skipping first-admin creation.')
        return
    print('>> createsuperuser --noinput (existing users are left untouched)', flush=True)
    result = subprocess.run([sys.executable, 'manage.py', 'createsuperuser', '--noinput'],
                            capture_output=True, text=True)
    out = (result.stdout + result.stderr).strip()
    if result.returncode == 0:
        print('First administrator created.')
    elif 'already taken' in out or 'already exists' in out:
        print('Administrator already exists: nothing changed.')
    else:
        print(out[-600:])
        sys.exit('Could not create the first administrator.')


def main():
    run('collectstatic', '--noinput')
    # Accept RUN_MIGRATIONS=1 (standard) or VERCEL_RUN_MIGRATIONS=1
    if os.environ.get('RUN_MIGRATIONS') == '1' or os.environ.get('VERCEL_RUN_MIGRATIONS') == '1':
        if not os.environ.get('DATABASE_URL'):
            sys.exit('RUN_MIGRATIONS=1 is set, but DATABASE_URL is missing.')
        run('migrate', '--noinput')
        run('seed_roles')
        create_first_admin()
    else:
        print('Skipping migrations (set RUN_MIGRATIONS=1 to run them during the build).')


if __name__ == '__main__':
    main()
