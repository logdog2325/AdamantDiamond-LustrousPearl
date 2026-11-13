"""The Battle Arcade, checked offline in one run (notes/PLATINUM_FRONTIER.md "The Battle Arcade").

    python3 b2tools/platinum_arcade_check.py [SEEDS]

1. b2tools/platinum_arcade_data.py check: the Arcade's tables (the round's Trainers, the free BP, the board's speed by round, the
   performance, the item and Berry pools, the BP, and the board's own: the cursor's frames, the effects by round and by battle, the
   kinds' weights and tiers) found in the dump's code and the same in arcade_rules.c; the items the same numbers in Black 2; the
   DS's division routine the same in Platinum and Black 2.
2. b2tools/platinum_arcade_host/run.sh: the Arcade's rules, Platinum's own C (its challenge, its scene commands, its game board's app
   frame by frame) against ours (the decomp's arcade_rules.c), with the same random numbers and the same choices: the LowerHP sweep,
   boards for every round, battle number, performance, speed and cursor, and SEEDS seeds of challenges.
Each under a watchdog (10 minutes); the first that fails stops the run (exit 1).
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('ARCADE_HOST_OUT', os.path.join(os.environ.get('TMPDIR', '/tmp'), 'platinum_arcade_host'))


def run(name, cmd):
    print(f'== {name}', flush=True)
    r = subprocess.run(['timeout', '600'] + cmd, text=True, capture_output=True, env={**os.environ, 'ARCADE_HOST_OUT': OUT})
    out = [l for l in (r.stdout + r.stderr).strip().split('\n') if 'warning:' not in l]
    print('\n'.join(out[-12:]))
    if r.returncode:
        print(f'{name}: FAILED ({r.returncode})')
        sys.exit(1)


def main(argv):
    seeds = argv[0] if argv else '2000'
    run('the data', [sys.executable, os.path.join(HERE, 'platinum_arcade_data.py'), 'check'])
    run('the Arcade\'s rules', [os.path.join(HERE, 'platinum_arcade_host', 'run.sh'), seeds])
    print('all passed')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
