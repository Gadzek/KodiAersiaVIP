import os
import sys
import urllib
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xml.etree.ElementTree as ET
from urllib.request import urlopen
import time

def build_url(query):
    base_url = sys.argv[0]
    return base_url + '?' + urllib.parse.urlencode(query)
    
def get_roster(url):
    with(urlopen(url)) as xml:
        tree = ET.iterparse(xml)
        for _, el in tree:
        #strip namespace for easier component search
            _, _, el.tag = el.tag.rpartition('}')
    return tree.root
    
def parse_roster(roster):
    songs = {}
    index = 1
    for track in roster.iter('track'):
        # update dictionary with the creator, song title and song url
        songs.update({index: {'creator': track.find('creator').text, 'title': track.find('title').text, 'url': track.find('location').text}})
        index += 1
    return songs
    
def build_song_list(songs):
    song_list = []
    # iterate over the contents of the dictionary songs to build the list
    xbmc.log('Adding songs to list', xbmc.LOGDEBUG)
    liCreate = 0
    setProp = 0
    setInfo = 0
    buildUrl = 0
    append = 0
    start_time = time.time()
    for song in songs:
        # create a list item using the song filename for the label
        title = songs[song]['title']
        artist = songs[song]['creator']
        li_start = time.time()
        li = xbmcgui.ListItem(label=title, label2=artist)
        liCreate += time.time() - li_start
        # set the list item to playable
        setProp_start = time.time()
        #TODO: Yooo, why this method takes the longest time?
        li.setProperty('IsPlayable', 'true')
        setProp += time.time() - setProp_start
        setInfo_start = time.time()
        li.setInfo('music', {'title': title, 'artist': artist})
        setInfo += time.time() - setInfo_start
        buildUrl_start = time.time()
        url = build_url({'mode': 'stream', 'url': songs[song]['url']})
        buildUrl += time.time() - buildUrl_start
        # add the current list item to a list
        append_start = time.time()
        song_list.append((url, li, False))
        append += time.time() - append_start
    xbmc.log('Adding songs took {0}s'.format(time.time() - start_time), xbmc.LOGDEBUG)
    start_time = time.time()
    xbmcplugin.addDirectoryItems(addon_handle, song_list, len(song_list))
    xbmc.log('Adding directory items took {0}s'.format(time.time() - start_time), xbmc.LOGDEBUG)
    xbmc.log('ListItems create: {0}s; setProperties: {1}s; setInfos: {2}s; build_urls: {3}s; list appends: {4}s'.format(liCreate, setProp, setInfo, buildUrl, append), xbmc.LOGDEBUG)
    # set the content of the directory
    xbmcplugin.setContent(addon_handle, 'songs')
    xbmcplugin.endOfDirectory(addon_handle)

def build_playlists_menu(playlists):
    playlists_list = []
    for key, value in playlists.items():
        li = xbmcgui.ListItem(label=key)
        url = build_url({'mode': 'playlist', 'roster_url': value, 'title': key})
        playlists_list.append((url, li, True))
        xbmc.log('Added playlist {0} with url {1}'.format(key, value), xbmc.LOGDEBUG)
    xbmcplugin.addDirectoryItems(addon_handle, playlists_list, len(playlists_list))
    xbmcplugin.endOfDirectory(addon_handle)

    
def play_song(url):
    #TODO: stop current playback?
    # set the path of the song to a list item
    play_item = xbmcgui.ListItem(path=url)
    # the list item is ready to be played by Kodi
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
    
def main():
    args = urllib.parse.parse_qs(sys.argv[2][1:])
    mode = args.get('mode', None)
    # initial launch of add-on
    if mode is None:
        build_playlists_menu(playlists)
    elif mode[0] == 'playlist':
        roster_url = args['roster_url'][0]
        xbmc.log('Received playlist {0}'.format(roster_url), xbmc.LOGDEBUG)
        xbmc.log('Getting roster {0}'.format(roster_url), xbmc.LOGDEBUG)
        start_time = time.time()
        roster = get_roster(roster_url)
        xbmc.log('Getting roster took {0}s'.format(time.time() - start_time), xbmc.LOGDEBUG)
        xbmc.log('Parsing roster {0}'.format(roster_url), xbmc.LOGDEBUG)
        start_time = time.time()
        content = parse_roster(roster)
        xbmc.log('Parsing roster took {0}s'.format(time.time() - start_time), xbmc.LOGDEBUG)
        xbmc.log('Building songs list', xbmc.LOGDEBUG)
        start_time = time.time()
        build_song_list(content)
        xbmc.log('Building list took {0}s'.format(time.time() - start_time), xbmc.LOGDEBUG)
    # a song from the list has been selected
    elif mode[0] == 'stream':
        xbmc.log('args received: {0}'.format(args))
        # pass the url of the song to play_song
        play_song(args['url'][0])
    
if __name__ == '__main__':
    playlists = {
                'VIP': 'http://vip.aersia.net/roster.xml',
                'Mellow': 'http://vip.aersia.net/roster-mellow.xml',
                'Source': 'http://vip.aersia.net/roster-source.xml',
                'Exiled': 'http://vip.aersia.net/roster-exiled.xml',
                'WAP': 'http://wap.aersia.net/roster.xml',
                'CPP': 'http://cpp.aersia.net/roster.xml',
        };

    default_playlist = 'VIP';
    addon_handle = int(sys.argv[1])
    main()
