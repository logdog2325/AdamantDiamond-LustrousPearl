"""The Battle Castle, checked offline in one run (notes/PLATINUM_FRONTIER.md "The Battle Castle").

    python3 b2tools/platinum_castle_check.py [SEEDS]

1. b2tools/platinum_castle_data.py check: the Castle's tables (the round's Trainers, the BP, the rentals and their CP, the heal
   and rank-up costs) found in the dump and the same in castle_rules.c; the items the same numbers in Black 2.
2. b2tools/platinum_castle_host/run.sh: the Castle's rules, Platinum's own C (its challenge, its scene commands, its two screens'
   state machines) against ours (the decomp's castle_rules.c), with the same random numbers and the same choices: SEEDS seeds
   of challenges (purchases on both screens, passes, battles with carried HP and PP, CP, rounds, BP, Darach, rests resumed,
   retires, losses).
Each under a watchdog (10 minutes); the first that fails stops the run (exit 1).
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('CASTLE_HOST_OUT', os.path.join(os.environ.get('TMPDIR', '/tmp'), 'platinum_castle_host'))


def run(name, cmd):
    print(f'== {name}', flush=True)
    r = subprocess.run(['timeout', '600'] + cmd, text=True, capture_output=True, env={**os.environ, 'CASTLE_HOST_OUT': OUT})
    out = [l for l in (r.stdout + r.stderr).strip().split('\n') if 'warning:' not in l]
    print('\n'.join(out[-20:]))
    if r.returncode:
        print(f'{name}: FAILED ({r.returncode})')
        sys.exit(1)


def main(argv):
    seeds = argv[0] if argv else '2000'
    run('the data', [sys.executable, os.path.join(HERE, 'platinum_castle_data.py'), 'check'])
    run('the Castle\'s rules', [os.path.join(HERE, 'platinum_castle_host', 'run.sh'), seeds])
    print('all passed')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
