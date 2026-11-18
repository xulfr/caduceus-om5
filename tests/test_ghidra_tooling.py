"""Host-independent import/query planning tests; not a Ghidra runtime test."""
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'tools/ghidra'


def load(name):
    spec = importlib.util.spec_from_file_location('om5_' + name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GhidraPlanningTests(unittest.TestCase):
    def test_import_sections_keep_native_gaps_unmapped(self):
        module = load('import_sections')
        image = bytes(256)
        report = dict(schema='om5-space-map/1', base=0x60021020,
                      image_sha256=hashlib.sha256(image).hexdigest(), sections=[
                          dict(id=1, start=0x60021040, end=0x60021060),
                          dict(id=2, start=0x60021080, end=0x600210a0)])
        blocks = module.import_plan(report, image)
        self.assertEqual([b['name'] for b in blocks], ['resident_prefix', 'section_1', 'section_2'])
        self.assertEqual(blocks[1]['offset'], 32)
        self.assertFalse(any(b['start'] <= 0x60021070 < b['end'] for b in blocks))
        with self.assertRaisesRegex(ValueError, 'disagree'):
            module.import_plan(report, b'x' * 256)
        report['sections'][1]['start'] = 0x60021050
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            module.import_plan(report, image)

    def test_labels_conflicts_and_sanitization(self):
        module = load('import_sections')
        doc = dict(schema='om5-symbols/1', conflicts=[], symbols=[dict(name='a.b', address=0x60000000)])
        self.assertEqual(module.label_plan(doc), [('a_b', 0x60000000)])
        doc['symbols'].append(dict(name='a_b', address=0x60000004))
        with self.assertRaisesRegex(ValueError, 'collide'):
            module.label_plan(doc)
        doc['conflicts'] = [{}]
        with self.assertRaisesRegex(ValueError, 'conflicts'):
            module.label_plan(doc)

    def test_headless_command_uses_mn103_and_call_frame_fix(self):
        module = load('headless')
        command = module.import_command(Path('/ghidra'), Path('/generated/ghidra'), True)
        self.assertIn('MN103:LE:32:AM33-2', command)
        self.assertIn('import_sections.py', command)
        self.assertIn('MN103FixCallFrames.java', command)
        self.assertNotIn('-overwrite', command)
        self.assertIn('-noanalysis', module.import_command(Path('/ghidra'), Path('/out')))

    def test_query_reports_data_calls_and_truncation(self):
        module = load('find_refs')
        address = lambda n: SimpleNamespace(getOffset=lambda: n)
        function = SimpleNamespace(getName=lambda: 'caller', getEntryPoint=lambda: address(0x60000100))

        class Kind:
            def __init__(self, call):
                self.call = call
            def isCall(self):
                return self.call
            def __str__(self):
                return 'CALL' if self.call else 'DATA'

        refs = [SimpleNamespace(getFromAddress=lambda: address(0x60000120),
                                getReferenceType=lambda: Kind(True)),
                SimpleNamespace(getFromAddress=lambda: address(0x60000200),
                                getReferenceType=lambda: Kind(False))]
        program = SimpleNamespace(
            getReferenceManager=lambda: SimpleNamespace(getReferencesTo=lambda _: refs),
            getFunctionManager=lambda: SimpleNamespace(getFunctionContaining=lambda _: function))
        result = module.query(program, address(0x60023818), limit=1)
        self.assertEqual(result['callers'], ['0x60000100'])
        self.assertEqual(result['xref_count'], 2)
        self.assertTrue(result['truncated'])
        self.assertEqual(len(result['xrefs']), 1)
        with self.assertRaises(ValueError):
            module.parse_address('0x100000000')


if __name__ == '__main__':
    unittest.main()
