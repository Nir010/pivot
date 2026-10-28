# Pivot Risk — Deployment Guide

A complete, step-by-step guide to putting the Django backend on a fresh Ubuntu
VPS and serving it at `https://pivotrisks.com`.

- Repo: `https://github.com/Nir010/pivot.git` (branch `work`)
- Values written like `this-placeholder` must be replaced with your real values.
- **Never** commit real secrets (`.env`) or uploaded files (`media/`).

---

## How the site fits together

Before touching the server it helps to know who does what. Each request flows
through the pieces below:

```text
Browser ──HTTPS──▶ Nginx (:443)
                     ├── /static/  ──▶ /var/www/pivot/staticfiles/   (CSS/JS/images)
                     ├── /media/   ──▶ /var/www/pivot/media/        (photos, PDFs)
                     └── everything else ──▶ Gunicorn (127.0.0.1:8000)
                                                └──▶ Django ──▶ PostgreSQL
```

| Piece | Role |
|-------|------|
| **Nginx** | Public web server. Terminates HTTPS, serves static/media directly (fast), and forwards dynamic requests to Gunicorn. |
| **Gunicorn** | Runs the Django application. Fewer, long-lived worker processes (not `runserver`). |
| **Django / WhiteNoise** | Application logic; WhiteNoise is a fallback that can also serve static files. |
| **PostgreSQL** | Stores all content (team, services, projects, blog, notices, messages). |
| **systemd** | Keeps Gunicorn running and restarts it after reboots or crashes. |

### Prerequisites (do these before starting)

1. A VPS (Ubuntu 22.04/24.04) with a public IP and `sudo` access.
2. Your domain's DNS **A records** for `pivotrisks.com` **and**
   `www.pivotrisks.com` pointing at that IP (needed for the SSL step).
3. A local working copy of this repo with the content already entered in the
   admin — you will copy that content up in step 7.

---

## What has to travel (read this first)

Different kinds of things reach the server in different ways. Forgetting one is
the usual cause of a "half-deployed" site: code is new but content is empty, or
content is there but images are broken.

| Kind of thing | Examples | How it reaches the server |
|---------------|----------|---------------------------|
| Code | models, views, templates, migrations | `git pull` |
| Python packages | `requirements.txt` | `pip install -r requirements.txt` |
| Static files | `css/`, `js/`, `images/` | `collectstatic` |
| Media | team photos, blog covers, PDFs | `scp` (step 7a) **or** admin upload |
| Secrets | `.env` | written by hand on the server |
| **Database content** | team, services, projects, blog, notices, socials, contact messages | **DB dump / fixtures (step 7b)** |
| Database schema + defaults | tables + seeded services/team | `migrate` |

`.env` and `media/` are gitignored, so they never travel through git.

> **Important:** `migrate` only creates the tables and seeds the **default**
> services and team (via data migrations). It does **not** recreate the team
> members, projects, blog posts, notices, social links or contact messages you
> add later in the admin. Those live in the database and must be copied in
> step 7b, or the fresh server will look empty.

---

## 1. Server basics (Ubuntu)

Update the package list, apply security updates, and install everything the
stack needs.

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip postgresql nginx git
```

| Package | Why it's needed |
|---------|-----------------|
| `python3-venv` | create the isolated virtual environment for the project |
| `python3-pip` | install packages inside that environment |
| `postgresql` | the database server |
| `nginx` | the public web server / reverse proxy |
| `git` | pull the code onto the server |

Create a dedicated non-root user to own and run the app (running as `root` is an
unnecessary security risk):

```bash
sudo adduser deployer
sudo usermod -aG sudo deployer
```

Turn on the firewall, allowing only SSH and web traffic:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

`ufw allow 'Nginx Full'` opens ports 80 (HTTP) and 443 (HTTPS). `OpenSSH` keeps
your SSH session working. Confirm with `sudo ufw status`.

---

## 2. Get the code

Download the repository and give the `deployer` user ownership of it.

```bash
cd /var/www
sudo git clone https://github.com/Nir010/pivot.git pivot
cd /var/www/pivot
sudo git checkout work
sudo chown -R deployer:deployer /var/www/pivot
```

- `/var/www` is the conventional home for web projects.
- The `work` branch holds the Django backend (the `main` branch is the separate
  static site).
- `chown` is required because `git clone` ran as `root`; the app must be
  owned/writable by `deployer`.

Switch to the app user for every remaining step:

```bash
su - deployer
cd /var/www/pivot
```

---

## 3. Virtualenv + packages

Create an isolated Python environment and install the pinned dependencies. A
virtual environment keeps this project's packages separate from the system
Python.

```bash
cd /var/www/pivot
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

- `source .venv/bin/activate` puts `.venv/bin` first on your `PATH`, so `python`
  and `pip` refer to the environment. Your prompt shows `(.venv)` when active.
- `requirements.txt` already includes `gunicorn` (app server) and `whitenoise`
  (static files), so there is nothing extra to install.
- If you ever log out, re-activate with `source .venv/bin/activate`.

---

## 4. PostgreSQL — database + app role

Create a dedicated, least-privilege role for the app. **Do not** run Django as
the `postgres` superuser — if the app is compromised, the role can only touch
its own database.

```bash
sudo -u postgres psql
```

Then run these statements:

```sql
CREATE USER pivot_user WITH PASSWORD 'strong-app-password';
CREATE DATABASE pivot OWNER pivot_user;
ALTER ROLE pivot_user SET client_encoding TO 'utf8';
ALTER ROLE pivot_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE pivot_user SET timezone TO 'Asia/Kathmandu';

-- PostgreSQL 15 and newer: the public schema needs an explicit grant.
\c pivot
GRANT ALL ON SCHEMA public TO pivot_user;
\q
```

> **Least privilege:** `pivot_user` owns `pivot` and has `ALL` on `public`. It
> should have **no superuser** and **no** access to other databases. If you ever
> need to rotate the password, do it here and update `.env`.

| Statement | What it does |
|-----------|--------------|
| `CREATE USER ...` | creates the login role the Django app will use |
| `CREATE DATABASE ... OWNER ...` | creates the `pivot` database owned by that role |
| `ALTER ROLE ... client_encoding` | ensures UTF-8 (safe text storage) |
| `ALTER ROLE ... transaction_isolation` | Django's expected isolation level |
| `ALTER ROLE ... timezone` | server-side timezone for the database |
| `GRANT ALL ON SCHEMA public` | lets the role create tables (required on PG 15+) |
| `\c pivot` | connect to the new database before granting |
| `\q` | leave `psql` |

> `strong-app-password` must match `DB_PASSWORD` in `.env` (step 5). Use a real,
> random password.

---

## 5. Production `.env`

Create `/var/www/pivot/.env`. This file holds all environment-specific settings
and secrets, and is loaded by `python-dotenv` in `settings.py`.

```bash
DJANGO_DEBUG=False
ALLOWED_HOSTS=pivotrisks.com,www.pivotrisks.com
SITE_URL=https://pivotrisks.com
SECRET_KEY=YOUR_SECRET_KEY
DB_NAME=pivot
DB_USER=pivot_user
DB_PASSWORD=strong-app-password
DB_HOST=127.0.0.1
DB_PORT=5432
TIME_ZONE=Asia/Kathmandu
```

| Variable | Meaning |
|----------|---------|
| `DJANGO_DEBUG` | `False` in production. Turns off debug pages and enables HTTPS/HSTS/secure cookies. |
| `ALLOWED_HOSTS` | Comma-separated domains Django will answer for (blocks Host-header attacks). |
| `SITE_URL` | Public canonical site origin, without a trailing slash; used by SEO metadata, sitemap, and robots.txt. |
| `SECRET_KEY` | Cryptographic key for sessions/CSRF. Must be secret and unique. |
| `DB_*` | PostgreSQL connection details (must match step 4). |
| `TIME_ZONE` | Server-side timezone used by Django. |

Generate a fresh secret key:

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Restrict the file so only its owner can read it:

```bash
chmod 600 /var/www/pivot/.env
```

> With `DJANGO_DEBUG=False`, Django forces HTTPS (`SECURE_SSL_REDIRECT`) and sets
> secure cookies and HSTS. That is why the SSL step (11) and the Nginx
> `X-Forwarded-Proto` header (step 10) are mandatory — without them you can get a
> redirect loop or a 400 error.

---

## 6. Migrate + static + superuser

Build the database schema, gather static files, and create your admin account.

```bash
cd /var/www/pivot
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

| Command | What it does |
|---------|--------------|
| `migrate` | Creates all database tables and runs data migrations that seed the **default** services/team. |
| `collectstatic` | Copies `css/`, `js/`, `images/` into `staticfiles/` for Nginx to serve. |
| `createsuperuser` | Prompts for an admin username/email/password for `/admin/`. |

> `migrate` does **not** restore content you added later in the admin. That is
> step 7b.

---

## 7. Bring your content across (media + database)

This is the step that is most often skipped, and the reason a new deployment can
look empty. Do **both** 7a and 7b.

### 7a. Media files (photos, PDFs) — NOT via git

Uploaded files live in `media/`, which is gitignored. Copy it from your laptop:

```bash
cd /path/to/pivot
scp -r media/ deployer@SERVER_IP:/var/www/pivot/media/
```

- `scp -r` copies the folder recursively over SSH.
- Alternatively, re-upload the files once through the admin after deploy — the
  result is the same.

### 7b. Database content — NOT via git or migrate

Everything entered through the admin lives in the database. Choose **one** option.
Both copy **all admin-entered content**: team, services, projects, blog posts,
notices, social links, site settings and contact messages.

#### Option A — full database copy (also carries admin logins)

This copies the entire database, schema and data, in one shot.

On your laptop (the dev database is named `pivot`; change it if yours differs):

```bash
pg_dump --no-owner pivot > pivot_dev.sql
scp pivot_dev.sql deployer@SERVER_IP:/var/www/pivot/
```

- `pg_dump` writes a plain-SQL snapshot of the database.
- `--no-owner` omits ownership commands so the restore works as any role.

On the server, rebuild the database from that dump:

```bash
sudo -u postgres dropdb --if-exists pivot
sudo -u postgres createdb -O pivot_user pivot
PGPASSWORD='strong-app-password' psql -h 127.0.0.1 -U pivot_user -d pivot \
    < /var/www/pivot/pivot_dev.sql

cd /var/www/pivot
source .venv/bin/activate
python manage.py migrate              # apply migrations newer than the dump
python manage.py collectstatic --noinput
rm /var/www/pivot/pivot_dev.sql       # remove the dump — it contains data
```

- `dropdb`/`createdb` wipe the half-empty database from step 6 and recreate it,
  so there is no clash between the dump's schema and the existing one.
- `psql ... < dump` replays the snapshot as `pivot_user`.
- `migrate` afterwards applies any migrations added since the dump was taken.
- **Your admin users come with the dump**, so `createsuperuser` is not needed in
  this option.

#### Option B — content only via fixtures (no users/passwords)

This copies just the content rows and leaves users/credentials behind.

On your laptop:

```bash
.venv/bin/python manage.py dumpdata home blog projects --indent 2 -o content.json
scp content.json deployer@SERVER_IP:/var/www/pivot/
```

- `dumpdata home blog projects` exports every content model (see the appendix).
- It deliberately excludes `auth`/users, so no passwords travel.

On the server, after step 6:

```bash
cd /var/www/pivot
source .venv/bin/activate
python manage.py loaddata content.json
```

- `loaddata` reads the JSON back into the database.
- No users are loaded — run `createsuperuser` (step 6) if you haven't.
- If you get duplicate-key errors because the default seeds already exist, run
  `python manage.py flush --noinput`, then `loaddata content.json`, then
  `createsuperuser` again.
- Fixtures store only the **file paths** of images/PDFs — the actual files must
  already be in `media/` (step 7a).
- If you develop on SQLite, copying `db.sqlite3` will **not** work on PostgreSQL.
  Use Option B.

#### Verify the content arrived

```bash
python manage.py shell -c "
from home.models import TeamMember, Service, Notice, SocialLink, ContactMessage
from blog.models import Post
from projects.models import Project
print('team', TeamMember.objects.count())
print('services', Service.objects.count())
print('notices', Notice.objects.count())
print('socials', SocialLink.objects.count())
print('messages', ContactMessage.objects.count())
print('posts', Post.objects.count())
print('projects', Project.objects.count())
"
```

Each number should match your dev site. If a count is `0`, the content did not
transfer — re-check 7b.

---

## 8. Test Django directly (before wiring the web server)

Run Django's built-in server to confirm the app and database work, *before*
adding Gunicorn and Nginx.

> Production `.env` has `DJANGO_DEBUG=False`, so the app forces HTTPS and only
> trusts the real domains. Testing the bare IP would 400/redirect. Temporarily
> relax it to prove the app runs:

```bash
# edit /var/www/pivot/.env — temporary, for this test only
DJANGO_DEBUG=True
ALLOWED_HOSTS=pivotrisks.com,www.pivotrisks.com,SERVER_IP
```

```bash
cd /var/www/pivot
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

Open `http://SERVER_IP:8000/` and check that pages, images and the notice popup
all appear. `runserver` is for testing only — never use it in production.

Then **restore the real `.env`** (`DJANGO_DEBUG=False`) and stop the server with
Ctrl+C before continuing.

---

## 9. Gunicorn (production app server)

Run Django under Gunicorn, supervised by systemd so it starts on boot and
restarts after crashes.

Create `/etc/systemd/system/pivot.service`:

```ini
[Unit]
Description=Pivot Django app via Gunicorn
After=network.target

[Service]
User=deployer
Group=www-data
WorkingDirectory=/var/www/pivot
ExecStart=/var/www/pivot/.venv/bin/gunicorn pivot.wsgi:application \
    --bind 127.0.0.1:8000 --workers 3 --timeout 60
Restart=always

[Install]
WantedBy=multi-user.target
```

| Setting | Meaning |
|---------|---------|
| `User` / `Group` | run as `deployer`, grouped with the web server |
| `WorkingDirectory` | so Django can find `manage.py` and `.env` |
| `--bind 127.0.0.1:8000` | listen on localhost only; Nginx is the public face |
| `--workers 3` | handle three requests at once (a common default: 2×CPU+1) |
| `--timeout 60` | allow slow requests/upload processing |
| `Restart=always` | auto-restart on crash |

Enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable pivot
sudo systemctl start pivot
sudo systemctl status pivot
```

- `daemon-reload` re-reads the new unit file.
- `enable` makes it start automatically on boot.
- `status` should show `active (running)`. If not, inspect logs with
  `journalctl -u pivot -e`.

---

## 10. Nginx — gateway + static/media

Nginx is the public server. It serves static/media files and proxies everything
else to Gunicorn.

Create `/etc/nginx/sites-available/pivot`:

```nginx
server {
    listen 80;
    server_name pivotrisks.com www.pivotrisks.com;

    client_max_body_size 25M;   # allow photo / PDF uploads

    location /static/ {
        alias /var/www/pivot/staticfiles/;
    }

    location /media/ {
        alias /var/www/pivot/media/;   # Django won't serve media in production
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;   # REQUIRED for HTTPS redirect
    }
}
```

| Directive | Meaning |
|-----------|---------|
| `client_max_body_size 25M` | accept uploads up to 25 MB (larger than default 1 MB) |
| `location /static/` | serve collected static files straight from disk |
| `location /media/` | serve uploaded files; Django does not serve them in production |
| `proxy_pass` | send dynamic requests to Gunicorn on localhost |
| `X-Forwarded-Proto` | tells Django whether the original request was HTTPS (needed for `SECURE_SSL_REDIRECT`) |

Activate it and reload:

```bash
sudo ln -s /etc/nginx/sites-available/pivot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

- The `ln -s` enables the site.
- `nginx -t` validates the config before applying (always run it).
- `reload` applies changes with no downtime.

---

## 11. HTTPS (SSL) — free certs

Obtain a free Let's Encrypt certificate and let Certbot rewrite the Nginx config
for TLS (and set up auto-renewal):

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d pivotrisks.com -d www.pivotrisks.com
```

- Your DNS A records must already point at the server, or issuance fails.
- Certbot adds the `listen 443 ssl` block and the HTTP→HTTPS redirect.
- Renewal is automatic; test it any time with `sudo certbot renew --dry-run`.

---

## 12. Backups (do this regularly)

Back up the database and uploaded media. Keep backups **off the server** if
possible (copy to another machine/object storage). Only ever dump as
`pivot_user` (not as `postgres`).

Store the DB password for non-interactive dumps:

```bash
echo '127.0.0.1:5432:pivot:pivot_user:strong-app-password' > ~/.pgpass
chmod 600 ~/.pgpass
```

Create a backup folder and schedule daily jobs:

```bash
sudo mkdir -p /var/backups/pivot
crontab -e
```

Add these lines:

```cron
# Daily DB dump at 03:00
0 3 * * * pg_dump -h 127.0.0.1 -U pivot_user pivot | gzip > /var/backups/pivot/db_$(date +\%F).sql.gz
# Daily media sync at 04:00
0 4 * * * rsync -a /var/www/pivot/media/ /var/backups/pivot/media/
```

> **Tips:** test a restore on a throwaway database regularly. If you need a full
> off-server copy, `scp`/`rsync` the gzipped dump and the media folder. Keep
> `.pgpass` readable only by the `deployer` user.

- `~/.pgpass` lets `pg_dump` authenticate without a password prompt (format:
  host:port:database:user:password). Keep it `chmod 600`.
- The first cron line dumps the database nightly and gzips it.
- The second mirrors uploaded media.
- Copy `/var/backups/pivot/` off the server (another machine or object storage)
  for real disaster recovery.

---

## 13. Updating the live site later

After you push new commits from your laptop, run on the server:

```bash
cd /var/www/pivot
source .venv/bin/activate
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart pivot
```

| Step | Purpose |
|------|---------|
| `git pull` | fetch the new code |
| `pip install -r requirements.txt` | install any new/changed packages |
| `migrate` | apply new database migrations |
| `collectstatic` | refresh static files |
| `restart pivot` | load the new code into Gunicorn |

Additional cases:

- New/changed **images or PDFs** → re-run step 7a.
- New/changed **admin content** to copy to another environment → re-run step 7b.
- Changed Nginx/systemd config → `sudo nginx -t && sudo systemctl reload nginx`
  and `sudo systemctl daemon-reload && sudo systemctl restart pivot`.

---

## 14. Post-deploy sanity checks

```bash
# On the server:
cd /var/www/pivot && source .venv/bin/activate
python manage.py check --deploy        # fix any reported warnings

# From your laptop:
curl -I https://pivotrisks.com         # expect 200 OK (and an HTTPS redirect from http)
```

Go through this list:

- [ ] Site loads over HTTPS
- [ ] CSS / JS / images load (`collectstatic` worked)
- [ ] Team photos, blog covers and PDFs show (`media/` transferred)
- [ ] Team / services / projects / blog / notices match dev (step 7b)
- [ ] Admin login works (`/admin/`)
- [ ] Contact form saves messages (admin → Contact messages)
- [ ] Important-notice popup appears on the home page
- [ ] Editing Site Settings in the admin updates the site

---

## 15. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `400 Bad Request` / `DisallowedHost` | Host not in `ALLOWED_HOSTS` | add the domain to `.env`, `sudo systemctl restart pivot` |
| Redirect loop / "too many redirects" | Nginx missing `X-Forwarded-Proto` | add the header (step 10), reload Nginx |
| `502 Bad Gateway` | Gunicorn down | `sudo systemctl status pivot`; `journalctl -u pivot -e` |
| Static files 404 | `collectstatic` not run / wrong alias | rerun `collectstatic`; check `/static/` alias |
| Media 403/404 | wrong alias or file permissions | check `/media/` alias; ensure `deployer` can read files |
| `could not connect to server` (psycopg) | Postgres down / wrong host/port | `sudo systemctl status postgresql`; check `.env` |
| Content missing after deploy | step 7b skipped | run Option A or B, then verify |
| Broken images after fixtures | `media/` not copied | run step 7a |
| `SSL_ERROR` / cert not issued | DNS not pointing at server | fix A records, rerun `certbot` |

Useful log commands:

```bash
sudo journalctl -u pivot -e      # application/Gunicorn logs
sudo tail -f /var/log/nginx/error.log   # Nginx errors
```

---

## Appendix — what "content" means (all copied in step 7b)

| App | Models |
|-----|--------|
| `home` | `SiteSettings`, `TeamMember`, `Service`, `Notice`, `SocialLink`, `ContactMessage` |
| `blog` | `Category`, `Post` |
| `projects` | `ProjectCategory`, `Project`, `ProjectImage` |

`dumpdata home blog projects` captures every one of these, so Option B copies all
admin-entered content. Option A copies the whole database on top of that.
