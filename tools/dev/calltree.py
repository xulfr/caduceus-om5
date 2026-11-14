#!/usr/bin/env python3
"""Read a call log written by tools/dev/calls.mjs.

    calltree.py LOG tree TARGET [DEPTH] [LINES] [OCCURRENCE]   the calls made below a call to TARGET (hex, no 0x)
    calltree.py LOG chain LINE [LINE ...]                      the callers above a log line (1-based)
    calltree.py LOG events                                     the GUI events dispatched (0x60d41952 on E148 1.1)
"""
import sys


def main():
    log = [l.split() for l in open(sys.argv[1]) if l.strip()]
    what = sys.argv[2]
    if what == 'events':
        print('; '.join(f'{i + 1} {l[3]}' for i, l in enumerate(log) if l[2] == '60d41952'))
    elif what == 'chain':
        for arg in sys.argv[3:]:
            at = int(arg) - 1
            chain, sp = [], int(log[at][0], 16)
            for j in range(at - 1, -1, -1):
                s = int(log[j][0], 16)
                if sp < s < sp + 0x2000:
                    chain.append((j + 1, log[j])); sp = s
                if len(chain) > 14:
                    break
            for j, l in reversed(chain):
                print(j, ' '.join(l))
            print(arg, ' '.join(log[at]), '\n')
    else:
        target = sys.argv[3]
        depth = int(sys.argv[4]) if len(sys.argv) > 4 else 4
        lines = int(sys.argv[5]) if len(sys.argv) > 5 else 200
        skip = int(sys.argv[6]) if len(sys.argv) > 6 else 0
        for i, l in enumerate(log):
            if l[2] != target:
                continue
            if skip:
                skip -= 1; continue
            top, shown, stack = int(l[0], 16), 0, []
            print(' '.join(l))
            for m in log[i + 1:]:
                sp = int(m[0], 16)
                if sp >= top or top - sp > 0x4000:
                    break
                while stack and sp >= stack[-1]:
                    stack.pop()
                stack.append(sp)
                if len(stack) <= depth:
                    print('  ' * len(stack) + ' '.join(m[1:])); shown += 1
                    if shown >= lines:
                        break
            break


if __name__ == '__main__':
    main()
