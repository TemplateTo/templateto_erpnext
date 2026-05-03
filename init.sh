#!/bin/bash
# Idempotent first-boot init for the local Frappe v15 / ERPNext dev environment.
# Re-running this script after first boot is a no-op for the parts that completed.

set -e

cd /home/frappe

# 1. Initialise the bench (only first time).
# Frappe v15 supports Python 3.10-3.12. Pin to /usr/bin/python3.11 so we don't
# pick up the pyenv default (which may be 3.14, too new for v15).
if [ ! -d frappe-bench ]; then
  echo ">>> bench init (this takes ~3-5 minutes)..."
  bench init \
    --frappe-branch version-15 \
    --python /usr/bin/python3.11 \
    --skip-redis-config-generation \
    --no-backups \
    frappe-bench
fi

cd /home/frappe/frappe-bench

# 2. Point bench at the docker service hostnames (idempotent — overwrites each run).
echo ">>> Configuring bench for docker service hostnames..."
bench set-config -g db_host mariadb
bench set-config -g db_port 3306
bench set-config -g redis_cache "redis://redis-cache:6379"
bench set-config -g redis_queue "redis://redis-queue:6379"
bench set-config -g redis_socketio "redis://redis-queue:6379"

# 3. Get ERPNext (only first time).
if [ ! -d apps/erpnext ]; then
  echo ">>> bench get-app erpnext (this takes ~2-3 minutes)..."
  bench get-app --branch version-15 erpnext
fi

# 4. Get our templateto_reports app from the mounted volume (only first time).
# `bench get-app` chokes on plain local paths (tries to build a remote URL),
# so we do what it would do manually: copy the source, pip install -e, and
# register the app in sites/apps.txt. We mount the *repo root* (which contains
# pyproject.toml + the templateto_reports/ Python package) and copy the whole
# thing into apps/templateto_reports so pip can install it as an editable package.
# Check by pyproject.toml (the marker that cp succeeded). If a previous run
# half-installed (dir present, pyproject missing) we wipe and redo.
if [ ! -f apps/templateto_reports/pyproject.toml ]; then
  echo ">>> Installing templateto_reports app from mounted volume..."
  rm -rf apps/templateto_reports
  cp -r /mnt/templateto_reports_repo apps/templateto_reports
  # Strip dev-only files that don't belong in an installed app
  rm -rf \
    apps/templateto_reports/.git \
    apps/templateto_reports/.github \
    apps/templateto_reports/screenshots \
    apps/templateto_reports/docker-compose.yml \
    apps/templateto_reports/init.sh
  ./env/bin/pip install -q -e apps/templateto_reports
  if ! grep -qx templateto_reports sites/apps.txt 2>/dev/null; then
    # Ensure apps.txt ends with a newline before appending — bench get-app
    # sometimes leaves the file without a trailing \n.
    [ -s sites/apps.txt ] && [ "$(tail -c1 sites/apps.txt)" != "" ] && \
      echo "" >> sites/apps.txt
    echo templateto_reports >> sites/apps.txt
  fi
fi

# 5. Create the dev.localhost site and install ERPNext + templateto_reports (only first time).
# --force drops any leftover MariaDB DB from a previous failed attempt.
if [ ! -d sites/dev.localhost ]; then
  echo ">>> Creating dev.localhost site..."
  bench new-site dev.localhost \
    --mariadb-root-password root \
    --admin-password admin \
    --no-mariadb-socket \
    --force \
    --install-app erpnext \
    --install-app templateto_reports
  bench use dev.localhost
fi

# 6. Make sure templateto_reports is installed on the site (covers re-installs after dev edits).
if ! bench --site dev.localhost list-apps | grep -q templateto_reports; then
  echo ">>> Installing templateto_reports on dev.localhost..."
  bench --site dev.localhost install-app templateto_reports
fi

# 7. Auto-complete the ERPNext setup wizard so we land on /app directly.
# Idempotent: setup_complete is a flag that doesn't unset.
if [ "$(bench --site dev.localhost execute 'frappe.db.get_single_value' --kwargs '{"doctype":"System Settings","fieldname":"setup_complete"}' 2>/dev/null | tail -1)" != "1" ]; then
  echo ">>> Auto-completing setup wizard..."
  bench --site dev.localhost execute 'frappe.desk.page.setup_wizard.setup_wizard.setup_complete' \
    --kwargs '{"args":{"language":"English","country":"United Kingdom","timezone":"Europe/London","currency":"GBP","full_name":"Administrator","email":"admin@example.com","password":"admin","company_name":"TemplateTo Test","company_abbr":"TT","chart_of_accounts":"Standard","fy_start_date":"2026-01-01","fy_end_date":"2026-12-31","company_tagline":"Testing","bank_account":"Test Bank","domains":["Manufacturing"]}}' \
    || echo "Warning: setup wizard auto-complete failed (continuing)"
fi

# 7b. Clear cache so the property setter on Print Format takes effect.
bench --site dev.localhost clear-cache || true

# 8. Generate the Procfile that `bench start` reads, and strip the bench-managed
# redis processes (we're using external redis containers).
if [ ! -f Procfile ]; then
  echo ">>> Generating Procfile..."
  bench setup procfile
  sed -i '/^redis_/d' Procfile
fi

echo ">>> Init complete. The frappe service can now be started."
