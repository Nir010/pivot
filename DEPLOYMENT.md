# Pivot Risk — Deployment Checklist

Steps to deploy the Django site on a production VPS
(Ubuntu + PostgreSQL + Nginx + Gunicorn).

> Values in `like-this` are placeholders. Replace them with real ones.
> Never put real passwords in this file.

---

## 0. From your laptop, once

Commit everything except secrets:

```bash
git add -A
git commit -m "deploy: initial production config"
git push
```

Because `.env` and `media/` are gitignored, they never travel via git.
You transfer them manually (steps 3 and 7).

---

## 1. Server basics (Ubuntu)

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip postgresql nginx git
```

Create a non-root user for the app (recommended):

```bash
sudo adduser deployer
sudo usermod -aG sudo deployer
```

---

## 2. Get the code

```bash
cd /var/www
sudo git clone https://github.com/YOUR_USER/Company_tem.git pivot
sudo chown -R deployer:deployer /var/www/pivot
```

---

## 3. Environment file (secrets live on the server, not in git)

Create `/var/www/pivot/.env`:

```bash
DEBUG=False
ALLOWED_HOSTS=pivotrisk.com.np,www.pivotrisk.com.np
SECRET_KEY=generate-a-long-random-string
DB_NAME=pivot
DB_USER=postgres
DB_PASSWORD=strong-postgres-password
DB_HOST=127.0.0.1
DB_PORT=5432
TIME_ZONE=UTC
```

Generate the secret key with:

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 4. Virtualenv + packages

```bash
cd /var/www/pivot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

---

## 5. PostgreSQL database

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE pivot OWNER postgres;
ALTER USER postgres PASSWORD 'strong-postgres-password';
\q
```

---

## 6. Migrate + static + superuser

```bash
cd /var/www/pivot
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

- `migrate` builds tables **and** seeds the services + team (your data
  migrations).
- `collectstatic` copies `css/`, `js/`, `images/` into `staticfiles/`.

---

## 7. Upload media (photos, PDFs) — NOT via git

From your laptop:

```bash
scp -r media/ deployer@SERVER_IP:/var/www/pivot/media/
```

(Or upload the files once through the admin instead.)

---

## 8. Test Django directly

```bash
python manage.py runserver 0.0.0.0:8000
```

Open `http://SERVER_IP:8000/` and confirm the site renders.
Stop it (Ctrl+C) before continuing.

---

## 9. Run Django with Gunicorn (production server)

Create `/etc/systemd/system/pivot.service`:

```ini
[Unit]
Description=Pivot Django app via Gunicorn
After=network.target

[Service]
User=deployer
WorkingDirectory=/var/www/pivot
ExecStart=/var/www/pivot/.venv/bin/gunicorn pivot.wsgi:application --bind 127.0.0.1:8000 --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable pivot
sudo systemctl start pivot
sudo systemctl status pivot
```

---

## 10. Nginx — gateway + static/media

Create `/etc/nginx/sites-available/pivot`:

```nginx
server {
    listen 80;
    server_name pivotrisk.com.np www.pivotrisk.com.np;

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
    }
}
```

Activate it:

```bash
sudo ln -s /etc/nginx/sites-available/pivot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 11. SSL (HTTPS) — free certs

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d pivotrisk.com.np -d www.pivotrisk.com.np
```

---

## 12. Backups (do this regularly)

```bash
pg_dump pivot > backup_$(date +%F).sql        # database
rsync -a /var/www/pivot/media/ backup_dir/     # uploaded files
```

---

## 13. Sanity checks after deploy

```bash
# From your laptop:
curl -I https://your-domain.com          # expect 200 OK
python manage.py check --deploy          # on the server, fix all warnings
```

- [ ] Site loads over HTTPS
- [ ] CSS/JS/images load (collectstatic worked)
- [ ] Team photos + blog PDFs show (media transferred)
- [ ] Contact form saves messages (see admin → Contact messages)
- [ ] Important-notice popup works

---

## Remember the three "different worlds"

| Thing | How it gets to the server |
|-------|---------------------------|
| Code (models, templates, migrations, this file) | `git pull` |
| Static files (css/js/images) | `collectstatic` |
| Media (team photos, PDFs) | `scp` or admin upload |
| Secrets (`.env`) | written by hand on the server |
| Database content | `migrate` (creates/seeds) + backups |