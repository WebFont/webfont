#coding:utf-8

import sublime, sublime_plugin
import json
import webbrowser

SETTINGS_FILE = "FontStorage.sublime-settings"

def is_st3():
    return sublime.version()[0] == '3'

if is_st3():
    import urllib.request
else:
    import urllib2

loc = {
    'en_US':{
        'cant_refresh_fonts' : u'can\'t update fonts list',
        'cant_download_font' : u'can\'t download font',
        'unpack_error' : u'unpacking error',
        'go_to_fontstorage' : u'* go to fontstorage.com',
        'update_fonts_list' : u'* update fonts list',
        'open_on_fontstorage' : u'* open on fontstorage.com',
        'please_wait' : u'please wait',
        'cant_open_website' : u'can\'t open website "%s"',

        'download_reminder':u'/* Please do not use links to our site in production. You could download this font from here %s */'
    }
}

current_loc = loc['en_US']

def _(id):
    return current_loc[id]

class WebfontImportFontCommand(sublime_plugin.TextCommand):

    def __init__(self, view):
        super(WebfontImportFontCommand, self).__init__(view)
        pass

    def run(self, edit, text):
        print("start WebfontImportFontCommand with args " + text)
        import_text = text
        pos = self.view.sel()[0].a
        self.view.insert(edit, pos, import_text)
        pass


class WebfontCommand(sublime_plugin.WindowCommand):

    URL = 'https://fontstorage.com/api/list.json2'
    SITE_URL = 'https://fontstorage.com/'

    def __init__(self, window):
        super(WebfontCommand, self).__init__(window)
        print("Init Fontstorage plugin")

        self.font_data = self._download_font_info()
        self.archive_url = None
        self.settings = sublime.load_settings(SETTINGS_FILE)

        self.download_mode = self.settings.get('download_mode')

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

    def run(self):
        print("command start")

        name_list = [ _('go_to_fontstorage'), _('update_fonts_list'), _('open_on_fontstorage')]
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

    def _go_to_site_selected(self, index):
        if index < 0: return

        font_url = self.font_data[index]['font_url']
        if font_url is not None:
            print("Go to font page: " + font_url)
            self._open_in_browser(font_url)

    def _show_quick_panel(self, options, done):
        if is_st3():
            sublime.set_timeout(lambda: self.window.show_quick_panel(options, done), 10)
        else:
            self.window.show_quick_panel(options, done)

    def _selected(self, index):
        if index < 0: return
        if index == 0:
            self._open_in_browser(self.SITE_URL)
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
            self._show_quick_panel(name_list, self._go_to_site_selected)

        else:
            font_data = self.font_data[index-3]
            text = font_data['import'] + '\n' \
                   + font_data['comments'] + '\n' \
                   + (_('download_reminder') % font_data['font_url'])
            self._insert(text)

    def _open_in_browser(self, url):
        try:
            webbrowser.open(url)
        except:
            sublime.status_message(_('cant_open_website') % url)
