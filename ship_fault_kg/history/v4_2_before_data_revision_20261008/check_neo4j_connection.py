"""Read-only health/login checks; passwords are prompted, never stored in receipts."""
import argparse
import base64
import getpass
import json
import socket
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def query(base, database, user, password, statement):
    auth = base64.b64encode(f"{user}:{password}".encode()).decode()
    request = Request(
        f"{base.rstrip('/')}/db/{database}/query/v2",
        data=json.dumps({"statement": statement}).encode(),
        headers={"Authorization": "Basic " + auth, "Content-Type": "application/json"},
    )
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get("errors"):
        raise RuntimeError("Query API returned errors: " + str(result["errors"]))
    data = result.get("data", {})
    return [dict(zip(data.get("fields", []), row)) for row in data.get("values", [])]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:7474")
    parser.add_argument("--user", default="neo4j")
    parser.add_argument("--database", default="shipfaultkg")
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    if not 1 <= args.repeat <= 10:
        parser.error("repeat must be between 1 and 10")
    receipt = {"url": args.url, "database": args.database, "read_only": True}
    try:
        with urlopen(args.url.rstrip('/') + '/', timeout=10) as response:
            receipt["discovery"] = json.load(response)
        # Check Bolt negotiation without credentials. Authentication is tested below
        # via HTTP Query API; this is not a full authenticated Bolt session.
        with socket.create_connection(("127.0.0.1", 7687), timeout=5) as sock:
            sock.sendall(bytes.fromhex("6060b017000001ff000008050000040400000000"))
            version = sock.recv(4)
            if len(version) != 4 or version == b"\x00\x00\x00\x00":
                raise RuntimeError("Bolt handshake was rejected")
            receipt["bolt_handshake"] = version.hex()
        password = getpass.getpass("Neo4j password (hidden): ")
        counts = """
        CALL () { MATCH (n:ShipKG) RETURN count(n) AS active_nodes }
        CALL () { MATCH (:ShipKG)-[r]->(:ShipKG) RETURN count(r) AS active_relationships }
        CALL () { MATCH (n:ShipKG:Sensor) RETURN count(n) AS active_sensors }
        CALL () { MATCH (n:ArchivedSensor) RETURN count(n) AS archived_sensors }
        RETURN active_nodes, active_relationships, active_sensors, archived_sensors
        """
        receipt["login_checks"] = []
        for i in range(args.repeat):
            started = time.monotonic()
            rows = query(args.url, args.database, args.user, password, counts)
            receipt["login_checks"].append({"attempt": i + 1, "seconds": round(time.monotonic() - started, 3), "rows": rows})
            print(f"Login/query {i + 1}/{args.repeat}: OK", flush=True)
            if i + 1 < args.repeat:
                time.sleep(1)
        receipt["databases"] = query(args.url, "system", args.user, password,
                                     "SHOW DATABASES YIELD name, currentStatus, requestedStatus RETURN name, currentStatus, requestedStatus")
        receipt["status"] = "pass"
    except HTTPError as error:
        receipt["status"] = "fail"
        receipt["error"] = f"HTTP {error.code}: check account and database availability; no credentials logged."
    except (OSError, URLError, RuntimeError) as error:
        receipt["status"] = "fail"
        receipt["error"] = str(error)
    if args.receipt:
        args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    raise SystemExit(0 if receipt["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
