class Roster:
	POSITION_ORDER = {
		"QB": 0,
		"RB": 1,
		"WR": 2,
		"TE": 3,
		"DST": 4
	}

	def __init__(self):
		self.players = []

	def add_player(self, player):
		self.players.append(player)

	def spent(self):
		return sum(map(lambda x: x.cost, self.players))

	def projected(self):
		return sum(map(lambda x: x.proj, self.players))/100.0

	def position_order(self, player):
		return self.POSITION_ORDER[player.pos]

	def sorted_players(self):
		sortedp = sorted(self.players, key=self.position_order)
		rbs = filter(lambda x: x.pos=='RB', self.players )
		wrs = filter(lambda x: x.pos=='WR', self.players )

		if (len(rbs)>2):
			sortedp.insert(7,sortedp.pop(3))
		elif (len(wrs)>3):
			sortedp.insert(7,sortedp.pop(6))

		return sortedp

	def __repr__(self):
		s = '\n'.join(str(x) for x in self.sorted_players())
		s += "\nProjected Score: %s" % self.projected()
		s += "\tCost: $%s\n" % self.spent()
		return s

class Player:
	def __init__(self, pos, name, cost,matchup=None, team=None, risk=0, proj=0, code='aa', marked=None):
		self.pos = pos
		self.name = name
		self.code = code
		self.dropoff = 0
		self.team = team
		self.matchup = matchup
		self.opps_team = matchup.split()[0].replace(team,'').replace('@','')
		self.cost = int(cost)
		self.risk = risk
		self.proj = proj
		self.marked = marked
		self.cost_ranking = 0

	def __repr__(self):
		return "[{0: <2}] {1: <20} {2} {3} (${4}, {5})".format(self.pos, \
									self.name, \
									self.team, \
									self.matchup, \
									self.cost, \
									self.proj/100.0)
