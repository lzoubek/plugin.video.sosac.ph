# -*- coding: UTF-8 -*-
# /*
# *      Copyright (C) 2015 Libor Zoubek + jondas
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

import urllib
import urllib2
import cookielib
import sys
import json

import util
from provider import ContentProvider, cached, ResolveException

sys.setrecursionlimit(10000)

MOVIES_BASE_URL = "http://movies.prehraj.me"
TV_SHOW_FLAG = "#tvshow#"
ISO_639_1_CZECH = "cs"

# JSONs
URL = "http://tv.sosac.to"
J_MOVIES_A_TO_Z_TYPE = "/vystupy5981/souboryaz.json"
J_MOVIES_GENRE = "/vystupy5981/souboryzanry.json"
J_MOVIES_MOST_POPULAR = "/vystupy5981/moviesmostpopular.json"
J_MOVIES_RECENTLY_ADDED = "/vystupy5981/moviesrecentlyadded.json"
# hack missing json with a-z series
J_TV_SHOWS_A_TO_Z_TYPE = "/vystupy5981/tvpismenaaz/"
J_TV_SHOWS = "/vystupy5981/tvpismena/"
J_SERIES = "/vystupy5981/serialy/"
J_TV_SHOWS_MOST_POPULAR = "/vystupy5981/tvshowsmostpopular.json"
J_TV_SHOWS_RECENTLY_ADDED = "/vystupy5981/tvshowsrecentlyadded.json"
J_SEARCH = "/jsonsearchapi.php?q="
STREAMUJ_URL = "http://www.streamuj.tv/video/"
IMAGE_URL = "http://movies.sosac.tv/images/"
IMAGE_MOVIE = IMAGE_URL + "75x109/movie-"
IMAGE_SERIES = IMAGE_URL + "558x313/serial-"
IMAGE_EPISODE = URL

LIBRARY_MENU_ITEM_ADD = "[B][COLOR red]Add to library[/COLOR][/B]"
LIBRARY_MENU_ITEM_ADD_ALL = "[B][COLOR red]Add all to library[/COLOR][/B]"
LIBRARY_MENU_ITEM_REMOVE = "[B][COLOR red]Remove from subscription[/COLOR][/B]"
LIBRARY_TYPE_VIDEO = "video"
LIBRARY_TYPE_TVSHOW = "tvshow"
LIBRARY_TYPE_ALL_VIDEOS = "all-videos"
LIBRARY_TYPE_ALL_SHOWS = "all-shows"
LIBRARY_ACTION_ADD = "add-to-library"
LIBRARY_ACTION_ADD_ALL = "add-all-to-library"
LIBRARY_ACTION_REMOVE_SUBSCRIPTION = "remove-subscription"
LIBRARY_FLAG_IS_PRESENT = "[B][COLOR yellow]*[/COLOR][/B] "

RATING = 'r'
LANG = 'd'
QUALITY = 'q'
IMDB = 'm'
CSFD = 'c'


class SosacContentProvider(ContentProvider):
    ISO_639_1_CZECH = None
    par = None

    def __init__(self, username=None, password=None, filter=None, reverse_eps=False):
        ContentProvider.__init__(self, name='sosac.ph', base_url=MOVIES_BASE_URL, username=username,
                                 password=password, filter=filter)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar()))
        urllib2.install_opener(opener)
        self.reverse_eps = reverse_eps

    def on_init(self):
        kodilang = self.lang or 'cs'
        if kodilang == ISO_639_1_CZECH or kodilang == 'sk':
            self.ISO_639_1_CZECH = ISO_639_1_CZECH
        else:
            self.ISO_639_1_CZECH = 'en'

    def capabilities(self):
        return ['resolve', 'categories', 'search']

    def categories(self):
        result = []
        item = self.dir_item(title="Movies", url=URL + J_MOVIES_A_TO_Z_TYPE)
        item['menu'] = {
            LIBRARY_MENU_ITEM_ADD_ALL: {
                'action': LIBRARY_ACTION_ADD_ALL,
                'type': LIBRARY_TYPE_ALL_VIDEOS
            }
        }
        result.append(item)

        item = self.dir_item(title="TV Shows", url=URL +
                             J_TV_SHOWS_A_TO_Z_TYPE)
        item['menu'] = {
            LIBRARY_MENU_ITEM_ADD_ALL: {
                'action': LIBRARY_ACTION_ADD_ALL,
                'type': LIBRARY_TYPE_ALL_SHOWS
            }
        }
        result.append(item)

        item = self.dir_item(title="Movies - by Genres", url=URL +
                             J_MOVIES_GENRE)
        result.append(item)

        item = self.dir_item(title="Movies - Most popular", url=URL +
                             J_MOVIES_MOST_POPULAR)
        result.append(item)

        item = self.dir_item(title="TV Shows - Most popular", url=URL +
                             J_TV_SHOWS_MOST_POPULAR)
        result.append(item)

        item = self.dir_item(title="Movies - Recently added", url=URL +
                             J_MOVIES_RECENTLY_ADDED)
        result.append(item)

        item = self.dir_item(title="TV Shows - Recently added", url=URL +
                             J_TV_SHOWS_RECENTLY_ADDED)
        result.append(item)

        return result

    def search(self, keyword):
        if len(keyword) < 3 or len(keyword) > 100:
            return [self.dir_item(title="Search query must be between 3 and 100 characters long!", url="fail")]
        return self.list_videos(URL + J_SEARCH + urllib.quote_plus(keyword))

    def a_to_z(self, url):
        result = []
        for letter in ['0-9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'e', 'h', 'i', 'j', 'k', 'l', 'm',
                       'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']:
            item = self.dir_item(title=letter.upper())
            item['url'] = URL + url + letter + ".json"
            result.append(item)
        return result

    @staticmethod
    def particular_letter(url):
        return "a-z/" in url

    def has_tv_show_flag(self, url):
        return TV_SHOW_FLAG in url

    def list(self, url):
        util.info("Examining url " + url)
        if J_MOVIES_A_TO_Z_TYPE in url:
            return self.load_json_list(url)
        if J_MOVIES_GENRE in url:
            return self.load_json_list(url)
        if J_MOVIES_MOST_POPULAR in url:
            return self.list_videos(url)
        if J_MOVIES_RECENTLY_ADDED in url:
            return self.list_videos(url)
        if J_TV_SHOWS_A_TO_Z_TYPE in url:
            return self.a_to_z(J_TV_SHOWS)
        if J_TV_SHOWS in url:
            return self.list_series_letter(url)
        if J_SERIES in url:
            return self.list_episodes(url)
        if J_TV_SHOWS_MOST_POPULAR in url:
            return self.list_series_letter(url)
        if J_TV_SHOWS_RECENTLY_ADDED in url:
            return self.list_recentlyadded_episodes(url)
        return self.list_videos(url)

    def load_json_list(self, url):
        result = []
        data = util.request(url)
        json_list = json.loads(data)
        for key, value in json_list.iteritems():
            item = self.dir_item(title=key.title())
            item['url'] = value
            result.append(item)

        return sorted(result, key=lambda i: i['title'])

    def list_videos(self, url):
        result = []
        data = util.request(url)
        json_video_array = json.loads(data)
        for video in json_video_array:
            item = self.video_item()
            item['title'] = self.get_video_name(video)
            item['img'] = IMAGE_MOVIE + video['i']
            item['url'] = video['l'] if video['l'] else ""
            if RATING in video:
                item['rating'] = video[RATING]
            if LANG in video:
                item['lang'] = video[LANG]
            if QUALITY in video:
                item['quality'] = video[QUALITY]
            item['menu'] = {
                LIBRARY_MENU_ITEM_ADD: {
                    'url': item['url'],
                    'type': LIBRARY_TYPE_VIDEO,
                    'action': LIBRARY_ACTION_ADD,
                    'name': self.get_library_video_name(video)
                }
            }
            if CSFD in video and video[CSFD] is not None:
                item['menu'][LIBRARY_MENU_ITEM_ADD]['csfd'] = video[CSFD]
            if IMDB in video and video[CSFD] is not None:
                item['menu'][LIBRARY_MENU_ITEM_ADD]['imdb'] = video[IMDB]
            result.append(item)
        return result

    def list_series_letter(self, url, load_subs=True):
        result = []
        data = util.request(url)
        json_list = json.loads(data)
        subs = self.get_subscriptions() if load_subs else {}
        for serial in json_list:
            item = self.dir_item()
            item['title'] = self.get_localized_name(serial['n'])
            item['img'] = IMAGE_SERIES + serial['i']
            item['url'] = serial['l']
            if item['url'] in subs:
                item['title'] = LIBRARY_FLAG_IS_PRESENT + item['title']
                item['menu'] = {
                    LIBRARY_MENU_ITEM_REMOVE: {
                        'url': item['url'],
                        'action': LIBRARY_ACTION_REMOVE_SUBSCRIPTION,
                        'name': self.get_library_video_name(serial)
                    }
                }
            else:
                item['menu'] = {
                    LIBRARY_MENU_ITEM_ADD: {
                        'url': item['url'],
                        'type': LIBRARY_TYPE_TVSHOW,
                        'action': LIBRARY_ACTION_ADD,
                        'name': self.get_library_video_name(serial)
                    }
                }
                if CSFD in serial and serial[CSFD] is not None:
                    item['menu'][LIBRARY_MENU_ITEM_ADD]['csfd'] = serial[CSFD]
                if IMDB in serial and serial[IMDB] is not None:
                    item['menu'][LIBRARY_MENU_ITEM_ADD]['imdb'] = serial[IMDB]
            result.append(item)
        return result

    def list_episodes(self, url):
        result = []
        data = util.request(url)
        json_series = json.loads(data)
        for series in json_series:
            for series_key, episode in series.iteritems():
                for episode_key, video in episode.iteritems():
                    item = self.video_item()
                    item['title'] = series_key + "x" + episode_key + " - " + video['n']
                    if video['i'] is not None:
                        item['img'] = IMAGE_EPISODE + video['i']
                    item['url'] = video['l'] if video['l'] else ""
                    result.append(item)
        if not self.reverse_eps:
            result.reverse()
        return result

    def list_recentlyadded_episodes(self, url):
        result = []
        data = util.request(url)
        json_series = json.loads(data)
        for episode in json_series:
            item = self.video_item()
            item['title'] = self.get_episode_recently_name(episode)
            item['img'] = IMAGE_EPISODE + episode['i']
            item['url'] = episode['l']
            result.append(item)
        return result

    def list_all_videos(self):
        letters = self.load_json_list(URL + J_MOVIES_A_TO_Z_TYPE)
        total = len(letters)

        step = int(100 / len(letters))
        for idx, letter in enumerate(letters):
            for video in self.list_videos(letter['url']):
                yield video
            yield {'progress': step * (idx + 1)}

    def list_all_tvshows(self):
        letters = self.a_to_z(J_TV_SHOWS)
        total = len(letters)

        step = int(100 / len(letters))
        for idx, letter in enumerate(letters):
            for video in self.list_series_letter(letter['url'], False):
                yield video
            yield {'progress': step * (idx + 1)}

    def get_video_name(self, video):
        name = self.get_localized_name(video['n'])
        year = (" (" + video['y'] + ")") if video['y'] else " "
        quality = (" - " + video[QUALITY].upper()) if video[QUALITY] else ""
        return name + year + quality

    def get_library_video_name(self, video):
        name = self.get_localized_name(video['n'])
        year = (" (" + video['y'] + ")") if video['y'] else " "
        return (name + year).encode('utf-8')

    def get_episode_recently_name(self, episode):
        serial = self.get_localized_name(episode['t']) + ' '
        series = episode['s'] + "x"
        number = episode['e'] + " - "
        name = self.get_localized_name(episode['n'])
        return serial + series + number + name

    def get_localized_name(self, names):
        return names[self.ISO_639_1_CZECH] if self.ISO_639_1_CZECH in names else names[ISO_639_1_CZECH]

    def _url(self, url):
        # DirtyFix nefunkcniho downloadu: Neznam kod tak se toho zkusenejsi chopte
        # a prepiste to lepe :)
        if '&authorize=' in url:
            return url
        else:
            return self.base_url + "/" + url.lstrip('./')

    def resolve(self, item, captcha_cb=None, select_cb=None):
        data = item['url']
        if not data:
            raise ResolveException('Video is not available.')
        result = self.findstreams([STREAMUJ_URL + data])
        if len(result) == 1:
            return result[0]
        elif len(result) > 1 and select_cb:
            return select_cb(result)

    def get_subscriptions(self):
        return self.parent.get_subs()
