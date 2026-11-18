#!/usr/bin/env python3
"""Run bounded queries against the saved Ghidra project; print JSON only."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
QUERIES = ('find_refs', 'callees', 'func_at', 'find_imm', 'decomp')


def jobs_from_data(data):
    if not isinstance(data, list) or not 1 <= len(data) <= 20:
        raise ValueError('batch must contain 1..20 query objects')
    jobs = []
    for row in data:
        if not isinstance(row, dict) or row.get('script') not in QUERIES:
            raise ValueError('unknown query script')
        args = row.get('args', [])
        if not isinstance(args, list) or not args or not all(isinstance(a, str) for a in args):
            raise ValueError('query args must be a nonempty list of strings')
        jobs.append((row['script'], args))
    return jobs


def extract_results(output):
    decoder = json.JSONDecoder()
    rows = []
    for line in output.splitlines():
        match = re.search(r'OM5_(?:QUERY|REFS) (\{.*)', line)
        if match:
            rows.append(decoder.raw_decode(match.group(1))[0])
    return rows


def command_for(ghidra, project_dir, jobs, index):
    executable = ghidra / 'support' / ('analyzeHeadless.bat' if sys.platform == 'win32' else 'analyzeHeadless')
    command = [str(executable), str(project_dir), 'E148-1100', '-process', 'main.expanded.bin',
               '-readOnly', '-noanalysis', '-scriptPath', str(HERE)]
    for script, arguments in jobs:
        args = list(arguments)
        if script == 'find_imm' and index.is_file() and '--index' not in args:
            args.extend(['--index', str(index)])
        command.extend(['-postScript', script + '.py'] + args)
    return command


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ghidra', type=Path, default=Path(os.environ.get('GHIDRA_HOME', ROOT / 'generated/runtime/ghidra_11.4.2_PUBLIC')))
    parser.add_argument('--java-home', type=Path)
    parser.add_argument('--project-dir', type=Path, default=ROOT / 'generated/ghidra/projects')
    parser.add_argument('--batch', type=Path)
    parser.add_argument('script', nargs='?', choices=QUERIES)
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    started, ghidra_run = time.time(), False
    try:
        if args.batch:
            if args.script:
                raise ValueError('use a batch or a single script')
            jobs = jobs_from_data(json.loads(args.batch.read_text(encoding='utf-8')))
        else:
            jobs = jobs_from_data([{'script': args.script, 'args': args.arguments}])
        command = command_for(args.ghidra.resolve(), args.project_dir.resolve(), jobs,
                              args.project_dir.resolve().parent / 'immediates.idx')
        if not Path(command[0]).is_file() or not (args.project_dir / 'E148-1100.gpr').is_file():
            raise ValueError('Ghidra installation or saved project unavailable')
        environment = os.environ.copy()
        java_home = args.java_home
        if java_home is None and not environment.get('JAVA_HOME'):
            local = ROOT / 'generated/runtime/jdk-21.0.9+10'
            if local.is_dir():
                java_home = local
        if java_home:
            environment['JAVA_HOME'] = str(java_home.resolve())
        logs = ROOT / 'generated/ghidra/query-logs'
        logs.mkdir(parents=True, exist_ok=True)
        log = logs / (datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '-%s.log' % os.getpid())
        with log.open('w', encoding='utf-8') as handle:
            ghidra_run = True
            process = subprocess.run(command, env=environment, stdout=handle, stderr=subprocess.STDOUT, check=False)
        results = extract_results(log.read_text(encoding='utf-8', errors='replace'))
        if process.returncode or len(results) != len(jobs):
            raise ValueError('Ghidra failed or a query produced no result; inspect ' + str(log))
        payload = {'ghidra_run': True, 'elapsed_seconds': round(time.time()-started, 3), 'results': results}
        print(json.dumps(payload, separators=(',', ':')))
        return 1 if any('error' in r for r in results) else 0
    except (OSError, ValueError) as exc:
        print(json.dumps({'ghidra_run': ghidra_run, 'error': str(exc)}, separators=(',', ':')))
        return 1


if __name__ == '__main__':
    sys.exit(main())
