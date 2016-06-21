FROM busybox:latest
MAINTAINER Ivan Pedrazas <ipedrazas@gmail.com>

ADD https://releases.hashicorp.com/vault/0.6.0/vault_0.6.0_linux_amd64.zip /tmp/vault.zip

# Download, unzip the given version of vault and set permissions
RUN unzip -d /bin /tmp/vault.zip && rm /tmp/vault.zip && chmod 755 /bin/vault

COPY vault.dev.hcl /etc/vault.dev.hcl
COPY sydney-policy.json /etc/policy.json

ENTRYPOINT ["/bin/vault"]
CMD ["server", "-config=/etc/vault.dev.hcl", "-dev"]