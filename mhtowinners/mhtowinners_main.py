from river_mwclient.esports_client import EsportsClient
from river_mwclient.auth_credentials import AuthCredentials
import lol_esports_parser
import mwparserfromhell
import logging


def tl_has(tl, param):
	return tl.has(param) and tl.get(param).value.strip() != ''


class MhToWinnersRunner(object):
	def __init__(self, site: EsportsClient):
		self.site = site
		self.summary = 'Discover sides & winners from the MH & populate in the row'
	
	def run(self):
		pages_to_edit = self.site.cargo_client.query(
			tables="MatchScheduleGame=MSG,MatchSchedule=MS",
			join_on="MSG.UniqueMatch=MS.UniqueMatch",
			where="(MSG.Blue IS NULL OR MSG.Red IS NULL OR MSG.Winner IS NULL) AND MSG.MatchHistory Like \"%leagueoflegends%\"",
			fields="MSG._pageName=Page,MSG.OverviewPage=OverviewPage",
			limit='max',
			order_by="MS.DateTime_UTC DESC",
			group_by="MSG._pageName"
		)
		if not pages_to_edit:
			return
		self.update_pages(pages_to_edit)
		
	def update_pages(self, pages_to_edit):
		for item in pages_to_edit:
			# print(item)
			page = self.site.client.pages[item['Page']]
			text = page.text()
			wikitext = mwparserfromhell.parse(text)
			self.update_wikitext(wikitext, item['OverviewPage'])
			new_text = str(wikitext)
			if new_text != text:
				page.save(new_text, summary=self.summary)
	
	def update_wikitext(self, wikitext, overview_page):
		for template in wikitext.filter_templates():
			if not template.name.matches('MatchSchedule/Game'):
				continue
			if not tl_has(template, 'mh'):
				continue
			if tl_has(template, 'blue') and tl_has(template, 'red') and tl_has(template, 'winner'):
				continue
			if 'gameHash' not in template.get('mh').value.strip():
				continue
			mh_url = (
				template.get('mh').value.strip()
			)
			# print(mh_url)
			game = lol_esports_parser.get_riot_game(mh_url, add_names=False)
			blue = game["teams"]["BLUE"]['name']
			red = game["teams"]["RED"]['name']
			blue_team = self.site.cache.get_team_from_event_tricode(overview_page, blue)
			red_team = self.site.cache.get_team_from_event_tricode(overview_page, red)
			if blue_team is not None and red_team is not None:
				template.add('blue', blue_team)
				template.add('red', red_team)
				if game["winner"] == "BLUE":
					template.add('winner', "1")
				elif game["winner"] == "RED":
					template.add('winner', "2")
			
		
if __name__ == '__main__':
	credentials = AuthCredentials(user_file='me')
	site = EsportsClient('lol', credentials=credentials)  # Set wiki
	MhToWinnersRunner(site).run()
