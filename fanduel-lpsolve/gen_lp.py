# -*- coding: utf-8 -*-
"""
Generates a linear program (in lp_solve's file format) which find an optimal FanDuel team
using user-supplied player data.

Example usage:
  $ python bin/gen_lp.py ffpros-9-22-2015.csv --salary-cap 60000 | lp_solve'
  $ python bin/gen_lp.py ffpros-9-22-2015.csv | lp_solve | grep '_' | awk '{print $2, $1}' | grep '1 '
"""

from collections import namedtuple
from argparse import ArgumentParser
from csv import DictReader
import random

PlayerDatum = namedtuple('PlayerDatum', ['name', 'position', 'salary', 'projection'])


def load_player_data(filename):
    """
    Loads player data from a comma-separated file with the following columns: PLAYER, POSITION, SALARY, PROJECTION

    :param filename: The filename of the .csv file
    :return: A dictionary mapping player position to lists of PlayerDatum entries
    """
    player_data = {'QB': [], 'RB': [], 'WR': [], 'TE': [], 'K': [], 'D': []}

    with open(filename) as fin:
        data_reader = DictReader(fin)

        for row in data_reader:
            player_datum = PlayerDatum(
                name       = row['PLAYER'],
                position   = row['POSITION'],
                salary     = int(row['SALARY']),
                projection = float(row['PROJECTION'])
            )
            player_data[player_datum.position].append(player_datum)

    return player_data


def write_lp_file(player_data, salary_cap, proj_jitter):
    """
    Write an lp_solve .lp file to stdout.

    :param player_data: A dictionary mapping player position to lists of PlayerDatum entries
    :param salary_cap: The maximum salary amount for an individual team.
    """
    def get_var_name(player):
        return '%s_%s' % (player.position, filter(str.isalpha, player.name))

    # Get a list of all the players:
    all_players = []
    for position, position_player_data in player_data.items():
        for p in position_player_data:
            all_players.append(p)

    # Write the objective function:
    print 'max: %s;' % ' + '.join(['%s %s' % (p.projection * random.uniform(1.0-proj_jitter, 1.0+proj_jitter), get_var_name(p)) for p in all_players])

    # Write the position constraints:
    print 'qb_lim: %s = 1;' % ' + '.join([get_var_name(p) for p in player_data['QB']])
    print 'rb_lim: %s = 2;' % ' + '.join([get_var_name(p) for p in player_data['RB']])
    print 'wr_lim: %s = 3;' % ' + '.join([get_var_name(p) for p in player_data['WR']])
    print 'te_lim: %s = 1;' % ' + '.join([get_var_name(p) for p in player_data['TE']])
    print 'k_lim: %s = 1;' % ' + '.join([get_var_name(p) for p in player_data['K']])
    print 'd_lim: %s = 1;' % ' + '.join([get_var_name(p) for p in player_data['D']])

    # Write the salary constraint:
    print 'sal_lim: %s <= %s;' % (' + '.join(['%s %s' % (p.salary, get_var_name(p)) for p in all_players]), salary_cap)

    # Write the binary variables:
    print 'bin %s;' % ' '.join(get_var_name(p) for p in all_players)


if __name__ == '__main__':
    # Read command-line arguments:
    arg_parser = ArgumentParser()
    arg_parser.add_argument('player_data_file', help='The .CSV file containing player data')
    arg_parser.add_argument('--salary-cap', type=int, default=60000, help='The team salary cap restriction')
    arg_parser.add_argument('--min-player-proj', type=float, default=2.718, help='Minimum point projection required to consider a player.')
    arg_parser.add_argument('--proj-jitter', type=float, default=0.0, help='Adds a random adjustment to player projections')
    args = arg_parser.parse_args()

    # Load player data from the input file:
    player_data = load_player_data(args.player_data_file)

    # Filter players with low point projections (they're almost never relevant with real data):
    for position in player_data.keys():
        player_data[position] = filter(lambda p: p.projection >= args.min_player_proj, player_data[position])

    # Write the .lp file:
    write_lp_file(player_data, args.salary_cap, args.proj_jitter)
