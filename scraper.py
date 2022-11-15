from sys import argv
import re
import csv
import requests
from bs4 import BeautifulSoup as BS

from constants import FFPRO

def build_fp_pages():
    return [
        FFPRO + '{0}.php?week={1}'.format(page, argv[1])
        for page in ['qb', 'rb', 'wr', 'te', 'k']
    ]

def scrape():
    hold = []
    hold.append(['playername', 'points'])
    for page in build_fp_pages():
	r = requests.get(page)
        soup = BS(r.text,"html5lib")
        for row in soup.find_all('tr',{'class': re.compile('mpb-available')}):
            #print(row)    
	    try:
		pnamesplit = str(row.find_all('td')[0].text).split(' ',3)
                pname = pnamesplit[2]+pnamesplit[0]+pnamesplit[1]
		hold.append([pname.replace(".",'').replace("-","").lower(),
                             str(row.find_all('td')[-1].text)])
                
            except Exception, e:
                print e

    with open('data/fan-pros.csv', 'w') as fp:
        w = csv.writer(fp, delimiter=',')
        w.writerows(hold)

if __name__ == "__main__":
    scrape()
