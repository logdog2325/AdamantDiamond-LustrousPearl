"""The Battle Frontier's core, checked offline in one run (notes/PLATINUM_FRONTIER.md "Checks").

    python3 b2tools/platinum_frontier_check.py [SEEDS]

1. b2tools/frontier_script.py check: every frontier script of Platinum's dump decodes fully and matches the decomp's sources.
2. b2tools/platinum_frontier_data.py check: the Frontier's Trainers, sets, names, lines, the Tower's tables, the marts.
3. b2tools/platinum_frontier_host/run.sh: the Battle Tower's rules, Platinum's own C against the code the ROM runs (the same
   opponents for the same random numbers, the Battle Points, the IVs, the team picks).
4. (plat-factory) b2tools/platinum_factory_host/run.sh: the Battle Factory's rules, Platinum's own C against
   src/pearlb2/plat_factory/factory_rules.c (the Trainers, rentals, opponents, swaps, records, Battle Points, the save).
Each under a watchdog (10 minutes); the first that fails stops the run (exit 1).
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('FRONTIER_HOST_OUT', os.path.join(os.environ.get('TMPDIR', '/tmp'), 'platinum_frontier_host'))


def run(name, cmd):
    print(f'== {name}', flush=True)
    r = subprocess.run(['timeout', '600'] + cmd, text=True, capture_output=True, env={**os.environ, 'FRONTIER_HOST_OUT': OUT})
    out = (r.stdout + r.stderr).strip().split('\n')
    print('\n'.join(out[-12:]))
    if r.returncode:
        print(f'{name}: FAILED ({r.returncode})')
        sys.exit(1)


def main(argv):
    seeds = argv[0] if argv else '2000'
    run('the script language', [sys.executable, os.path.join(HERE, 'frontier_script.py'), 'check'])
    run('the data', [sys.executable, os.path.join(HERE, 'platinum_frontier_data.py'), 'check'])
    run('the Tower\'s rules', [os.path.join(HERE, 'platinum_frontier_host', 'run.sh'), seeds])
    # ---- plat-factory
    run('the Factory\'s rules', [os.path.join(HERE, 'platinum_factory_host', 'run.sh'), str(max(1, int(seeds) // 10))])
    # ---- end plat-factory
    print('all passed')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
