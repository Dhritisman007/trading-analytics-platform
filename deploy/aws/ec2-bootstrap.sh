#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo ./deploy/aws/ec2-bootstrap.sh"
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y ca-certificates curl gnupg lsb-release unzip nginx certbot python3-certbot-nginx awscli

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

. /etc/os-release

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  ${VERSION_CODENAME} stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start docker

if id ubuntu >/dev/null 2>&1; then
  usermod -aG docker ubuntu
fi

# CloudWatch Agent
TMP_DEB="/tmp/amazon-cloudwatch-agent.deb"
curl -fsSL "https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb" -o "${TMP_DEB}"
dpkg -i "${TMP_DEB}" || apt-get install -f -y
rm -f "${TMP_DEB}"

systemctl enable nginx
systemctl restart nginx

cat <<MSG
Bootstrap complete.

Installed:
- Docker Engine + Compose plugin
- Nginx
- Certbot
- AWS CLI
- Amazon CloudWatch Agent

Next steps:
1) Re-login SSH session (or run: newgrp docker)
2) Clone repo and set .env
3) Run deploy/aws/scripts/deploy-compose.sh
4) Configure nginx domain + certbot
MSG
