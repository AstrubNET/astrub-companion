#!/usr/bin/env python3
"""Astrub Companion Windows: passive and anonymous Dofus HDV price collector."""

from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import ipaddress
import json
import logging
import os
import signal
import sqlite3
import struct
import subprocess
import sys
import threading
import queue as thread_queue
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

APP_DIR = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "Astrub Companion"
DEFAULT_CONFIG = APP_DIR / "config.json"
DEFAULT_DB = APP_DIR / "queue.sqlite3"
TYPE_PREFIX = "type.ankama.com/"


def read_varint(data: bytes, pos: int = 0):
    value = 0
    shift = 0
    while pos < len(data) and shift < 70:
        byte = data[pos]
        pos += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, pos
        shift += 7
    raise ValueError("varint incomplet")


def protobuf_fields(data: bytes):
    fields = []
    pos = 0
    while pos < len(data):
        key, pos = read_varint(data, pos)
        number, wire = key >> 3, key & 7
        if wire == 0:
            value, pos = read_varint(data, pos)
        elif wire == 1:
            if pos + 8 > len(data):
                raise ValueError("fixed64 incomplet")
            value, pos = data[pos:pos + 8], pos + 8
        elif wire == 2:
            size, pos = read_varint(data, pos)
            if pos + size > len(data):
                raise ValueError("champ tronqué")
            value, pos = data[pos:pos + size], pos + size
        elif wire == 5:
            if pos + 4 > len(data):
                raise ValueError("fixed32 incomplet")
            value, pos = data[pos:pos + 4], pos + 4
        else:
            raise ValueError(f"wire type non géré: {wire}")
        fields.append((number, wire, value))
    return fields


def varint_map(data: bytes):
    return {number: value for number, wire, value in protobuf_fields(data) if wire == 0}


def decode_envelope(frame: bytes):
    """Return (short type name, protobuf payload) from either envelope direction."""
    def visit(data: bytes, depth: int):
        if depth > 3:
            return None
        try:
            fields = protobuf_fields(data)
        except ValueError:
            return None
        for number, wire, value in fields:
            if number != 1 or wire != 2:
                continue
            try:
                type_url = value.decode()
            except UnicodeDecodeError:
                continue
            if type_url.startswith(TYPE_PREFIX):
                payload = next(
                    (candidate for field, candidate_wire, candidate in fields if field == 2 and candidate_wire == 2),
                    b"",
                )
                return type_url.rsplit("/", 1)[-1], payload
        for _, wire, value in fields:
            if wire == 2:
                found = visit(value, depth + 1)
                if found:
                    return found
        return None

    return visit(frame, 0)


class FrameStream:
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, payload: bytes):
        self.buffer.extend(payload)
        frames = []
        while self.buffer:
            try:
                size, header_end = read_varint(self.buffer)
            except ValueError:
                break
            if size > 16 * 1024 * 1024:
                del self.buffer[0]
                continue
            end = header_end + size
            if len(self.buffer) < end:
                break
            frames.append(bytes(self.buffer[header_end:end]))
            del self.buffer[:end]
        return frames


class PcapReader:
    """Minimal classic-PCAP reader for tcpdump -w stdout."""
    def __init__(self, stream):
        self.stream = stream
        header = self._exact(24)
        magic = header[:4]
        if magic in (b"\xd4\xc3\xb2\xa1", b"M<\xb2\xa1"):
            self.endian = "<"
        elif magic in (b"\xa1\xb2\xc3\xd4", b"\xa1\xb2<M"):
            self.endian = ">"
        else:
            raise RuntimeError("format PCAP inattendu")
        self.link_type = struct.unpack(self.endian + "I", header[20:24])[0]
        if self.link_type != 1:
            raise RuntimeError(f"liaison non gérée: {self.link_type} (Ethernet attendu)")

    def _exact(self, size):
        chunks = []
        remaining = size
        while remaining:
            chunk = self.stream.read(remaining)
            if not chunk:
                raise EOFError
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def packets(self):
        while True:
            try:
                record = self._exact(16)
                _, _, captured, _ = struct.unpack(self.endian + "IIII", record)
                yield self._exact(captured)
            except EOFError:
                return


def tcp_segment(packet: bytes):
    """Decode an Ethernet IPv4/IPv6 TCP segment involving Dofus port 5555."""
    if len(packet) < 54:
        return None
    offset = 14
    ether_type = packet[12:14]
    if ether_type == b"\x81\x00" and len(packet) >= 58:
        ether_type = packet[16:18]
        offset = 18
    ip = packet[offset:]
    if ether_type == b"\x08\x00":
        if len(ip) < 20 or ip[9] != 6:
            return None
        ip_header = (ip[0] & 0x0F) * 4
        src_addr, dst_addr = ip[12:16], ip[16:20]
    elif ether_type == b"\x86\xdd":
        if len(ip) < 40 or ip[6] != 6:  # pas d'en-têtes d'extension attendus ici
            return None
        ip_header = 40
        src_addr, dst_addr = ip[8:24], ip[24:40]
    else:
        return None
    tcp = ip[ip_header:]
    if len(tcp) < 20:
        return None
    src_port, dst_port = struct.unpack("!HH", tcp[:4])
    sequence = struct.unpack("!I", tcp[4:8])[0]
    tcp_header = (tcp[12] >> 4) * 4
    payload = tcp[tcp_header:]
    if not payload or (src_port != 5555 and dst_port != 5555):
        return None
    direction = "out" if dst_port == 5555 else "in"
    flow = (src_addr, dst_addr, src_port, dst_port)
    return direction, flow, sequence, payload


class TCPFlow:
    """Minimal ordered TCP reassembly with retransmission/overlap removal."""
    def __init__(self):
        self.next_sequence = None
        self.pending = {}
        self.frames = FrameStream()

    def feed(self, sequence: int, payload: bytes):
        if self.next_sequence is None:
            self.next_sequence = sequence

        if sequence < self.next_sequence:
            overlap = self.next_sequence - sequence
            if overlap >= len(payload):
                return []
            payload = payload[overlap:]
            sequence = self.next_sequence

        if sequence > self.next_sequence:
            self.pending.setdefault(sequence, payload)
            return []

        chunks = [payload]
        self.next_sequence += len(payload)
        while self.next_sequence in self.pending:
            chunk = self.pending.pop(self.next_sequence)
            chunks.append(chunk)
            self.next_sequence += len(chunk)
        return self.frames.feed(b"".join(chunks))


def decode_iua_item(payload: bytes):
    """Extract (item_id, quantity) from the confirmed inventory addition."""
    try:
        update = next(value for number, wire, value in protobuf_fields(payload) if number == 3 and wire == 2)
        item = next(value for number, wire, value in protobuf_fields(update) if number == 5 and wire == 2)
        values = varint_map(item)
        return values.get(1), values.get(3, 1)
    except (StopIteration, ValueError):
        return None, None


def decode_kes_update(payload: bytes):
    """Extract (item_id, price, quantity) from a confirmed listing price update."""
    try:
        fields = protobuf_fields(payload)
        details = next(value for number, wire, value in fields if number == 1 and wire == 2)
        outer = {number: value for number, wire, value in fields if wire == 0}
        inner = varint_map(details)
        return inner.get(3), outer.get(2), inner.get(4)
    except (StopIteration, ValueError):
        return None, None, None


def decode_kbt_market_view(payload: bytes):
    """Extract (item_id, unit_price) from a detailed resource-market response."""
    try:
        fields = protobuf_fields(payload)
        outer = {number: value for number, wire, value in fields if wire == 0}
        details = next(value for number, wire, value in fields if number == 3 and wire == 2)
        detail_fields = protobuf_fields(details)
        inner = {number: value for number, wire, value in detail_fields if wire == 0}
        packed_prices = next(
            value for number, wire, value in detail_fields if number == 6 and wire == 2
        )
        price, _ = read_varint(packed_prices)
        item_id = outer.get(2)
        if item_id != inner.get(5):
            return None, None
        return item_id, price
    except (StopIteration, ValueError):
        return None, None


class Queue:
    def __init__(self, path: Path):
        self.db = sqlite3.connect(path)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS pending (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at INTEGER NOT NULL,
                payload TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT
            )
        """)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS rejected (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pending_id INTEGER NOT NULL,
                rejected_at INTEGER NOT NULL,
                payload TEXT NOT NULL,
                error TEXT NOT NULL
            )
        """)
        self.db.commit()

    def add(self, payload):
        self.db.execute(
            "INSERT INTO pending(created_at,payload) VALUES (?,?)",
            (int(time.time()), json.dumps(payload, separators=(",", ":"))),
        )
        self.db.commit()

    def first(self):
        return self.db.execute("SELECT id,payload FROM pending ORDER BY id LIMIT 1").fetchone()

    def done(self, row_id):
        self.db.execute("DELETE FROM pending WHERE id=?", (row_id,))
        self.db.commit()

    def failed(self, row_id, error):
        self.db.execute(
            "UPDATE pending SET attempts=attempts+1,last_error=? WHERE id=?",
            (str(error)[:500], row_id),
        )
        self.db.commit()

    def reject(self, row_id, payload, error):
        self.db.execute(
            "INSERT INTO rejected(pending_id,rejected_at,payload,error) VALUES (?,?,?,?)",
            (row_id, int(time.time()), payload, str(error)[:2000]),
        )
        self.db.execute("DELETE FROM pending WHERE id=?", (row_id,))
        self.db.commit()


class Companion:
    def __init__(self, config):
        self.config = config
        self.candidate_item_id = None
        self.candidate_item_at = 0.0
        self.current_item_id = None
        self.current_item_at = 0.0
        self.pending_purchases = {}
        self.pending_market_views = {}
        self.sent_market_views = {}
        self.recent_events = {}
        self.api_retry_at = 0.0
        self.queue = Queue(Path(config.get("queue_path", DEFAULT_DB)))

    def enqueue_once(self, event, signature):
        now = time.time()
        self.recent_events = {
            key: seen_at for key, seen_at in self.recent_events.items()
            if now - seen_at <= 10
        }
        if signature in self.recent_events:
            logging.debug("Retransmission applicative ignorée: %s", signature)
            return False
        self.recent_events[signature] = now
        # Utilisés pour la corrélation locale uniquement : ils ne quittent pas le Mac.
        event.pop("object_uid", None)
        event.pop("offer_id", None)
        event["event_id"] = str(uuid.uuid4())
        event["device_id"] = self.config["device_id"]
        self.queue.add(event)
        return True

    def handle(self, direction, message_type, payload):
        now = time.time()
        self.pending_purchases = {
            offer_id: purchase
            for offer_id, purchase in self.pending_purchases.items()
            if now - purchase["created_at"] <= self.config.get("purchase_ttl_seconds", 20)
        }
        values = varint_map(payload)
        if direction == "out" and message_type == "keh" and 1 in values:
            # keh annonce une sélection potentielle. Dès que l'utilisateur
            # change d'objet, l'ancienne association ne doit plus être utilisée.
            self.candidate_item_id = values[1]
            self.candidate_item_at = now
            if self.current_item_id != self.candidate_item_id:
                self.current_item_id = None
                self.current_item_at = 0.0
            logging.debug("Objet HDV candidat: %s", self.candidate_item_id)
            if values.get(2) == 1:
                self.pending_market_views[values[1]] = now
            return
        if direction == "in" and message_type == "kbt":
            item_id, price = decode_kbt_market_view(payload)
            requested_at = self.pending_market_views.get(item_id)
            if item_id is None or price is None or price <= 0 or requested_at is None:
                if item_id is not None and price == 0:
                    self.pending_market_views.pop(item_id, None)
                    logging.info("Consultation HDV ignorée: item=%s sans offre x1", item_id)
                return
            if now - requested_at > self.config.get("market_view_ttl_seconds", 20):
                self.pending_market_views.pop(item_id, None)
                return
            self.pending_market_views.pop(item_id, None)
            dedupe_seconds = self.config.get("market_view_dedupe_seconds", 300)
            previous = self.sent_market_views.get((item_id, price), 0)
            if now - previous < dedupe_seconds:
                logging.debug("Consultation HDV déjà transmise récemment: item=%s prix=%s", item_id, price)
                return
            self.sent_market_views = {
                key: seen_at for key, seen_at in self.sent_market_views.items()
                if now - seen_at <= dedupe_seconds
            }
            event = {
                "server_id": self.config["server_id"],
                "item_id": item_id,
                "price": price,
                "quantity": 1,
                "source": "companion_market_view",
                "transaction_confirmed": True,
                "captured_at": int(now),
            }
            if self.enqueue_once(event, ("market_view", item_id, price)):
                self.sent_market_views[(item_id, price)] = now
                logging.info("Prix HDV observé: item=%s prix=%s quantité=1", item_id, price)
                self.flush()
            return
        if direction == "out" and message_type == "kbz" and 1 in values:
            # Une vente n'est associée qu'après la séquence cohérente
            # keh(item_id) -> kbz(même item_id). En cas d'ambiguïté, on ignore.
            if self.candidate_item_id == values[1]:
                self.current_item_id = values[1]
                self.current_item_at = now
                logging.debug("Objet HDV confirmé: %s", self.current_item_id)
            else:
                self.current_item_id = None
                self.current_item_at = 0.0
                logging.warning(
                    "Sélection HDV ambiguë ignorée: keh=%s kbz=%s",
                    self.candidate_item_id,
                    values[1],
                )
            return
        if direction == "out" and message_type == "kbm":
            if not all(field in values for field in (1, 2, 3)):
                logging.warning("Demande d'achat kbm incomplète")
                return
            if self.candidate_item_id is None or now - self.candidate_item_at > self.config.get("selection_ttl_seconds", 120):
                logging.warning("Achat ignoré par sécurité: aucun item_id candidat récent")
                return
            offer_id = values[1]
            self.pending_purchases[offer_id] = {
                "offer_id": offer_id,
                "item_id": self.candidate_item_id,
                "price": values[2],
                "quantity": values[3],
                "created_at": now,
                "server_confirmed": False,
            }
            logging.info(
                "Demande d'achat détectée: item=%s prix=%s quantité=%s",
                self.candidate_item_id,
                values[2],
                values[3],
            )
            return
        if direction == "in" and message_type == "kgp":
            offer_id, item_id = values.get(3), values.get(5)
            purchase = self.pending_purchases.get(offer_id)
            if purchase and purchase["item_id"] == item_id:
                purchase["server_confirmed"] = True
                logging.debug("Achat confirmé par le marché: offre=%s item=%s", offer_id, item_id)
            return
        if direction == "in" and message_type == "iua":
            item_id, quantity = decode_iua_item(payload)
            candidates = sorted(
                (
                    purchase for purchase in self.pending_purchases.values()
                    if purchase["server_confirmed"]
                    and purchase["item_id"] == item_id
                    and purchase["quantity"] == quantity
                ),
                key=lambda purchase: purchase["created_at"],
            )
            if not candidates:
                return
            purchase = candidates[0]
            if quantity != 1:
                del self.pending_purchases[purchase["offer_id"]]
                logging.info("Achat ignoré: quantité=%s (seuls les lots x1 sont transmis)", quantity)
                return
            event = {
                "server_id": self.config["server_id"],
                "item_id": purchase["item_id"],
                "price": purchase["price"],
                "quantity": purchase["quantity"],
                "offer_id": purchase["offer_id"],
                "source": "companion_purchase",
                "transaction_confirmed": True,
                "captured_at": int(now),
            }
            self.enqueue_once(event, ("purchase", purchase["offer_id"], item_id, event["price"], quantity))
            del self.pending_purchases[purchase["offer_id"]]
            logging.info("Achat confirmé: item=%s prix=%s quantité=%s", item_id, event["price"], quantity)
            self.flush()
            return
        if direction == "in" and message_type == "kes":
            item_id, price, quantity = decode_kes_update(payload)
            if not all(isinstance(value, int) and value > 0 for value in (item_id, price, quantity)):
                logging.warning("Confirmation de modification kes incomplète")
                return
            if quantity != 1:
                logging.info("Modification ignorée: quantité=%s (seuls les lots x1 sont transmis)", quantity)
                return
            event = {
                "server_id": self.config["server_id"],
                "item_id": item_id,
                "price": price,
                "quantity": quantity,
                "source": "companion_price_update",
                "transaction_confirmed": True,
                "captured_at": int(now),
            }
            if self.enqueue_once(event, ("price_update", item_id, price, quantity)):
                logging.info("Modification confirmée: item=%s prix=%s quantité=%s", item_id, price, quantity)
                self.flush()
            return
        if direction != "out" or message_type != "kge":
            return
        if now - self.current_item_at > self.config.get("selection_ttl_seconds", 120):
            logging.warning("Mise en vente ignorée par sécurité: aucun item_id confirmé et récent (UID %s)", values.get(2))
            return
        if not all(field in values for field in (1, 2, 3)):
            logging.warning("Message kge incomplet")
            return
        if values[3] != 1:
            logging.info("Mise en vente ignorée: quantité=%s (seuls les lots x1 sont transmis)", values[3])
            return
        event = {
            "server_id": self.config["server_id"],
            "item_id": self.current_item_id,
            "price": values[1],
            "quantity": values[3],
            "object_uid": values[2],
            "source": "astrub_companion",
            "captured_at": int(now),
        }
        if not self.enqueue_once(event, ("listing", values[2], values[1], values[3])):
            return
        logging.info("Offre détectée: item=%s prix=%s quantité=%s", event["item_id"], event["price"], event["quantity"])
        self.flush()

    def flush(self):
        if time.time() < self.api_retry_at:
            return
        while True:
            row = self.queue.first()
            if not row:
                return
            row_id, raw = row
            request = urllib.request.Request(
                self.config["api_url"],
                data=raw.encode(),
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Astrub-Companion-Windows/1.1.2",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    if not 200 <= response.status < 300:
                        raise RuntimeError(f"HTTP {response.status}")
                self.queue.done(row_id)
                logging.info("Contribution transmise à Astrub.net")
            except urllib.error.HTTPError as error:
                try:
                    detail = error.read(500).decode("utf-8", "replace")
                except Exception:
                    detail = ""
                if error.code in (400, 404, 409, 422):
                    self.queue.reject(row_id, raw, f"HTTP {error.code}: {detail}")
                    logging.error("Contribution invalide placée en quarantaine: HTTP %s %s", error.code, detail)
                    continue
                retry_after = error.headers.get("Retry-After") if error.headers else None
                delay = max(60, int(retry_after)) if retry_after and retry_after.isdigit() else 60
                self.api_retry_at = time.time() + delay
                self.queue.failed(row_id, f"HTTP {error.code}: {detail}")
                logging.warning("API HTTP %s; nouvel essai dans %ss", error.code, delay)
                return
            except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
                self.api_retry_at = time.time() + 15
                self.queue.failed(row_id, error)
                logging.warning("API indisponible; contribution conservée: %s", error)
                return


def load_config(path: Path):
    with path.open() as file:
        config = json.load(file)
    required = ("api_url", "server_id", "device_id")
    missing = [key for key in required if not config.get(key)]
    if missing:
        raise RuntimeError("configuration manquante: " + ", ".join(missing))
    if not str(config["api_url"]).startswith("https://"):
        raise RuntimeError("api_url doit utiliser HTTPS")
    config["server_id"] = int(config["server_id"])
    return config


class PcapIf(ctypes.Structure):
    pass


PcapIf._fields_ = [
    ("next", ctypes.POINTER(PcapIf)),
    ("name", ctypes.c_char_p),
    ("description", ctypes.c_char_p),
    ("addresses", ctypes.c_void_p),
    ("flags", ctypes.c_uint),
]


class TimeVal(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_long), ("tv_usec", ctypes.c_long)]


class PcapHeader(ctypes.Structure):
    _fields_ = [("ts", TimeVal), ("caplen", ctypes.c_uint), ("length", ctypes.c_uint)]


class BpfProgram(ctypes.Structure):
    _fields_ = [("bf_len", ctypes.c_uint), ("bf_insns", ctypes.c_void_p)]


def load_npcap():
    candidates = [
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32" / "Npcap" / "wpcap.dll",
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32" / "wpcap.dll",
    ]
    dll_path = next((path for path in candidates if path.exists()), None)
    if dll_path is None:
        raise RuntimeError("Npcap est absent. Installe-le depuis https://npcap.com/#download")
    dll = ctypes.WinDLL(str(dll_path))
    dll.pcap_findalldevs.argtypes = [ctypes.POINTER(ctypes.POINTER(PcapIf)), ctypes.c_char_p]
    dll.pcap_findalldevs.restype = ctypes.c_int
    dll.pcap_freealldevs.argtypes = [ctypes.POINTER(PcapIf)]
    dll.pcap_open_live.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
    dll.pcap_open_live.restype = ctypes.c_void_p
    dll.pcap_datalink.argtypes = [ctypes.c_void_p]
    dll.pcap_datalink.restype = ctypes.c_int
    dll.pcap_compile.argtypes = [ctypes.c_void_p, ctypes.POINTER(BpfProgram), ctypes.c_char_p, ctypes.c_int, ctypes.c_uint]
    dll.pcap_setfilter.argtypes = [ctypes.c_void_p, ctypes.POINTER(BpfProgram)]
    dll.pcap_freecode.argtypes = [ctypes.POINTER(BpfProgram)]
    dll.pcap_next_ex.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.POINTER(PcapHeader)), ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte))]
    dll.pcap_next_ex.restype = ctypes.c_int
    dll.pcap_close.argtypes = [ctypes.c_void_p]
    return dll


def npc_interfaces(dll):
    errbuf = ctypes.create_string_buffer(256)
    first = ctypes.POINTER(PcapIf)()
    if dll.pcap_findalldevs(ctypes.byref(first), errbuf) != 0:
        raise RuntimeError(errbuf.value.decode("utf-8", "replace"))
    names = []
    current = first
    try:
        while current:
            entry = current.contents
            if entry.name and not (entry.flags & 1):  # exclure les interfaces loopback
                names.append(entry.name)
            current = entry.next
    finally:
        dll.pcap_freealldevs(first)
    return names


def capture_adapter(dll, name, packets, stopped):
    errbuf = ctypes.create_string_buffer(256)
    handle = dll.pcap_open_live(name, 65535, 0, 250, errbuf)
    if not handle:
        logging.warning("Interface ignorée: %s", errbuf.value.decode("utf-8", "replace"))
        return
    try:
        if dll.pcap_datalink(handle) != 1:
            return
        program = BpfProgram()
        if dll.pcap_compile(handle, ctypes.byref(program), b"tcp port 5555", 1, 0xFFFFFFFF) != 0:
            return
        try:
            if dll.pcap_setfilter(handle, ctypes.byref(program)) != 0:
                return
        finally:
            dll.pcap_freecode(ctypes.byref(program))
        while not stopped.is_set():
            header = ctypes.POINTER(PcapHeader)()
            data = ctypes.POINTER(ctypes.c_ubyte)()
            status = dll.pcap_next_ex(handle, ctypes.byref(header), ctypes.byref(data))
            if status == 1:
                packets.put(ctypes.string_at(data, header.contents.caplen))
            elif status == -1:
                return
    finally:
        dll.pcap_close(handle)


def run(config):
    dll = load_npcap()
    interfaces = npc_interfaces(dll)
    if not interfaces:
        raise RuntimeError("Aucune interface Npcap utilisable")
    packets = thread_queue.Queue(maxsize=10000)
    stopped = threading.Event()
    for name in interfaces:
        threading.Thread(target=capture_adapter, args=(dll, name, packets, stopped), daemon=True).start()
    logging.info("Écoute passive démarrée sur %s interface(s) Windows", len(interfaces))
    companion = Companion(config)
    streams = {}
    try:
        while True:
            try:
                packet = packets.get(timeout=1)
            except thread_queue.Empty:
                companion.flush()
                continue
            decoded_tcp = tcp_segment(packet)
            if not decoded_tcp:
                continue
            direction, flow, sequence, payload = decoded_tcp
            stream = streams.setdefault((direction, flow), TCPFlow())
            for frame in stream.feed(sequence, payload):
                decoded = decode_envelope(frame)
                if decoded:
                    companion.handle(direction, *decoded)
            companion.flush()
    finally:
        stopped.set()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    APP_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(APP_DIR / "companion.log", encoding="utf-8")],
    )
    try:
        run(load_config(args.config))
    except Exception as error:
        logging.exception("Arrêt d'Astrub Companion: %s", error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
