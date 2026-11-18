"""Synthetic formatting, index, batching and unavailable-runtime tests."""
import contextlib
import io
import json
from pathlib import Path
import struct
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'tools/ghidra'
sys.path.insert(0, str(SCRIPTS))
import query_common as common
import query as runner


class QueryTests(unittest.TestCase):
    def test_immediate_index_unsigned_duplicates_and_empty(self):
        data = b''.join(struct.pack('>II', v, a) for v, a in
                        [(0, 100), (907, 200), (907, 300), (911, 400), (0xffffffff, 500)])
        handle = io.BytesIO(data)
        self.assertEqual(list(common.index_addresses(handle, 907)), [200, 300])
        self.assertEqual(list(common.index_addresses(handle, 908)), [])
        self.assertEqual(list(common.index_addresses(handle, 0xffffffff)), [500])
        self.assertEqual(list(common.index_addresses(io.BytesIO(), 907)), [])
        with self.assertRaisesRegex(ValueError, 'truncated'):
            list(common.index_addresses(io.BytesIO(data[:-1]), 907))

    def test_value_limits_and_signed_normalization(self):
        self.assertEqual(common.immediate_value('-1'), 0xffffffff)
        self.assertEqual(common.address_value('0x60023818'), 0x60023818)
        for value in ('-1', '0x100000000'):
            with self.assertRaises(ValueError):
                common.address_value(value)

    def test_decompile_truncation_handles_long_lines_and_empty(self):
        result = common.truncate_lines('a\nb\nc\n', 2)
        self.assertEqual(result, {'lines': ['a', 'b'], 'total_lines': 3, 'truncated': True})
        self.assertEqual(common.truncate_lines('', 10)['lines'], [])
        self.assertTrue(common.truncate_lines('x' * 100, 10, max_chars=10)['truncated'])

    def test_log_extraction_ignores_ghidra_noise_and_trailing_logger(self):
        output = 'INFO something\nINFO script> OM5_QUERY {"ghidra_run":true,"function":null} (GhidraScript)\n'
        output += 'INFO find_refs.py> OM5_REFS {"xref_count":0} (GhidraScript)\n'
        self.assertEqual(runner.extract_results(output), [{'ghidra_run': True, 'function': None}, {'xref_count': 0}])

    def test_batch_validation_and_read_only_command(self):
        jobs = runner.jobs_from_data([{'script': 'decomp', 'args': ['malloc', '--max-lines', '4']}])
        command = runner.command_for(Path('/g'), Path('/p'), jobs, Path('/missing-index'))
        self.assertIn('-readOnly', command)
        self.assertIn('-noanalysis', command)
        self.assertIn('--max-lines', command)
        for invalid in ([], [{'script': 'arbitrary.py', 'args': ['x']}], [{'script': 'decomp', 'args': []}]):
            with self.assertRaises(ValueError):
                runner.jobs_from_data(invalid)

    def test_unavailable_runtime_reports_not_run(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            status = runner.main(['--ghidra', '/__absent_ghidra__', 'func_at', '0x60023818'])
        self.assertEqual(status, 1)
        self.assertFalse(json.loads(output.getvalue())['ghidra_run'])

    def test_direct_cpython_script_does_not_claim_ghidra(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(common.execute({}, lambda: {'success': True}), 1)
        self.assertFalse(json.loads(output.getvalue())['ghidra_run'])


if __name__ == '__main__':
    unittest.main()
