#!/usr/bin/python
from __future__ import print_function
import sys, urllib, urllib2, urlparse
import xbmc, xbmcgui
import xbmcplugin
import xml.dom.minidom
import json
import xbmcaddon
from mediaviewer import *
import time

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

addon = xbmcaddon.Addon()
plugin_path = addon.getAddonInfo("path")
creds_path = plugin_path + "/credentials.json"
token_path = plugin_path + "/token.pickle"

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']

base_url = sys.argv[0]

addon_handle = int(sys.argv[1])
xbmcplugin.setContent(addon_handle, 'pictures')

args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get('mode', None)

class MyPhotoIterator(MediaIterator):
	def __init__(self, albumId, index):
		xbmc.log(albumId,level=xbmc.LOGNOTICE)
		self.photoset = []
		self.currIndex = index
		nextpagetoken = 'Dummy'
		idx = 0
		service = getGoogleService()
		while nextpagetoken != '':
			nextpagetoken = '' if nextpagetoken == 'Dummy' else nextpagetoken
			results = service.mediaItems().search(body={"albumId":albumId, "pageSize": 100, "pageToken": nextpagetoken}).execute()
			items = results.get('mediaItems', [])
			nextpagetoken = results.get('nextPageToken', '')
			for item in items:
				self.photoset.append(item['baseUrl'] + '=d')		

	def forward(self):
		self.currIndex += 1
		# load next page if necessary

	def back(self):
		self.currIndex -= 1
		# load previous page if necessary

	def getCurrUrl(self):
		return self.photoset[self.currIndex]

	def isCurrVideo(self):
		return False

	def getVideoUrl(self):
		return self.photoset[self.currIndex]

def build_url(query):
	url = base_url + '?' + urllib.urlencode(query)
	return url

def ShowKeyboard():
	user_input = ''
	exit = True
	while exit:
		kb = xbmc.Keyboard('default', 'heading', True)
		kb.setDefault('')
		kb.setHeading('Authentication')
		kb.setHiddenInput(False)
		kb.doModal()
		if kb.isConfirmed():
			user_input = kb.getText()
			exit = False
	return user_input

def getGoogleService():
	creds = None
	# The file token.pickle stores the user's access and refresh tokens, and is
	# created automatically when the authorization flow completes for the first
	# time.
	if os.path.exists(token_path):
		with open(token_path, 'rb') as token:
			creds = pickle.load(token)
			xbmc.log("creds loaded from file",level=xbmc.LOGNOTICE)
	
	# If there are no (valid) credentials available, let the user log in.
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			xbmc.log("creds need to update",level=xbmc.LOGNOTICE)
			creds.refresh(Request())
		else:
			xbmc.log("creds file not found need new process",level=xbmc.LOGNOTICE)
			flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
			auth_url, _ = flow.authorization_url(prompt='consent')
			xbmc.log(auth_url,level=xbmc.LOGNOTICE)
			creds = flow.run_local_server(port=0)
		# Save the credentials for the next run
		with open(token_path, 'wb') as token:
			pickle.dump(creds, token)
	return build('photoslibrary', 'v1', credentials=creds)

start = time.time()
if mode is None:
	url = build_url({'mode': 'connect-account'})
	li = xbmcgui.ListItem('Connect a new Google photos account', iconImage='DefaultPicture.png')
	xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
	xbmcplugin.endOfDirectory(addon_handle)
	xbmc.log("Time to load dir: "+str(time.time() - start), level=xbmc.LOGNOTICE)

elif mode[0] == 'connect-account':
	start = time.time()
	service = getGoogleService()
	xbmc.log("Time to load service: "+str(time.time() - start), level=xbmc.LOGNOTICE)
	start = time.time()
	results = service.albums().list(pageSize=10).execute()
	xbmc.log("Time to fetch albums: "+str(time.time() - start), level=xbmc.LOGNOTICE)
	start = time.time()
	albums = results.get('albums', [])
	for album in albums:
		if album['title'] != 'Private':
			url = build_url({'mode': 'list-album-photos', 'albumId': album['id']})
			li = xbmcgui.ListItem(album['title'], iconImage='DefaultPicture.png')
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
	xbmcplugin.endOfDirectory(addon_handle)
	xbmc.log("Time to load albums: "+str(time.time() - start), level=xbmc.LOGNOTICE)

elif mode[0] == 'list-album-photos':
	albumId = args.get('albumId', '')
	nextpagetoken = 'Dummy'
	idx = 0
	service = getGoogleService()
	while nextpagetoken != '':
		start = time.time()
		nextpagetoken = '' if nextpagetoken == 'Dummy' else nextpagetoken
		results = service.mediaItems().search(body={"albumId":albumId[0], "pageSize": 100, "pageToken": nextpagetoken}).execute()
		xbmc.log("Time to load items: "+str(time.time() - start), level=xbmc.LOGNOTICE)
		items = results.get('mediaItems', [])
		nextpagetoken = results.get('nextPageToken', '')
		start = time.time()
		for item in items:
			# url = item['baseUrl'] + '=w1024-h512'
			url = build_url({'mode':'play_media', 'albumId': albumId[0], 'idx':idx})
			idx += 1
			li = xbmcgui.ListItem(item['filename'], iconImage='DefaultPicture.png', thumbnailImage=item['baseUrl']+"=w256-h128")
			# li.setInfo(type="image", infoLabels={"Title": item['filename']})
			xbmcplugin.addDirectoryItem(addon_handle, url, li, True)
		xbmc.log("Time to load directory: "+str(time.time() - start), level=xbmc.LOGNOTICE)
	xbmcplugin.endOfDirectory(addon_handle)
	# xbmc.executebuiltin("Container.SetViewMode(500)")

elif mode[0] == 'play_media':
	albumId = args.get('albumId', '')
	xbmc.log(albumId[0],level=xbmc.LOGNOTICE)
	index = args.get('idx', '0')
	window = MediaWindow(MyPhotoIterator(albumId[0], int(index[0])))
	window.doModal()