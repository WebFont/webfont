#coding:utf-8

import sublime, sublime_plugin, json, urllib2, webbrowser, cStringIO, zipfile, os, threading

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

	def select(self):
		self.drive_list = self._get_drives()
		self.window.show_quick_panel(self.drive_list, self._on_done)


class FolderBrowser:

	def __init__(self, window, callback, curr_dir=None):
		self.window = window		
		self.callback = callback
		self.new_dir_name = 'new_folder'

		if curr_dir is None:
			self.curr_dir = os.path.abspath(os.path.dirname(__file__))
		else:
			self.curr_dir = os.path.abspath(curr_dir)
		try:			
			self.curr_dir = unicode(self.curr_dir, 'cp1251')
		except:
			self.curr_dir = unicode(self.curr_dir)

		self.folder_list = [] 
		self.driver_selector = DriveSelector(self.window, self._check_and_select)

	def _get_file_name(self, file_path):
		return os.path.split(file_path)[1]

	def _get_sub_dirs(self, dir_path):
		subdirs = []		
		for f in os.listdir(dir_path):
			full_path = os.path.abspath(os.path.join(dir_path, f))
			if os.path.isdir(full_path):
				subdirs.append(f)
		return subdirs

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
				sublime.status_message(u'невозможно создать каsталог: "%s"' % dir_path)					
				self._check_and_select(None)
			else:
				self._check_and_select(dir_path)

		def on_cancel(*args):
			self._check_and_select(None)

		self.window.show_input_panel(u'Введите имя каталога:', self.new_dir_name, on_done, None, on_cancel)

	def _show_folder_menu(self):
		self.window.show_quick_panel(self.folder_list, self._folder_selected)

	def _sort(self, lst):
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
				sublime.status_message(u'текущий каталог: "%s"' % self.curr_dir)
			else:
				sublime.status_message(u'невозможно войти в каталог "%s"; текущий каталог: "%s"' % (dir_, self.curr_dir))
		self.select_folder()
		
	def select_folder(self):			

		self.folder_list = list()
		for d in self._get_sub_dirs(self.curr_dir):
			self.folder_list.append(d)

		self.folder_list = self._sort(self.folder_list)
		if sublime.platform() == 'windows':
			self.folder_list.insert(0, u'* сменить диск')
		self.folder_list.insert(0, u'* создать каталог')
		self.folder_list.insert(0, u'* да, распаковать сюда')
		self.folder_list.insert(0, u'* на уровень выше')		
		self._show_folder_menu()


class WebfontCommand(sublime_plugin.WindowCommand):

	URL = 'http://webfonts.ru/api/list.json'
	SITE_URL = 'http://webfont.ru/'

	def __init__(self, window):
		super(WebfontCommand, self).__init__(window)
		self.folder_browser = FolderBrowser(self.window, self._folder_selected)
		self.font_data = self._download_font_info()		
		self.archive_url = None	

	def _download_font_info(self):		
		try:
			fd = urllib2.urlopen(self.URL, timeout=5)
			result = json.load(fd)
		except Exception as e:
			sublime.status_message(u'не удалось обновить список шрифтов')
			result = None
		return result

	def _download_font_archive(self, url):
		try:
			zipped_data = urllib2.urlopen(url, timeout=15).read()
			result = cStringIO.StringIO(zipped_data)
		except Exception as e:
			sublime.status_message(u'не удалось скачать шрифт')
			result = None
		return result

	def _unpack_archive(self, fd, dest_folder):
		try:			
			dest_folder = os.path.normpath(dest_folder)
			z = zipfile.ZipFile(fd)
			for name in z.namelist():				
				file_path = os.path.join(dest_folder, name)
				outfile = open(file_path, 'wb+')
   				outfile.write(z.read(name))
   				outfile.close()
			fd.close()
			return True
		except Exception as e:
			sublime.status_message(u'при распаковке шрифта произошла ошибка')
			return False

	def run(self):

		name_list = [u'* перейти на webfont.ru', u'* обновить список шрифтов', u'* скачать шрифт']
		if self.font_data is not None:
			for i in self.font_data:
				name_list.append(i['name'])
		self.window.show_quick_panel(name_list, self._selected)

	def _insert(self, text):
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
		sublime.status_message(u'шрифт успешно скачан')

	def _folder_selected(self, dest_folder):
		if dest_folder is None:
			return
		sublime.status_message(u'немного подождите')
		t = threading.Thread(args=(dest_folder, self.archive_url, ), target=self._download_font_archive_and_unpack)		
		t.start()

	def _font_archive_selected(self, index):
		if index < 0: return

		self.archive_url = self.font_data[index]['pack_url']
		self.folder_browser.select_folder()

	def _selected(self, index):
		if index < 0: return
		if index == 0:
			try:
				webbrowser.open(self.SITE_URL)
			except:
				sublime.status_message(u'не удалось открыть страницу "%s"' % self.SITE_URL)
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
			self.window.show_quick_panel(name_list, self._font_archive_selected)

		else:			
			text = self.font_data[index-3]['import'] + '\n' + self.font_data[index-3]['comments']
			self._insert(text)