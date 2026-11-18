from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import symbols_export as se


class SymbolsTests(unittest.TestCase):
    def test_ld_ignores_comments_and_non_address_constants(self):
        text = '/* fake = 0x60000000; */ PM_ID = 111; malloc = 0x60023818; .ext2 0x605af4b0 : { *(.ext2) }'
        rows = list(se.ld_symbols(text, 'layout.ld'))
        self.assertEqual([r['name'] for r in rows], ['malloc', 'ext2'])

    def test_dedup_preserves_sources_conflicts_and_aliases(self):
        rows = [dict(name=n, address=a, kind='function', source_file=s) for n, a, s in
                [('foo', 1, 'a'), ('foo', 1, 'b'), ('foo', 2, 'c'), ('alias', 1, 'a')]]
        result = se.collect(rows + rows)
        self.assertEqual(len(result['symbols']), 3)
        self.assertEqual(len(result['conflicts']), 1)
        foo = next(r for r in result['symbols'] if r['name'] == 'foo' and r['address'] == 1)
        self.assertEqual(foo['source_files'], ['a', 'b'])

    def test_atlas_end_and_numeric_yaml(self):
        doc = {'records': [dict(id='reference.test', category='layout',
                                address=dict(value=0x60843000, end='0x60846000', space='runtime-cached'))]}
        rows = list(se.atlas_symbols(doc, 'atlas.yaml'))
        self.assertEqual([r['name'] for r in rows], ['reference.test', 'reference.test.end'])

    def test_patch_addresses_in_all_named_containers(self):
        doc = dict(ranges=[dict(name='hook', address='0x602d19b6', bytes=5)],
                   assembly=[dict(name='wb', sections={'wb_hook': '0x602d19b6'})],
                   components={'0x100': {'cpu_base': '0x60021020'}},
                   data_edits=[dict(name='edit', address='0x602d0000', after='8cee4e60')])
        rows = list(se.json_symbols(doc, 'patch.json'))
        self.assertEqual(len(rows), 4)
        self.assertIn('hook', [r['name'] for r in rows])
        self.assertIn('wb_hook', [r['name'] for r in rows])

    def test_section_definitions_from_patch_and_linker_merge(self):
        rows = list(se.ld_symbols('.ext2 0x605af4b0 : { *(.ext2) }', 'layout.ld'))
        rows += list(se.json_symbols({'assembly': [{'sections': {'ext2': '0x605af4b0'}}]}, 'patch.json'))
        result = se.collect(rows)
        self.assertEqual(len(result['symbols']), 1)
        self.assertEqual(result['symbols'][0]['source_files'], ['layout.ld', 'patch.json'])


if __name__ == '__main__':
    unittest.main()
