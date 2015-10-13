FFPRO = 'http://www.fantasypros.com/nfl/projections/'

ALL_POS = ['QB', 'RB', 'WR', 'TE', 'DST']
ALL_POS_TEAM = ['QB', 'RB1', 'RB2',
                'WR1', 'WR2', 'WR3', 'FLEX',
                'TE', 'DST']

SALARY_CAP = 50000
ROSTER_SIZE = 9

POSITION_LIMITS_FLEX = [
  ["QB", 1],
  ["RB", 2],
  ["WR", 3],
  ["TE", 1],
  ["DST",  1]
]

OPTIMIZE_COMMAND_LINE = [
  ['-mp', 'missing players to allow', 100],
  ['-sp', 'salary threshold to ignore', 3000],
  ['-i', 'iterations to run', 3]
]