"""Dofus 3.7 market messages, including item 13831 from a real capture."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PRICE_REQUEST = bytes.fromhex("08876c1001")  # kcy: item 13831, price view
PRICE_RESPONSE = bytes.fromhex(
    "0a1808876c1206a08d0600000018a0bd022097012a0428015075"
    "10970118876c"
)  # jzs: x1 = 100000, other lot prices unavailable


def load_companion(platform):
    path = ROOT / platform / "astrub_companion.py"
    spec = importlib.util.spec_from_file_location(f"companion_{platform}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def varint(value):
    output = bytearray()
    while value >= 128:
        output.append((value & 127) | 128)
        value >>= 7
    output.append(value)
    return bytes(output)


def field(number, value):
    if isinstance(value, int):
        return varint(number << 3) + varint(value)
    return varint(number << 3 | 2) + varint(len(value)) + value


class Market37Tests(unittest.TestCase):
    def test_real_price_and_correlation_on_both_platforms(self):
        for platform in ("macos", "windows"):
            with self.subTest(platform=platform), tempfile.TemporaryDirectory() as directory:
                module = load_companion(platform)
                self.assertEqual(module.decode_jzs_market_view(PRICE_RESPONSE), (13831, [(1, 100000)]))
                companion = module.Companion({
                    "queue_path": str(Path(directory) / "queue.sqlite3"),
                    "server_id": 3,
                    "device_id": "test-device",
                })
                companion.flush = lambda: None
                companion.handle("in", "jzs", PRICE_RESPONSE)
                self.assertEqual(companion.queue.db.execute("SELECT COUNT(*) FROM pending").fetchone()[0], 0)
                companion.handle("out", "kcy", PRICE_REQUEST)
                companion.handle("in", "jzs", PRICE_RESPONSE)
                rows = companion.queue.db.execute("SELECT payload FROM pending").fetchall()
                self.assertEqual(len(rows), 1)
                event = json.loads(rows[0][0])
                self.assertEqual((event["item_id"], event["quantity"], event["price"]), (13831, 1, 100000))
                companion.queue.db.close()

    def test_minimum_per_available_lot_and_legacy_format(self):
        for platform in ("macos", "windows"):
            with self.subTest(platform=platform):
                module = load_companion(platform)
                details = [
                    field(1, 13831) + field(2, b"".join(map(varint, (150000, 700000, 0, 0)))),
                    field(1, 13831) + field(2, b"".join(map(varint, (100000, 800000, 0, 0)))),
                    field(1, 42) + field(2, b"".join(map(varint, (1, 1, 1, 1)))),
                ]
                response = b"".join(field(1, detail) for detail in details) + field(3, 13831)
                self.assertEqual(module.decode_jzs_market_view(response), (13831, [(1, 100000), (10, 700000)]))
                self.assertEqual(module.decode_jzs_market_view(response[:-1]), (None, None))
                old_detail = field(2, 13831) + field(6, b"".join(map(varint, (180, 187, 0, 0))))
                self.assertEqual(module.decode_jzn_market_view(field(1, 13831) + field(2, old_detail)),
                                 (13831, [(1, 180), (10, 187)]))


if __name__ == "__main__":
    unittest.main()
