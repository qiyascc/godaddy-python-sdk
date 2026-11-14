# Scheduled jobs

Scripts like [dynamic DNS](dynamic-dns.md) or a renewal report need to run on their own, every few minutes or once a week. Here is how to schedule one on Linux with cron or a systemd timer, and on Windows with the Task Scheduler.

The examples run `/opt/dns-tools/ddns.py` with the virtual environment in `/opt/dns-tools/.venv`. Adjust the paths to yours.

## Keep the credentials in a file

Scheduled jobs do not see the variables you exported in your terminal. Put them in a file only the job's user can read:

```bash
sudo mkdir -p /etc/dns-tools
sudo tee /etc/dns-tools/env > /dev/null <<'EOF'
GODADDY_API_KEY=your-key
GODADDY_API_SECRET=your-secret
EOF
sudo chmod 600 /etc/dns-tools/env
```

Alternatively, use a `godaddy.toml` file and point `GODADDY_CONFIG` at it. See [](../configuration.md).

## cron

Edit the crontab of the user that should run the job with `crontab -e` and add:

```text
*/5 * * * * set -a; . /etc/dns-tools/env; set +a; /opt/dns-tools/.venv/bin/python /opt/dns-tools/ddns.py >> /var/log/ddns.log 2>&1
```

- `*/5 * * * *` runs it every five minutes.
- `set -a` exports every variable the env file sets, so Python can see them.
- Calling the venv's own `python` means you do not have to activate the virtual environment.
- Output and errors go to `/var/log/ddns.log`. The user must be allowed to write there.

## systemd timer

A timer gives you logs in the journal, and it does not start a second run while the first one is still going.

`/etc/systemd/system/ddns.service`:

```ini
[Unit]
Description=Update home.example.com with the current public IP
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
EnvironmentFile=/etc/dns-tools/env
ExecStart=/opt/dns-tools/.venv/bin/python /opt/dns-tools/ddns.py
User=nobody
```

`/etc/systemd/system/ddns.timer`:

```ini
[Unit]
Description=Run ddns every five minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

Enable it and check it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ddns.timer
systemctl list-timers ddns.timer
journalctl -u ddns.service -n 20
```

The user in `User=` must be able to read the env file. Either create a dedicated user and give it the file, or drop `User=` to run as root.

## Windows Task Scheduler

1. Create `C:\dns-tools\run-ddns.cmd`:

   ```bat
   @echo off
   set GODADDY_API_KEY=your-key
   set GODADDY_API_SECRET=your-secret
   C:\dns-tools\.venv\Scripts\python.exe C:\dns-tools\ddns.py >> C:\dns-tools\ddns.log 2>&1
   ```

2. Open **Task Scheduler**, choose **Create Task**.
3. On **Triggers**, add a daily trigger and set **Repeat task every** to 5 minutes for a duration of **Indefinitely**.
4. On **Actions**, start the program `C:\dns-tools\run-ddns.cmd`.
5. On **General**, choose **Run whether user is logged on or not**.

Keep the `.cmd` file in a folder only your user can read, since it holds the credentials.

## A weekly report instead

The same setup runs any script. For a weekly job, use `0 8 * * 1` in cron (Mondays at 08:00) or `OnCalendar=Mon 08:00` in the timer instead of the five minute interval.
