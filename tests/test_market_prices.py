import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
MODULES = []
for platform in ('macos', 'windows'):
    spec = importlib.util.spec_from_file_location(platform, ROOT / platform / 'astrub_companion.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    MODULES.append(module)


def varint(value):
    result = bytearray()
    while value >= 128:
        result.append((value & 127) | 128)
        value >>= 7
    result.append(value)
    return bytes(result)


def integer(field, value):
    return varint(field << 3) + varint(value)


def blob(field, value):
    return varint(field << 3 | 2) + varint(len(value)) + value


def response(kind, rows, item=8215):
    outer, details, inner = (1, 2, 2) if kind == 'jzn' else (2, 3, 5)
    return integer(outer, item) + b''.join(
        blob(details, integer(inner, row_item) + blob(6, b''.join(map(varint, prices))))
        for row_item, prices in rows
    )


class MarketTests(unittest.TestCase):
    def test_minimum_independently_per_lot_and_order(self):
        rows = [(8215, [2499, 700, 0, 50000]), (8215, [180, 900, 10000, 0]),
                (8215, [0, 600, 9000, 45000]), (999, [1, 1, 1, 1])]
        for module in MODULES:
            for kind in ('jzn', 'kbt'):
                for ordered in (rows, list(reversed(rows))):
                    with self.subTest(platform=module.__name__, kind=kind):
                        self.assertEqual(getattr(module, 'decode_' + kind + '_market_view')(response(kind, ordered)),
                                         (8215, [(1, 180), (10, 600), (100, 9000), (1000, 45000)]))

    def test_missing_lots_and_empty_response(self):
        for module in MODULES:
            for kind in ('jzn', 'kbt'):
                decoder = getattr(module, 'decode_' + kind + '_market_view')
                for rows, expected in [([], []), ([(8215, [0, 0, 0, 0])], []),
                                       ([(8215, [0, 1870])], [(10, 1870)]),
                                       ([(999, [1])], [])]:
                    self.assertEqual(decoder(response(kind, rows)), (8215, expected))
                self.assertEqual(decoder(b''), (None, None))

    def test_truncation_never_publishes_partial_minimum(self):
        for module in MODULES:
            for kind in ('jzn', 'kbt'):
                data = response(kind, [(8215, [2499]), (8215, [180])])
                self.assertEqual(getattr(module, 'decode_' + kind + '_market_view')(data[:-1]), (None, None))

    def test_equipment_capture_and_api_queue(self):
        payload = bytes.fromhex((ROOT / 'tests/fixtures/item-8215-jzn.hex').read_text())
        for module in MODULES:
            self.assertEqual(module.decode_jzn_market_view(payload), (8215, [(1, 180)]))
            with tempfile.TemporaryDirectory() as directory:
                companion = module.Companion({'queue_path': str(Path(directory) / 'queue.db'),
                                              'server_id': 3, 'device_id': 'test-device'})
                companion.flush = Mock()
                companion.handle('out', 'kde', integer(1, 1) + integer(2, 8215))
                companion.handle('in', 'jzn', payload)
                import json
                event = json.loads(companion.queue.first()[1])
                self.assertEqual((event['item_id'], event['quantity'], event['price']), (8215, 1, 180))
                self.assertEqual(event['source'], 'companion_market_view')
                self.assertEqual(companion.queue.db.execute('SELECT COUNT(*) FROM pending').fetchone()[0], 1)
                companion.handle('out', 'kde', integer(1, 1) + integer(2, 8215))
                companion.handle('in', 'jzn', payload)
                self.assertEqual(companion.queue.db.execute('SELECT COUNT(*) FROM pending').fetchone()[0], 1)
                companion.queue.db.close()

    def test_api_receives_each_lot_minimum(self):
        for module in MODULES:
            with tempfile.TemporaryDirectory() as directory:
                companion = module.Companion({'queue_path': str(Path(directory) / 'queue.db'),
                                              'server_id': 3, 'device_id': 'test-device'})
                companion.flush = Mock()
                companion.handle('out', 'kde', integer(1, 1) + integer(2, 8215))
                companion.handle('in', 'jzn', response('jzn', [(8215, [200, 0, 9000, 60000]),
                                                            (8215, [180, 1500, 9500, 55000])]))
                import json
                events = [json.loads(row[0]) for row in companion.queue.db.execute('SELECT payload FROM pending')]
                self.assertEqual([(e['quantity'], e['price']) for e in events],
                                 [(1, 180), (10, 1500), (100, 9000), (1000, 55000)])
                companion.queue.db.close()


if __name__ == '__main__':
    unittest.main()
