# Deploying UMS on Vercel (frontend + backend in one project)

UMS is a server-rendered Django project: the pages ("frontend") and the logic ("backend") are the same code, so **one Vercel project** hosts both.
There is no separate React/Next.js frontend to deploy. Vercel runs Django as a single serverless function and serves `/static/` from its CDN.

## What works and what does not on Vercel
| Needs | On Vercel |
|---|---|
| Web pages, login, dashboards, forms, APIs | Works (one WSGI function, max 60 s per request as configured) |
| Database | **Not included.** Use external PostgreSQL (Neon via the Vercel Marketplace, Supabase, ...). SQLite does not work. |
| Uploaded files (photos, documents) | **No persistent disk.** Set `CLOUD_STORAGE_*` (S3-compatible) or uploads are lost. |
| Celery / Redis / built-in scheduler | **Not available.** Scheduled jobs run through Vercel Cron -> `/internal/cron/` (`SCHEDULER_MODE=external`). |
| Cron frequency | Hobby plan: once per day. Pro: more often. For hourly runs on Hobby use a free pinger (cron-job.org) calling the same URL. |
| Cold starts | The first request after idle is slower. |
| Hobby plan terms | Hobby is for personal, non-commercial use: fine for a demo/FYP, not for the live university system. |

## Steps
1. Push the project to GitHub (never commit `.env`, `db.sqlite3`, `.secret_key`).
2. Vercel dashboard -> **Add New -> Project** -> import the repo. Framework: Vercel detects Django from `manage.py`. Root directory = the folder containing `manage.py`.
3. **Storage -> Create Database -> Postgres (Neon)** and connect it to the project. This sets `DATABASE_URL`. Use the *pooled* connection string.
4. Project -> Settings -> Environment Variables (Production):

| Variable | Value |
|---|---|
| `DEBUG` | `0` |
| `DJANGO_SECRET_KEY` | long random string (`python -c "import secrets;print(secrets.token_urlsafe(64))"`) |
| `FIELD_ENCRYPTION_KEY` | `python manage.py generate_encryption_key` - **keep a private backup; never change it later** |
| `SECURE_PROXY_SSL_HEADER` | `1` |
| `SECURE_COOKIES` | `1` |
| `SECURE_SSL_REDIRECT` | `1` (once the site works over HTTPS) |
| `CRON_SECRET` | random string, at least 20 characters (Vercel sends it as `Authorization: Bearer ...` to the cron route) |
| `SCHEDULER_MODE` | `external` (this is also the automatic choice on Vercel) |
| `VERCEL_RUN_MIGRATIONS` | `1` for the first deploy (runs `migrate` + `seed_roles` during the build); remove it afterwards if you prefer manual migrations |
| `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `DEFAULT_FROM_EMAIL` | your mail provider, otherwise no verification/OTP emails are delivered |
| `PUBLIC_BASE_URL` | `https://<your-project>.vercel.app` |
| `CLOUD_STORAGE_*` | S3-compatible bucket for uploads |

   `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` need no manual setting for `*.vercel.app`: the app trusts the host Vercel assigns (`VERCEL_URL`,
   `VERCEL_PROJECT_PRODUCTION_URL`). Add your own domain to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` when you attach one.
5. **Deploy.** The build runs `python build.py` (collectstatic, and migrations if enabled).
6. Create the first administrator (Vercel has no shell): on your computer run
   `vercel env pull .env.local`, load those variables, then `python manage.py createsuperuser`.
   Then follow `docs/PRODUCTION.md` section 4 to create the first office holders.
7. Check `https://<project>.vercel.app/ready/` (database reachable) and log in.

## Cron
`vercel.json` ships a daily schedule (03:00 UTC) calling `GET /internal/cron/`. Because Vercel freezes a function when the response is sent,
the app runs the jobs *inside* that request when it detects Vercel (`SERVERLESS`), bounded by the 60 s function limit.
Jobs are database-locked, so an overlapping or repeated call cannot run one twice.

## Verified locally (October 2026)
Using the same WSGI app that Vercel runs, with `VERCEL=1` and a fresh PostgreSQL database:
`build.py` (collectstatic + 172 migrations + 25 roles) succeeded; `/health/`, `/ready/` and the login page returned 200 for the Vercel hostname;
a forged Host header is refused (400); `/internal/cron/` returned 403 without or with a wrong token and ran all three jobs synchronously with the
correct `Authorization: Bearer` header; `/static/` returned 200.

## NOT verified
An actual Vercel deployment (no Vercel account was available), Vercel's own build step and CDN static handling, `vercel dev`, real Neon pooling and
cold-start timing, SMTP, payments. Treat the first deployment as a test, and keep a `pg_dump` backup (see `docs/PRODUCTION.md`).
