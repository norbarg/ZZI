import json
from dataclasses import dataclass
from enum import Enum


class Action(Enum):
    PERMIT = "PERMIT"
    DENY = "DENY (Implicit Deny)"


class TCPState(Enum):
    SYN_SENT = "SYN_SENT"
    ESTABLISHED = "ESTABLISHED"
    CLOSED = "CLOSED"


@dataclass
class Packet:
    src_ip: str
    dst_ip: str
    protocol: str
    src_port: int
    dst_port: int
    tcp_flags: str = ""


@dataclass
class ACLRule:
    src_ip: str
    dst_ip: str
    protocol: str
    src_port: str
    dst_port: str
    action: Action


class StaticACLFirewall:
    def __init__(self, rules):
        self.rules = rules

    def _matches(self, rule_value, packet_value):
        if rule_value == "*":
            return True
        if "-" in rule_value:
            low, high = map(int, rule_value.split("-"))
            return low <= packet_value <= high
        return int(rule_value) == packet_value

    def evaluate(self, packet):
        for rule in self.rules:
            if (
                rule.src_ip in ("*", packet.src_ip)
                and rule.dst_ip in ("*", packet.dst_ip)
                and rule.protocol == packet.protocol
                and self._matches(rule.src_port, packet.src_port)
                and self._matches(rule.dst_port, packet.dst_port)
            ):
                return rule.action

        return Action.DENY


@dataclass
class ConnectionEntry:
    src_ip: str
    src_port: int
    dst_ip: str
    dst_port: int
    protocol: str
    state: TCPState
    udp_timer: int = 0


class StatefulFirewall:
    UDP_TIMEOUT = 30

    def __init__(self, outbound_policy_allows):
        self.outbound_policy_allows = outbound_policy_allows
        self.state_table = {}

    def _key(self, packet):
        return (
            packet.src_ip,
            packet.src_port,
            packet.dst_ip,
            packet.dst_port,
            packet.protocol,
        )

    def process_outbound(self, packet):
        key = self._key(packet)

        if packet.tcp_flags in ("FIN", "RST") and key in self.state_table:
            del self.state_table[key]
            return Action.PERMIT

        if (packet.protocol, packet.dst_port) not in self.outbound_policy_allows:
            return Action.DENY

        if packet.protocol == "TCP" and packet.tcp_flags == "SYN":
            self.state_table[key] = ConnectionEntry(
                packet.src_ip,
                packet.src_port,
                packet.dst_ip,
                packet.dst_port,
                "TCP",
                TCPState.SYN_SENT,
            )

        elif packet.protocol == "UDP":
            self.state_table[key] = ConnectionEntry(
                packet.src_ip,
                packet.src_port,
                packet.dst_ip,
                packet.dst_port,
                "UDP",
                TCPState.ESTABLISHED,
                self.UDP_TIMEOUT,
            )

        return Action.PERMIT

    def process_inbound(self, packet):
        for key, entry in list(self.state_table.items()):
            if (
                entry.dst_ip == packet.src_ip
                and entry.dst_port == packet.src_port
                and entry.src_ip == packet.dst_ip
                and entry.src_port == packet.dst_port
                and entry.protocol == packet.protocol
            ):
                if entry.protocol == "TCP":
                    if packet.tcp_flags == "SYN-ACK":
                        if entry.state != TCPState.SYN_SENT:
                            return Action.DENY
                        entry.state = TCPState.ESTABLISHED

                    elif packet.tcp_flags in ("FIN", "RST"):
                        entry.state = TCPState.CLOSED
                        del self.state_table[key]

                return Action.PERMIT

        return Action.DENY

    def show_state_table(self):
        if not self.state_table:
            print("  Таблиця станів порожня.")
            return

        for entry in self.state_table.values():
            print(
                f"  {entry.src_ip}:{entry.src_port} -> "
                f"{entry.dst_ip}:{entry.dst_port} "
                f"{entry.protocol} [{entry.state.value}]"
            )


def main():
    with open("variant_3.json", encoding="utf-8") as file:
        variant = json.load(file)

    client_ip = variant["client_ip"]
    server_ip = "203.0.113.10"
    client_port = 54321
    server_port = 443

    policy = {
        (protocol, int(port))
        for item in variant["outbound_policy"]
        for protocol, port in [item.split(":")]
    }

    firewall = StatefulFirewall(policy)

    print("=" * 65)
    print(f"STATEFUL FIREWALL - ВАРІАНТ №{variant['variant']}")
    print("=" * 65)
    print(f"Клієнт: {client_ip}")
    print(f"Сервер: {server_ip}")
    print(f"Дозволена політика: {sorted(policy)}")

    print("\n1. Вихідний SYN від клієнта")
    syn = Packet(client_ip, server_ip, "TCP", client_port, server_port, "SYN")
    print("Результат:", firewall.process_outbound(syn).value)
    firewall.show_state_table()

    print("\n2. Вхідний SYN-ACK від сервера")
    syn_ack = Packet(server_ip, client_ip, "TCP", server_port, client_port, "SYN-ACK")
    print("Результат:", firewall.process_inbound(syn_ack).value)
    firewall.show_state_table()

    print("\n3. Спроба підключення стороннього хоста")
    attacker = Packet(
        "198.51.100.99", client_ip, "TCP", server_port, client_port, "SYN-ACK"
    )
    print("Результат:", firewall.process_inbound(attacker).value)
    firewall.show_state_table()

    print("\n4. Завершення з'єднання (FIN)")
    fin = Packet(server_ip, client_ip, "TCP", server_port, client_port, "FIN")
    print("Результат:", firewall.process_inbound(fin).value)
    firewall.show_state_table()

    print("\n5. Повторна відповідь після закриття")
    print("Результат:", firewall.process_inbound(syn_ack).value)

    print("\n6. Порівняння зі статичним ACL")
    strict_acl = StaticACLFirewall([])
    broad_acl = StaticACLFirewall(
        [ACLRule("*", client_ip, "TCP", "443", "1024-65535", Action.PERMIT)]
    )

    print("Без дозволяючих правил:")
    print("  Сервер:", strict_acl.evaluate(syn_ack).value)

    print("Із широким правилом для зворотного трафіку:")
    print("  Сервер:", broad_acl.evaluate(syn_ack).value)
    print("  Сторонній хост:", broad_acl.evaluate(attacker).value)

    print("\nМоделювання завершено.")


if __name__ == "__main__":
    main()
