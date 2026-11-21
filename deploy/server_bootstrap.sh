#!/usr/bin/env bash
# One-time set-up of the Sydney server (docs/GO_LIVE_GUIDE.md B2-B5 in one go). PAPER ONLY.
# Run as root on a fresh Ubuntu 24.04 server. Safe to run again.
# It holds no secrets and asks for none: passwords and tokens go in later (GO_LIVE_GUIDE B6).
set -euo pipefail

echo "== 1/6 time zone and updates"
timedatectl set-timezone Australia/Sydney
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get -y full-upgrade
apt-get -y install unattended-upgrades ufw git qrencode curl ca-certificates
dpkg-reconfigure -f noninteractive unattended-upgrades

echo "== 2/6 Tailscale (a log-in link appears: open it and approve the server)"
command -v tailscale >/dev/null || curl -fsSL https://tailscale.com/install.sh | sh
tailscale status >/dev/null 2>&1 || tailscale up --ssh
tailscale status >/dev/null   # stop here if Tailscale is not connected

echo "== 3/6 firewall: nothing comes in from the internet, only over Tailscale"
ufw default deny incoming
ufw default allow outgoing
ufw allow in on tailscale0
ufw --force enable

echo "== 4/6 Docker"
command -v docker >/dev/null || curl -fsSL https://get.docker.com | sh
docker compose version

echo "== 5/6 folders the trader uses"
mkdir -p /srv/bigwins_forward/data/eodhd /srv/ref /srv/record/68_forward_record /srv/flex/inbox
chown 10001:10001 /srv/flex/inbox

echo "== 6/6 read-only GitHub key for the private repository"
[ -f ~/.ssh/bigwins_deploy ] || ssh-keygen -t ed25519 -f ~/.ssh/bigwins_deploy -N '' -C sydney-server
echo
echo "Done. Copy this PUBLIC key into GitHub > bigwins-trader > Settings > Deploy keys"
echo "(title: sydney server, leave 'Allow write access' OFF):"
echo
cat ~/.ssh/bigwins_deploy.pub
echo
timedatectl | grep -i synchronized
echo "Tailscale name of this server: $(tailscale status --self --json 2>/dev/null | grep -m1 '"DNSName"' | cut -d'"' -f4)"
