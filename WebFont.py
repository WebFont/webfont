# coding:utf-8

import json
import sublime
import sublime_plugin
import webbrowser
import urllib.request


loc = {
    'en_US': {
        'cant_refresh_fonts': u'can\'t update fonts list',
        'download_font': u'Download font(ttf/otf)',
        'import_font': u'Import font',
        'subsetting': u'Subsetting',
        'view_on_website': u'View on website',
        'update_fonts_list': u'* update fonts list',
        'cant_open_website': u'can\'t open website "%s"',

        'download_reminder': u'/* Please do not use this import in production. You could download this font from here %s */'
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

    URL = 'https://fontstorage.com/api/plugins.json'

    def __init__(self, window):
        super(WebfontCommand, self).__init__(window)
        self.data = self._download_font_info()
        self.font_data = self.data['fonts']
        self.urls = self.data['urls']

    def _site_font_url(self):
        site_font_url = self.urls['site_url'] + '/font/' + self.selected_font['font_slug'] + '?from=sublime'
        return site_font_url 
        
    def _download_font_url(self):
        download_font_url = self.urls['download_url'] + self.selected_font['slug'] + '/' + self.selected_font['slug'] + '.zip'
        return download_font_url

    def _import_font_url(self):
        import_font_url = '@import "' + self.urls['import_url'] + self.selected_font['slug'] + '.css";'
        return import_font_url

    def _subsetting_font_url(self):
        subsetting_font_url = self.urls['converter_url'] + '#' + self.selected_font['font_slug']
        return subsetting_font_url


    def _download_font_info(self):
        try:
            fd = urllib.request.urlopen(
                self.URL, timeout=5).read().decode("utf-8")
            result = json.loads(fd)

        except Exception as e:
            print("exception " + str(e))
            sublime.error_message(_('cant_refresh_fonts'))
            result = None
        return result

    def run(self):
        print("command start")
        self._download_font_info()
        name_list = []
        if self.font_data is not None:
            for i in self.font_data:
                name_list.append(i['name'])
        self.window.show_quick_panel(name_list, self._selected)

    def _insert(self, text):
        self.window.active_view().run_command(
            "webfont_import_font", {"text": text})

    def _selected_option(self, index):
        if index == 0:
            text = (_('download_reminder') % self._site_font_url()) + '\n' \
                + self._import_font_url() + '\n' \
                + self.selected_font['comments']
            self._insert(text)
        elif index == 1:
            self._open_in_browser(self._download_font_url())
        elif index == 2:
            self._open_in_browser(self._subsetting_font_url())
        elif index == 3:
            self._open_in_browser(self._site_font_url())

    def _selected(self, index):
        if index < 0:
            return
        name_list = [
            _('import_font'),
            _('download_font'),
            _('subsetting'),
            _('view_on_website')]
        self.selected_font = self.font_data[index]
        self.window.show_quick_panel(name_list, self._selected_option)

    def _open_in_browser(self, url):
        try:
            webbrowser.open(url)
        except:
            sublime.status_message(_('cant_open_website') % url)
