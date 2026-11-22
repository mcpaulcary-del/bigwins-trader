#!/usr/bin/env bash
# One-time set-up of the Sydney-time server (docs/GO_LIVE_GUIDE.md B2-B5 in one go). PAPER ONLY.
# Run as root on a fresh Ubuntu 24.04 server (BinaryLane, Singapore region, Sydney time).
# Safe to run again. It holds no secrets and asks for none: passwords and tokens go in
# later (GO_LIVE_GUIDE B6).
set -euo pipefail

echo "== 1/9 time zone and updates"
timedatectl set-timezone Australia/Sydney
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get -y full-upgrade
# review F7: age + rclone (backups), tmux (Claude sessions), openssl (generated keys)
apt-get -y install unattended-upgrades ufw git qrencode curl ca-certificates age rclone tmux openssl
dpkg-reconfigure -f noninteractive unattended-upgrades

echo "== 2/9 swap (2 GB): the gateway and a build at the same time need it"
if ! swapon --show | grep -q /swapfile; then
  [ -f /swapfile ] || { fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile; }
  swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "== 3/9 Tailscale (a log-in link appears: open it and approve the server)"
command -v tailscale >/dev/null || curl -fsSL https://tailscale.com/install.sh | sh
tailscale status >/dev/null 2>&1 || tailscale up --ssh
tailscale status >/dev/null   # stop here if Tailscale is not connected

echo "== 4/9 firewall: nothing comes in from the internet, only over Tailscale"
ufw default deny incoming
ufw default allow outgoing
ufw allow in on tailscale0
ufw --force enable

echo "== 5/9 Docker, with log rotation set before any container exists"
mkdir -p /etc/docker
if [ ! -s /etc/docker/daemon.json ]; then
  cat > /etc/docker/daemon.json <<'JSON'
{"log-driver": "json-file", "log-opts": {"max-size": "20m", "max-file": "5"}}
JSON
fi
command -v docker >/dev/null || curl -fsSL https://get.docker.com | sh
systemctl restart docker
docker compose version

echo "== 6/9 folders the trader uses (owned by the trader's user, uid 10001)"
mkdir -p /srv/bigwins_forward/data/eodhd /srv/ref /srv/record/68_forward_record /srv/flex/inbox
chown -R 10001:10001 /srv/flex/inbox /srv/bigwins_forward/data/eodhd

echo "== 7/9 read-only GitHub key for the private repository"
[ -f ~/.ssh/bigwins_deploy ] || ssh-keygen -t ed25519 -f ~/.ssh/bigwins_deploy -N '' -C sydney-server
if [ -d /srv/asx-trader/.git ]; then
  git -C /srv/asx-trader config core.sshCommand "ssh -i /root/.ssh/bigwins_deploy -o IdentitiesOnly=yes"
fi

echo "== 8/9 the bigwins command"
if [ -f /srv/asx-trader/deploy/bigwins.sh ]; then
  ln -sf /srv/asx-trader/deploy/bigwins.sh /usr/local/bin/bigwins
fi

echo "== 9/9 done"
echo
echo "Copy this PUBLIC key into GitHub > bigwins-trader > Settings > Deploy keys"
echo "(title: sydney server, leave 'Allow write access' OFF):"
echo
cat ~/.ssh/bigwins_deploy.pub
echo
echo "Then clone with:  GIT_SSH_COMMAND='ssh -i /root/.ssh/bigwins_deploy' git clone -b bigwins-fast \\"
echo "                    git@github.com:<owner>/bigwins-trader.git /srv/asx-trader"
echo "and run this script once more (it links bigwins and sets the deploy key for git)."
echo
echo "IMPORTANT (review F8): in the Tailscale admin console > Machines > this server > ..."
echo "  > Disable key expiry. Otherwise the server drops off your tailnet in 180 days and"
echo "  the phone app stops working until you log it in again."
echo
timedatectl | grep -i synchronized
echo "Tailscale name of this server: $(tailscale status --self --json 2>/dev/null | grep -m1 '"DNSName"' | cut -d'"' -f4)"
