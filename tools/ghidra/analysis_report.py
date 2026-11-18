# Persist full-analysis timing and coverage after the MN103 call-frame fixer.
# @category OM5
import json
import time


def run():
    from ghidra.app.util.headless import HeadlessAnalyzer
    args = getScriptArgs()
    if len(args) != 1:
        raise ValueError('analysis_report.py REPORT.JSON')
    with open(args[0], 'r') as handle:
        report = json.load(handle)
    report.update(finished_unix=time.time(),
                  elapsed_seconds=round(time.time()-report['started_unix'], 3),
                  function_count=currentProgram.getFunctionManager().getFunctionCount(),
                  instruction_count=currentProgram.getListing().getNumInstructions(),
                  language=str(currentProgram.getLanguageID()),
                  full_auto_analysis_complete=not HeadlessAnalyzer.getInstance().checkAnalysisTimedOut())
    with open(args[0], 'w') as handle:
        json.dump(report, handle, indent=2)
    println('OM5_ANALYSIS_REPORT ' + json.dumps(report, separators=(',', ':')))


if __name__ == '__main__':
    run()
