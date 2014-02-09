#coding:utf-8

import sublime, sublime_plugin
import json
import webbrowser
import zipfile
import os
import threading
import locale

SETTINGS_FILE = "WebFont.sublime-settings"

def is_st3():
	return sublime.version()[0] == '3'

if is_st3():
	import urllib.request
	import io	
else:
	import urllib2
	import cStringIO

def get_os_locale():
	os_locale = locale.getlocale()
	if os_locale is None:
		return 'en_US'
	else:
		if os_locale[0].startswith('en'):
			return 'en_US'
		else if os_locale[0].startswith('ru'):
			return 'ru_RU'
		else
			return 'en_US'

loc = {
	'en_US':{
		'cant_create_dir' : u'can\'t create dir: "%s"',
		'input_dir_name' : u'Enter dir name:',
		'current_dir' : u'current dir: "%s"',
		'cant_enter_dir' : u'can\'t enter dir "%s"; current dir: "%s"',
		'change_disk' : u'* change disk',
		'create_dir' : u'* create dir',
		'unpack_here' : u'* yes, unpack here',
		'level_up' : u'* go up',
		'cant_refresh_fonts' : u'can\'t update fonts list',
		'cant_download_font' : u'can\'t download font',
		'unpack_error' : u'unpacking error',
		'go_to_webfont' : u'* go to webfont.ru',
		'update_fonts_list' : u'* update fonts list',
		'download_font' : u'* download font',
		'download_complete' : u'font downloaded',
		'please_wait' : u'please wait',
		'cant_open_website' : u'can\'t open website "%s"'
	},

	'ru_RU':{
		'cant_create_dir' : u'невозможно создать каталог: "%s"',
		'input_dir_name' : u'Введите имя каталога:',
		'current_dir' : u'текущий каталог: "%s"',
		'cant_enter_dir' : u'невозможно войти в каталог "%s"; текущий каталог: "%s"',
		'change_disk' : u'* сменить диск',
		'create_dir' : u'* создать каталог',
		'unpack_here' : u'* да, распаковать сюда',
		'level_up' : u'* на уровень выше',
		'cant_refresh_fonts' : u'не удалось обновить список шрифтов',
		'cant_download_font' : u'не удалось скачать шрифт',
		'unpack_error' : u'при распаковке шрифта произошла ошибка',
		'go_to_webfont' : u'* перейти на webfont.ru',
		'update_fonts_list' : u'* обновить список шрифтов',
		'download_font' : u'* скачать шрифт',
		'download_complete' : u'шрифт успешно скачан',
		'please_wait' : u'немного подождите',
		'cant_open_website' : u'не удалось открыть страницу "%s"'
	}
}

current_loc = loc['en_US']

def _(id):
	return current_loc[id];


class DriveSelector:

	def __init__(self, window, callback):
		self.window = window
		self.callback = callback
		self.drive_list = None

	def _get_drives(self):
		import string
		drives = []
		wd = os.getcwd()
		for letter in string.lowercase:
			drive = u'%s:\\' % letter
			try:
				os.chdir(drive)
				drives.append(drive)
			except:
				pass

		os.chdir(wd)
		return drives

	def _on_done(self, index):
		if index < 0:
			self.callback(None)
		else:
			self.callback(self.drive_list[index])

	def _show_quick_panel(self, options, done):
		if is_st3():
			sublime.set_timeout(lambda: self.window.show_quick_panel(options, done), 10)
		else:
			self.window.show_quick_panel(options, done)

	def select(self):
		self.drive_list = self._get_drives()
		self._show_quick_panel(self.drive_list, self._on_done)


class FolderBrowser:

	def __init__(self, window, callback, curr_dir=None):
		self.window = window		
		self.callback = callback
		self.new_dir_name = 'new_folder'

		if curr_dir is None:
			self.curr_dir = os.path.abspath(os.path.dirname(__file__))
		else:			
			self.curr_dir = os.path.abspath(curr_dir)

		if is_st3():
			try:			
				self.curr_dir = str(self.curr_dir, 'cp1251')
			except:
				self.curr_dir = str(self.curr_dir)	
		else:
			try:			
				self.curr_dir = unicode(self.curr_dir, 'cp1251')
			except:
				self.curr_dir = unicode(self.curr_dir)

		self.folder_list = [] 
		self.driver_selector = DriveSelector(self.window, self._check_and_select)

	def _get_file_name(self, file_path):
		return os.path.split(file_path)[1]

	def _try_to_set_curr_file_dir(self):
		try:
			view = self.window.active_view()
			cur_file_path = view.file_name()
			cur_file_dir = os.path.dirname(cur_file_path)
			self.curr_dir = cur_file_dir
		except:
			pass

	def _get_sub_dirs(self, dir_path):
		subdirs = []		
		for f in os.listdir(dir_path):
			full_path = os.path.abspath(os.path.join(dir_path, f))
			if os.path.isdir(full_path):
				subdirs.append(f)
		return subdirs

	def _show_quick_panel(self, options, done):
		if is_st3():
			sublime.set_timeout(lambda: self.window.show_quick_panel(options, done), 10)
		else:
			self.window.show_quick_panel(options, done)

	def _check_dir(self, dir_path):
		try:
			os.listdir(dir_path)
		except:
			return False
		else:
			return True

	def _create_dir(self):
		
		def on_done(dir_name, *args):
			self.new_dir_name = dir_name
			try:
				dir_path = os.path.normpath(os.path.join(self.curr_dir, dir_name))
				os.mkdir(dir_path)
			except Exception as e:
				sublime.status_message( _('cant_create_dir') % dir_path)					
				self._check_and_select(None)
			else:
				self._check_and_select(dir_path)

		def on_cancel(*args):
			self._check_and_select(None)

		self.window.show_input_panel(_('input_dir_name'), self.new_dir_name, on_done, None, on_cancel)

	def _show_folder_menu(self):
		self._show_quick_panel(self.folder_list, self._folder_selected)

	def _sort(self, lst):
		if is_st3():
			return sorted(lst, key = str.lower)
		else:
			return sorted(lst, cmp=lambda a,b: cmp(a.lower(), b.lower()))

	def _folder_selected(self, index):
		if index < 0:
			self.callback(None)
		elif index == 0:
			dir_ = os.path.normpath(os.path.join(self.curr_dir, '..'))
			self._check_and_select(dir_)
		elif index == 1:
			self.callback(self.curr_dir)
		elif index == 2:
			self._create_dir()
		elif index == 3 and sublime.platform() == 'windows':
			self.drives = self.driver_selector.select()
		else:
			dir_ = os.path.normpath(os.path.join(self.curr_dir, self.folder_list[index]))
			self._check_and_select(dir_)

	def _check_and_select(self, dir_):
		if dir_ is not None:
			if self._check_dir(dir_):
				self.curr_dir = dir_
				sublime.status_message(_('current_dir') % self.curr_dir)
			else:
				sublime.status_message(_('cant_enter_dir') % (dir_, self.curr_dir))
		self._select_folder()
		
	def _select_folder(self):			

		self.folder_list = list()
		for d in self._get_sub_dirs(self.curr_dir):
			self.folder_list.append(d)

		self.folder_list = self._sort(self.folder_list)
		if sublime.platform() == 'windows':
			self.folder_list.insert(0, _('change_disk'))
		self.folder_list.insert(0, _('create_dir'))
		self.folder_list.insert(0, _('unpack_here'))
		self.folder_list.insert(0, _('level_up'))		
		self._show_folder_menu()

	def select_folder(self):
		self._try_to_set_curr_file_dir()
		self._select_folder()

class WebfontImportFontCommand(sublime_plugin.TextCommand):
	
	def __init__(self, view):
		super(WebfontImportFontCommand, self).__init__(view)
		pass

	def run(self, edit, text):
		print("start WebfontImportFontCommand with args " + text)
		importText = text
		pos = self.view.sel()[0].a
		self.view.insert(edit, pos, importText)
		pass


class WebfontCommand(sublime_plugin.WindowCommand):

	URL = 'http://webfonts.ru/api/list.json'
	SITE_URL = 'http://webfont.ru/'

	def __init__(self, window):
		super(WebfontCommand, self).__init__(window)
		print("Init webFont")
		self.folder_browser = FolderBrowser(self.window, self._folder_selected)
		self.font_data = self._download_font_info()		
		self.archive_url = None
		self.settings = sublime.load_settings(SETTINGS_FILE)

		if self.settings.get('lang') is None:
			self.settings.set('lang', get_os_locale())
			sublime.save_settings(SETTINGS_FILE)

		if self.settings.get('lang') == 'en_US':
			current_loc = loc['en_US']

		if self.settings.get('lang') == 'ru_RU':
			current_loc = loc['ru_RU']


	def _download_font_info(self):		
		print("_download_font_info")
		try:
			if is_st3():
				fd = urllib.request.urlopen(self.URL, timeout=5).read().decode("utf-8")
				result = json.loads(fd)	
			else:
				fd = urllib2.urlopen(self.URL, timeout=5)
				result = json.load(fd)
			
		except Exception as e:
			print("exception " + str(e))
			if is_st3():
				sublime.error_message(_('cant_refresh_fonts'))	
			else:
				sublime.status_message(_('cant_refresh_fonts'))
			result = None
		return result

	def _download_font_archive(self, url):
		try:
			if is_st3():
				zipped_data = urllib.request.urlopen(url, timeout=15).read()
				result = io.BytesIO(zipped_data)	
			else:
				zipped_data = urllib2.urlopen(url, timeout=15).read()
				result = cStringIO.StringIO(zipped_data)
			
		except Exception as e:
			print("exception " + str(e))
			if is_st3():
				sublime.error_message(_('cant_download_font'))	
			else:
				sublime.status_message(_('cant_download_font'))
			
			result = None
		return result

	def _unpack_archive(self, fd, dest_folder):
		try:			
			dest_folder = os.path.normpath(dest_folder)
			print("dest folder" + dest_folder)
			z = zipfile.ZipFile(fd)

			for name in z.namelist():	
				if name.endswith('/'):
					#this is folder
					folder_path = os.path.join(dest_folder, name)
					if not os.path.exists(folder_path):
						os.makedirs(folder_path)
				else:
					file_path = os.path.join(dest_folder, name)
					print("file_path" + file_path)
					outfile = open(file_path, 'wb+')
					outfile.write(z.read(name))
					outfile.close()

			fd.close()
			return True
		except Exception as e:
			print("exception " + str(e))
			if is_st3():
				sublime.error_message(_('unpack_error'))	
			else:
				sublime.status_message(_('unpack_error'))
			
			return False

	def run(self):
		print("command start")

		name_list = [ _('go_to_webfont'), _('update_fonts_list'), _('download_font')]
		if self.font_data is not None:
			for i in self.font_data:
				name_list.append(i['name'])
		self.window.show_quick_panel(name_list, self._selected)

	def _insert(self, text):
		if is_st3():
			self.window.active_view().run_command("webfont_import_font", {"text" : text })	
		else:
			view = self.window.active_view()		
			edit = view.begin_edit()		
			pos = view.sel()[0].a
			view.insert(edit, pos, text)		
			view.end_edit(edit)
		

	def _download_font_archive_and_unpack(self, dest_folder, pack_url):
		fd = self._download_font_archive(pack_url)
		if fd is None:
			return
		res = self._unpack_archive(fd, dest_folder)
		if not res:
			return
		sublime.status_message(_('download_complete'))

	def _folder_selected(self, dest_folder):
		if dest_folder is None:
			return
		sublime.status_message(_('please_wait'))
		t = threading.Thread(args=(dest_folder, self.archive_url, ), target=self._download_font_archive_and_unpack)		
		t.start()

	def _font_archive_selected(self, index):
		if index < 0: return

		self.archive_url = self.font_data[index]['pack_url']
		self.folder_browser.select_folder()

	def _show_quick_panel(self, options, done):
		if is_st3():
			sublime.set_timeout(lambda: self.window.show_quick_panel(options, done), 10)
		else:
			self.window.show_quick_panel(options, done)

	def _selected(self, index):
		if index < 0: return
		if index == 0:
			try:
				webbrowser.open(self.SITE_URL)
			except:
				sublime.status_message(_('cant_open_website') % self.SITE_URL)
		elif index == 1:
			old_font_data = self.font_data
			self.font_data = self._download_font_info()
			if self.font_data is None:
				self.font_data = old_font_data
			self.run()
		elif index == 2:
			name_list = []
			if self.font_data is not None:
				for i in self.font_data:
					name_list.append(i['name'])
			self._show_quick_panel(name_list, self._font_archive_selected)

		else:			
			text = self.font_data[index-3]['import'] + '\n' + self.font_data[index-3]['comments']
			self._insert(text)