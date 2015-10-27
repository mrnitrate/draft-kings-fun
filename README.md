Special thanks to BenBrostoff. I currently use data from [fantasyfootballanalytics.net](http://apps.fantasyfootballanalytics.net/projections) as the criteria to optimize on.

Pre-reqs:

* [ortools](https://developers.google.com/optimization/installing?hl=en)

To run:
Place dk-salaries.csv(from draftkings) and FFA-CustomRankings.csv( from [fantasyfootballanalytics.net](http://apps.fantasyfootballanalytics.net/projections)) in ./data folder

<pre><code>./optimize.py </pre></code>

Arguments can also be passed to run the optimizer multiple times while eliminating previous solutions. For instance, to run three different iterations and generate three different optimal rosters:

<pre><code>./optimize.py -i 3</pre></code>

To do:
* More data 
* More constraints 
* Support Different Start Times from one salary csv
* Different tuned solvers for specific DFS game types ie. GPP , H2H
* Optimal Bankroll Management and game mix 
* 




	

