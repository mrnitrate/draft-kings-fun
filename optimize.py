#!/usr/bin/python

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
for opt in OPTIMIZE_COMMAND_LINE:
	parser.add_argument(opt[0], help=opt[1], default=opt[2])
args = parser.parse_args()

'''
Load Salary and Prediction data from csv's
'''
def load_players():
	all_players = []
	with open('data/dk-salaries.csv', 'rb') as csvfile:
		csvdata = csv.reader(csvfile, skipinitialspace=True)

		for idx, row in enumerate(csvdata):
			if idx > 0:
				pname = row[5]+" "+row[1]
				pname = pname.replace(".",'').replace("-",'').replace(" ","").lower()
				all_players.append(Player(row[0],row[1].strip(),row[2],row[3],row[5],0,0,pname))

	# give each a ranking
	all_players = sorted(all_players, key=lambda x: x.cost, reverse=True)
	for idx, x in enumerate(all_players):
		x.cost_ranking = idx + 1

	with open('data/FFA-CustomRankings.csv', 'rb') as csvfile:
		csvdata = csv.DictReader(csvfile)

		for row in csvdata:
			pname=row['team'].lower()+row['playername'].replace(".",'').replace("-",'').replace(" ","").lower()
			player = filter(lambda x: x.code in pname, all_players)
			try:
				if row['upper'] == 0 :
					points = 0
				else:
					points = int(repr(float(row['upper'])*100).split('.')[0])

				if row['dropoff'] == 'null' :
					dropoff = 0
				else:
					dropoff = int(repr(float(row['dropoff'])).split('.')[0])

				if row['risk'] =='null' :
					risk = 0
				else:
					risk = int(repr(float(row['risk'])*100).split('.')[0])

				if '0.0' not in row['upper'] or player[0].cost != 0:
					ppd = (float(row['upper'])*100) / float(player[0].cost)
				else:
					ppd = 0

				player[0].proj = points
				player[0].risk = risk
				player[0].marked = 'Y'
				player[0].dropoff = dropoff

			except Exception as e:
				pass
				#print(e,pname,player)

	check_missing_players(all_players, args.sp, args.mp)
	return all_players 

'''
check for significant missing players
as names from different data do not match up
continues or stops based on inputs
'''
def check_missing_players(all_players, min_cost, e_raise):
	contained_report = len(filter(lambda x: x.marked == 'Y', all_players))
	total_report = len(all_players)
	miss = len(filter(lambda x: x.marked != 'Y' and x.cost > min_cost,all_players))
	if e_raise < miss:
		print 'Got {0} out of {1} total'.format(str(contained_report),str(total_report))
		raise Exception('Total missing players at price point: ' + str(miss))

'''
handle or-tools logic
'''
def run_solver(all_players,depth):
	solver = pywraplp.Solver('FD', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

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
	salary_cap = solver.Constraint(SALARY_CAP-1000, SALARY_CAP)
	for i, player in enumerate(all_players):
		salary_cap.SetCoefficient(variables[i], player.cost)

	'''
	Add Player Position constraints including flex position
	'''
	flex_rb = solver.IntVar(0, 1, 'Flex_RB')
	flex_wr = solver.IntVar(0, 1, 'Flex_WR')
	flex_te = solver.IntVar(0, 1, 'Flex_TE')

	solver.Add(flex_rb+flex_wr+flex_te==1)

	for position, limit in POSITION_LIMITS_FLEX:
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
	Add min number of different teams players must be drafted from constraint (draftkings == 2)
	'''
	team_names = set([o.team for o in all_players])
	teams = []
	for team in team_names:
		teams.append(solver.IntVar(0, 1, team))
	solver.Add(solver.Sum(teams)>=2)

	for idx,team in enumerate(team_names):
		ids, players_by_team = zip(*filter(lambda (x,_): x.team in team, zip(all_players, variables)))
		solver.Add(teams[idx]<=solver.Sum(players_by_team))

	'''
	Add Defence cant play against any offense's player team constraint
	'''
	o_players = filter(lambda x: x.pos in ['QB','WR','RB','TE'], all_players)
	# opps_team_names= set([o.opps_team for o in o_players])
	# teams_obj = filter(lambda x: x.pos == 'DST' , all_players)
	# teams = set([o.team for o in teams_obj])

	# for opps_team in team_names:
		# if opps_team in teams :
			# ids, players_by_opps_team = zip(*filter(lambda (x,_): x.pos in ['QB','WR','RB','TE'] and x.opps_team in opps_team, zip(all_players, variables)))
			# idxs, defense = zip(*filter(lambda (x,_): x.pos == 'DST' and x.team in opps_team, zip(all_players, variables)))
			# solver.Add(solver.Sum(1-x for x in players_by_opps_team)+solver.Sum(1-x for x in defense)>=1)

	'''
	Add QB stacking (at least 1 wr or te on same team as QB) constraint
	'''
	offense_team_names = set([o.team for o in o_players])
	for o_team in offense_team_names:
		ids, players_by_team = zip(*filter(lambda (x,_): x.pos in ['WR','TE'] and x.team == o_team, zip(all_players, variables)))
		idxs, qb = zip(*filter(lambda (x,_): x.pos == 'QB' and x.team == o_team, zip(all_players, variables)))
		solver.Add(solver.Sum(players_by_team)>=solver.Sum(qb))

	'''
	Add Max of 1 qb wr te or rb per team constraint, NOT TO BE USED WITH QB STACKING
	'''
# 	for team in list(team_names):
# 		ids, players_by_team = zip(*filter(lambda (x,_): x.team in team and x.pos in ['WR','TE','RB','QB'], zip(all_players, variables)))
# 		solver.Add(solver.Sum(players_by_team)<=1)

	'''
	Add Max of 2 qb wr te or rb per game constraint
	'''
	for team in list(team_names)[:len(team_names)/2]:
		team_players = filter(lambda x: x.team in team, all_players)
		ids, players_by_game = zip(*filter(lambda (x,_): x.team in team or x.team in team_players[0].opps_team and x.pos in ['WR','TE','RB','QB'], zip(all_players, variables)))
		solver.Add(solver.Sum(players_by_game)<=2)
		
	'''
	Add remove previous solutions constraint and loop to generate X rosters
	'''
	rosters = []
	for x in xrange(depth):
		if rosters :
			ids, players_from_roster = zip(*filter(lambda (x,_): x in rosters[-1].sorted_players()  , zip(all_players, variables)))
			ids, players_not_from_roster = zip(*filter(lambda (x,_): x  not in rosters[-1].sorted_players()  , zip(all_players, variables)))
			solver.Add(solver.Sum(players_not_from_roster)+solver.Sum(1-x for x in players_from_roster)>=1)
		solution = solver.Solve()
		if solution == solver.OPTIMAL:
			roster = Roster()
			for i, player in enumerate(all_players):
				if variables[i].solution_value() == 1:
					roster.add_player(player)
			rosters.append(roster)
			print "Optimal roster iterations: %s" % x
			print roster
		else:
			raise Exception('No solution error')

	return rosters

'''
Write rosters to csv for bulk import to draftkings 
'''
def write_bulk_import_csv(rosters):
	with open('data/bulk-import.csv', 'wb') as csvfile:
		writer = csv.writer(csvfile,delimiter=',',quotechar='"',quoting=csv.QUOTE_NONNUMERIC)
		for roster in rosters:
			writer.writerow([x.name for x in roster.sorted_players()])
		
'''
Main Loop
'''
if __name__ == "__main__":
	all_players = load_players()
	rosters = run_solver(all_players,int(args.i))
	write_bulk_import_csv(rosters)