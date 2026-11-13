"""The Battle Hall, checked offline in one run (notes/PLATINUM_FRONTIER.md "The Battle Hall").

    python3 b2tools/platinum_hall_check.py [SEEDS]

1. b2tools/platinum_hall_data.py check: the Hall's sets, opponents, their types, the Trainer class tables, found in the dump.
2. b2tools/platinum_hall_host/run.sh: the Hall's rules, Platinum's own C against ours (the decomp's hall_rules.c), with the same
   random numbers: the tables, SEEDS x 4 challenges (Init, the grid, the next opponent, the battle's setup and its Pokémon, wins,
   rank-ups, rounds, BP, losses, the win records, resumes), and sweeps of the level and the opponent draws.
Each under a watchdog (10 minutes); the first that fails stops the run (exit 1).
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('HALL_HOST_OUT', os.path.join(os.environ.get('TMPDIR', '/tmp'), 'platinum_hall_host'))


def run(name, cmd):
    print(f'== {name}', flush=True)
    r = subprocess.run(['timeout', '600'] + cmd, text=True, capture_output=True, env={**os.environ, 'HALL_HOST_OUT': OUT})
    out = [l for l in (r.stdout + r.stderr).strip().split('\n') if 'warning:' not in l]
    print('\n'.join(out[-8:]))
    if r.returncode:
        print(f'{name}: FAILED ({r.returncode})')
        sys.exit(1)


def main(argv):
    seeds = argv[0] if argv else '2000'
    run('the data', [sys.executable, os.path.join(HERE, 'platinum_hall_data.py'), 'check'])
    run('the Hall\'s rules', [os.path.join(HERE, 'platinum_hall_host', 'run.sh'), seeds])
    print('all passed')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
