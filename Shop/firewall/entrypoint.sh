
#!/bin/sh
set -eu

echo "[FIREWALL] Configuring ${SERVICE_NAME}"

iptables -F INPUT
iptables -F OUTPUT

iptables -P INPUT DROP
iptables -P OUTPUT ACCEPT

iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Поддержка одной или нескольких подсетей
SUBNETS="${ALLOWED_SUBNETS:-${ALLOWED_SUBNET:-}}"

for subnet in $(echo "$SUBNETS" | tr ',' ' '); do
    iptables -A INPUT -p tcp \
        -s "$subnet" \
        --dport "${FIREWALL_PORT}" \
        -j ACCEPT
done

iptables -A INPUT -m limit --limit 5/min \
    -j LOG --log-prefix "[FIREWALL DROP] " --log-level 4

echo "[FIREWALL] Rules applied:"
iptables -L INPUT -n -v

exec tail -f /dev/null
