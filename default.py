﻿import urllib

import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmc
from resources.router import Router, expander
import resources.bc as bc
import sys

addon = xbmcaddon.Addon()
language = addon.getLocalizedString
addon_id = addon.getAddonInfo('id')
icon = addon.getAddonInfo('icon')
fanart = addon.getAddonInfo('fanart')
addon_version = addon.getAddonInfo('version')
current_path = sys.argv[0]
handle = int(sys.argv[1])
query = sys.argv[2]

current_path = current_path + query

dbg = True
try:
    import StorageServer

    print 'real storage'
except ImportError:
    import storageserverdummy as StorageServer

    print 'dummy storage'

cache = StorageServer.StorageServer(addon_id, 24)

router = Router(host="plugin://%s" % (addon_id,))


class PluginHelper(object):
    def __init__(self, handle):
        self.handle = handle

    def listingAction(self, func):
        def inner(*args):
            items = func(*args)
            xbmcplugin.addDirectoryItems(self.handle, items)
            xbmcplugin.endOfDirectory(self.handle)

        return inner


plghelper = PluginHelper(handle)


def album_to_listitem(album):
    label = "Album: %s by %s" % (album.title, album.artist)
    return router.make('album', {'url': album.url}), xbmcgui.ListItem(label, '', album.cover, album.cover), True


def band_to_listitem(band):
    label = "Band: %s" % ("Fake band",)
    return router.make('home'), xbmcgui.ListItem(label), True


def track_to_listitem(track):
    # return router.make('album', {'url': track.url}), xbmcgui.ListItem(track.title), False
    label = "Track: %s" % (track.title,)
    return track.stream_url, xbmcgui.ListItem(label), False


me = "thesebas"


@router.route('home', R"^/$", expander("/"))
@plghelper.listingAction
def home(params, parts, route):
    print params, parts, route
    return [
        (router.make('discover'), xbmcgui.ListItem('discover', 'discover-2'), True),
        (router.make('search'), xbmcgui.ListItem('search', 'search-2'), True),
        (router.make('user', {"username": me}), xbmcgui.ListItem('user', 'user-2'), True),
    ]


@router.route('discover', R"^/discover$", expander("/discover"))
@plghelper.listingAction
def discover(params, parts, route):
    return []


@router.route('search', R"^/search$", expander("/search{?query}"))
@plghelper.listingAction
def search(params, parts, route):
    if "query" not in params:
        kb = xbmc.Keyboard()
        kb.doModal()
        if kb.isConfirmed():
            return search(dict(query=kb.getText()), parts, route)
        else:
            return []
    else:
        results = bc.get_search_results(params["query"])
        # print results
        ret = []
        for item in results:
            if type(item) is bc.Album:
                ret.append(album_to_listitem(item))
            if type(item) is bc.Track:
                ret.append(track_to_listitem(item))
            if type(item) is bc.Band:
                ret.append(band_to_listitem(item))

        # results = [item for item in ret if item is not None]
        # print ret
        return ret


@router.route('own-collection', R"^/own/collection$", expander("/own/collection"))
def owncollection(params, parts, route):
    return usercollection({"username": me}, parts, route)


@router.route('user-collection', R"^/user/(?P<username>.*?)/collection$", expander("/user/{username}/collection"))
@plghelper.listingAction
def usercollection(params, parts, route):
    albums = bc.get_collection(params["username"])
    return [album_to_listitem(album) for album in albums]


@router.route('own-wishlist', R"^/own/wishlist$", expander("/own/wishlist"))
def ownwishlist(params, parts, route):
    userwishlist({"username": me}, parts, route)


@router.route('user-wishlist', R"^/user/(?P<username>.*?)/wishlist$", expander("/user/{username}/wishlist"))
@plghelper.listingAction
def userwishlist(params, parts, route):
    albums = bc.get_wishlist(params["username"])
    return [album_to_listitem(album) for album in albums]


@router.route('album', R"^/album$", expander("/album{?url}"))
@plghelper.listingAction
def albumlist(params, parts, route):
    album_url = urllib.unquote(params["url"][0])
    print "getting album: %s" % album_url
    tracks = bc.get_album_tracks(album_url)
    return [track_to_listitem(track) for track in tracks]


@router.route('user', R"^/user/(?P<username>[^/]*?)$", expander("/user/{username}"))
@plghelper.listingAction
def user(params, parts, route):
    return [
        (router.make('user-collection', {"username": params["username"]}), xbmcgui.ListItem("collection"), True),
        (router.make('user-wishlist', {"username": params["username"]}), xbmcgui.ListItem("wishlist"), True),
    ]


print "current path: %s" % current_path
print "handle: %d" % handle

router.run(current_path)
