from redbot.core import commands
import rivercogutils as utils
import mwparserfromhell, re


class Redirects(commands.Cog):
	"""Fixes double redirects based on the wiki's Special:DoubleRedirects report"""
	
	def __init__(self, bot):
		self.bot = bot
		self.summary = 'Fixing double redirect'
	
	@commands.group(pass_context=True)
	async def redirects(self, ctx):
		pass
	
	@redirects.command(pass_context=True)
	async def double(self, ctx, wiki):
		site = await utils.login_if_possible(ctx, self.bot, wiki)
		if site is None:
			return
		result = site.client.api(action="query", list="querypage", qppage="DoubleRedirects")
		for item in result['query']['querypage']['results']:
			source_page = site.client.pages[item['title']]
			target_title = item['databaseResult']['c_title']
			target_namespace_number = int(item['databaseResult']['c_namespace'])
			target_namespace = site.client.namespaces[int(target_namespace_number)]
			target_page_name = '{}{}'.format(
				target_namespace + ':' if target_namespace != '' else '',
				target_title
			)
			source_page.save('#redirect[[%s]]' % target_page_name, summary=self.summary)
		
		return await ctx.send("Okay, should be done!")
