#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
from urllib import urlencode
from urlparse import parse_qs
from .google import GoogleRestClient

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
xbmcplugin.setContent(addon_handle, 'pictures')

def build_url(query):
	url = base_url + '?' + urlencode(query)
	return url

def Router():
    client = GoogleRestClient()

    args = parse_qs(sys.argv[2][1:])
    xbmc.log(str(args), xbmc.LOGNOTICE)
    mode = args.get('mode', None)
    url = args.get('url', [None])[0]
    if mode is None:
        li = xbmcgui.ListItem('All', iconImage='DefaultPicture.png')
        url = url=build_url({'mode': 'load-album', 'albumId': 'all'})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
        for album in client.getAlbumList().get('albums', []):
            title = album.get("title")
            if title == "Private":
                continue
            li = xbmcgui.ListItem(title, iconImage=album.get("coverPhotoBaseUrl")+"=w250-h150")
            url = url=build_url({'mode': 'load-album', 'albumId': album.get("id")})
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle)
    elif mode[0] == 'load-album':
        albumId = args.get('albumId', ['all'])[0]
        pageToken = args.get('pageToken', [None])[0]
        data = None
        if albumId == 'all':
            data = client.getMediaItems(pageToken)
        else:
            data = client.getAlbumItems(albumId, pageToken)
        for mediaItem in data.get('mediaItems', []):
            title = mediaItem.get("filename")
            icon = mediaItem.get('baseUrl')+"=w150-h100"
            li = xbmcgui.ListItem(title, iconImage=icon)
            li.setArt({ "thumb": icon })
            li.setProperty('IsPlayable', 'true')
            if mediaItem.get("mimeType") == "image/jpeg":
                url = mediaItem.get('baseUrl') + "=d"
                li.setInfo(type='pictures', infoLabels={
                    'title': title,
                    "picturepath": url,
                    "exif:path": url,
                    'exif:resolution': '{},{}'.format(
                        mediaItem.get("mediaMetadata").get("width"), 
                        mediaItem.get("mediaMetadata").get("height")
                    )
                })
            else:
                url = mediaItem.get('baseUrl') + "=dv"
                li.setInfo(type="video", infoLabels={
                    'title': title
                })
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)
        if data.get("nextPageToken", None):
            li = xbmcgui.ListItem('next page >', iconImage='DefaultPicture.png')
            url = url=build_url({
                'mode': 'load-album', 
                'albumId': albumId,
                'pageToken': data.get("nextPageToken")
            })
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
        xbmcplugin.setContent(addon_handle, 'images')
        xbmc.executebuiltin('Container.SetViewMode(500)')
        xbmcplugin.endOfDirectory(addon_handle)
        