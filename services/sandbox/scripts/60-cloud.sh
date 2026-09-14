#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
source /etc/profile.d/10-toolchains.sh
source /tmp/versions.env

apt-get update
apt-get install -y --no-install-recommends \
    docker-ce-cli docker-compose-plugin skopeo buildah \
    kubectl terraform vault packer
rm -rf /var/lib/apt/lists/*

curl -fsSL "https://get.helm.sh/helm-v${HELM_VERSION}-linux-amd64.tar.gz" -o /tmp/helm.tgz && tar -xzf /tmp/helm.tgz -C /usr/local/bin --strip-components=1 linux-amd64/helm && rm -f /tmp/helm.tgz

curl -fsSL "https://github.com/opentofu/opentofu/releases/download/v${TOFU_VERSION}/tofu_${TOFU_VERSION}_linux_amd64.tar.gz" -o /tmp/tofu.tgz && tar -xzf /tmp/tofu.tgz -C /usr/local/bin tofu && rm -f /tmp/tofu.tgz
curl -fsSL "https://github.com/getsops/sops/releases/download/v${SOPS_VERSION}/sops-v${SOPS_VERSION}.linux.amd64" -o /usr/local/bin/sops && chmod +x /usr/local/bin/sops
curl -fsSL "https://github.com/FiloSottile/age/releases/download/v${AGE_VERSION}/age-v${AGE_VERSION}-linux-amd64.tar.gz" -o /tmp/age.tgz && tar -xzf /tmp/age.tgz -C /usr/local/bin --strip-components=1 age/age age/age-keygen && rm -f /tmp/age.tgz

curl -fsSL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o /tmp/awscli.zip && unzip -q /tmp/awscli.zip -d /tmp && /tmp/aws/install && rm -rf /tmp/aws /tmp/awscli.zip

GOBIN=/opt/gopath/bin /opt/go/bin/go install github.com/derailed/k9s@latest || true
GOBIN=/opt/gopath/bin /opt/go/bin/go install sigs.k8s.io/kustomize/kustomize/v5@latest || true