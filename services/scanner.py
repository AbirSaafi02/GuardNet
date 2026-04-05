import nmap

class NetworkScanner:
    def __init__(self):
        self.scanner = nmap.PortScanner()

    def scan(self, ip_range: str, scan_type: str = "rapide") -> list:
        args = {
            "rapide": "-sn",
            "complet": "-sV -O --osscan-guess",
        }.get(scan_type, "-sn")

        print(f"[SCAN] Démarrage scan {ip_range} avec args '{args}'")
        self.scanner.scan(hosts=ip_range, arguments=args)

        results = []
        for host in self.scanner.all_hosts():
            host_info = self.scanner[host]

            os_name = ""
            device_type = "unknown"
            if "osmatch" in host_info and host_info["osmatch"]:
                os_name = host_info["osmatch"][0]["name"]
                device_type = self._detect_device_type(os_name)

            ports = []
            for proto in host_info.all_protocols():
                for port in host_info[proto].keys():
                    port_info = host_info[proto][port]
                    if port_info["state"] == "open":
                        ports.append({
                            "port": port,
                            "protocol": proto,
                            "service": port_info.get("name", ""),
                            "version": port_info.get("version", ""),
                            "is_new_port": False
                        })

            results.append({
                "ip": host,
                "hostname": host_info.hostname() or "",
                "state": host_info.state(),
                "os_name": os_name,
                "device_type": device_type,
                "ports": ports,
                "is_new": False
            })

        print(f"[SCAN] Terminé : {len(results)} hosts trouvés")
        return results

    def _detect_device_type(self, os_name: str) -> str:
        os_lower = os_name.lower()
        if any(x in os_lower for x in ["cisco", "router", "juniper"]):
            return "router"
        if any(x in os_lower for x in ["switch", "catalyst"]):
            return "switch"
        if any(x in os_lower for x in ["server", "ubuntu server", "centos", "debian"]):
            return "server"
        if any(x in os_lower for x in ["windows", "linux", "mac", "ubuntu"]):
            return "workstation"
        return "unknown"