#coding:utf-8

import sublime, sublime_plugin, json, urllib, urllib2, webbrowser

class WebfontCommand(sublime_plugin.WindowCommand):

	URL = 'http://webfont.ru/api/list.json'
	SITE_URL = 'http://webfont.ru/'

	def __init__(self, window):
		super(WebfontCommand, self).__init__(window)
		self.font_data = self.download_info()
		if self.font_data is None:
			sublime.status_message(u'не удалось обновить список шрифтов')

	def download_info(self):		
		try:
			fd = urllib2.urlopen(self.URL, timeout=5)
			result = json.load(fd)
		except Exception as e:
			result = None
		return result

	def run(self):

		name_list = [u'* перейти на webfont.ru', u'* обновить список шрифтов']
		if self.font_data is not None:
			for i in self.font_data:
				name_list.append(i['name'])
		self.window.show_quick_panel(name_list, self.on_done)

	def insert(self, text):
		view = self.window.active_view()		
		edit = self.window.active_view().begin_edit()		
		pos = view.sel()[0].a
		view.insert(edit, pos, text)		
		view.end_edit(edit)

	def on_done(self, index):
		if index < 0: return
		if index == 0:
			try:
				webbrowser.open(self.SITE_URL)
			except:
				sublime.status_message(u'не удалось открыть страницу "%s"' % self.SITE_URL)
		elif index == 1:
			old_font_data = self.font_data
			self.font_data = self.download_info()
			if self.font_data is None:
				sublime.status_message(u'не удалось обновить список шрифтов')
				self.font_data = old_font_data
			self.run()
		else:			
			text = self.font_data[index-2]['import'] + '\n' + self.font_data[index-2]['comments']
			self.insert(text)		
		