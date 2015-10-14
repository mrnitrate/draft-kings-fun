# A huge thanks to swanson
# this solution is almost wholly based off
# https://github.com/swanson/degenerate

import csv
from sys import argv
import time
import argparse
from ortools.linear_solver import pywraplp

from orm import Player, Roster
from constants import *

parser = argparse.ArgumentParser()

all_players = []

for opt in OPTIMIZE_COMMAND_LINE:
	parser.add_argument(opt[0], help=opt[1], default=opt[2])

args = parser.parse_args()

def check_missing_players(all_players, min_cost, e_raise):
	'''
	check for significant missing players
	as names from different data do not match up
	continues or stops based on inputs
	'''
	contained_report = len(filter(lambda x: x.marked == 'Y', all_players))
	total_report = len(all_players)

	miss = len(filter(lambda x: x.marked != 'Y' and x.cost > min_cost,
						 all_players))

	if e_raise < miss:
		print 'Got {0} out of {1} total'.format(str(contained_report),
												str(total_report))
		raise Exception('Total missing players at price point: ' + str(miss))


def run_solver(solver, all_players, max_flex):
	'''
	handle or-tools logic
	'''


	'''
	Setup Binary Player variables
	'''
	variables = []
	for player in all_players:
		variables.append(solver.IntVar(0, 1, player.code))


	'''
	Setup Maximization over player point projections
	'''
	objective = solver.Objective()
	objective.SetMaximization()
	for i, player in enumerate(all_players):
		objective.SetCoefficient(variables[i], player.proj)


	'''
	Add Salary Cap Constraint
	'''
	salary_cap = solver.Constraint(SALARY_CAP-5000, SALARY_CAP)
	for i, player in enumerate(all_players):
		salary_cap.SetCoefficient(variables[i], player.cost)


	'''
	Add Player Position constraints including flex position
	'''
	flex_rb = solver.IntVar(0, 1, 'Flex_RB')
	flex_wr = solver.IntVar(0, 1, 'Flex_WR')
	flex_te = solver.IntVar(0, 1, 'Flex_TE')

	solver.Add(flex_rb+flex_wr+flex_te==1)

	for position, limit in max_flex:
		ids, players_by_pos = zip(*filter(lambda (x,_): x.pos in position, zip(all_players, variables)))
		if position == 'WR':
			  solver.Add(solver.Sum(players_by_pos) == limit+flex_wr)
		elif position == 'RB':
			  solver.Add(solver.Sum(players_by_pos) == limit+flex_rb)
		elif position == 'TE':
			  solver.Add(solver.Sum(players_by_pos) == limit+flex_te)
		else :
			solver.Add(solver.Sum(players_by_pos) == limit)


	'''
	Add min number of different teams player must be drafted from constraint (draftkings == 2)
	'''
	team_names = set([o.team for o in all_players])
	teams = []
	for team in team_names:
		teams.append(solver.IntVar(0, 1, team))
	solver.Add(solver.Sum(teams)>=2)

	for idx,team in enumerate(team_names):
		ids, players_by_team = zip(*filter(lambda (x,_): x.team in team, zip(all_players, variables)))
		solver.Add(teams[idx]<=solver.Sum(players_by_team))

	# o_players = filter(lambda x: x.pos in ['QB','WR','RB','TE'], all_players)
	# opps_team_names= set([o.opps_team for o in o_players])
	# opps_teams = []
	# for idx,team in enumerate(opps_team_names):
		# opps_teams.append(solver.IntVar(0,idx,'opps_'+team))
	# print(opps_teams)

#	  for position, limit in max_flex:
#		  position_cap = solver.Constraint(limit, limit)
#		  for i, player in enumerate(all_players):
#			  if position == player.pos:
#				  position_cap.SetCoefficient(variables[i], 1)

	return variables, solver.Solve()

'''
Load Salary and Prediction data from csv's
'''
def load(all_players):

	with open('data/dk-salaries-current-week.csv', 'rb') as csvfile:
		csvdata = csv.reader(csvfile, skipinitialspace=True)

		for idx, row in enumerate(csvdata):
			if idx > 0:
				pname = row[5]+" "+row[1]
				pname = pname.replace(".",'').replace("-",'').replace(" ","").lower()
				all_players.append(Player(row[0],row[1],row[2],
									row[3],row[5],0,0,pname))

	# give each a ranking
	all_players = sorted(all_players, key=lambda x: x.cost, reverse=True)
	for idx, x in enumerate(all_players):
		x.cost_ranking = idx + 1

	with open('data/FFA-CustomRankings.csv', 'rb') as csvfile:
		csvdata = csv.DictReader(csvfile)
		mass_hold = [['playername', 'points', 'cost', 'ppd']]

		for row in csvdata:
			pname=row['team'].lower()+row['playername'].replace(".",'').replace("-",'').replace(" ","").lower()

			if row['points'] == 0 :
				points = 0
			else:
				points = int(repr(float(row['points'])*10).split('.')[0])

			if row['risk'] =='null' :
				risk = 0
			else:
				risk = int(repr(float(row['risk'])*10).split('.')[0])

			holder = row

			player = filter(lambda x: x.code in pname, all_players)
			try:
				player[0].proj = points
				player[0].risk = risk
				player[0].marked = 'Y'
				listify_holder = [
					pname,
					points
				]
				if '0.0' not in row['points'] or player[0].cost != 0:
					ppd = (float(row['points'])*10) / float(player[0].cost)
				else:
					ppd = 0
				listify_holder.extend([player[0].cost,
									   ppd * 100000])
				mass_hold.append(listify_holder)
			except Exception as e:
				pass
				#print(e,pname,player)

	check_missing_players(all_players, args.sp, args.mp)


'''
Removed previous optimal solution and run another iteration
'''
def run(all_players,max_flex, maxed_over):
	solver = pywraplp.Solver('FD',
							 pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

	variables, solution = run_solver(solver, all_players, max_flex)

	if solution == solver.OPTIMAL:
		roster = Roster()

		for i, player in enumerate(all_players):
			if variables[i].solution_value() == 1:
				roster.add_player(player)

		print "Optimal roster for: %s" % maxed_over
		print roster
		return roster
	else:
	  raise Exception('No solution error')


'''
Main Loop
'''
if __name__ == "__main__":
	load(all_players)
	rosters = []
	for x in xrange(0, int(args.i)):
		remove = []
		rosters.append(run(all_players,POSITION_LIMITS_FLEX, 'flex'))
		for roster in rosters:
			for player in roster.players:
				remove.append(player.code)
			remove_players = filter(lambda x: x.code in remove, all_players)
			sorted_remove = sorted(remove_players, key=lambda x: x.risk, reverse=True)
			bad = [p.code for p in sorted_remove[:1]]
			all_players = filter(lambda x: x.code not in bad, all_players)