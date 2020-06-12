#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, urllib, urllib2, urlparse, requests
import xbmc, xbmcaddon
import json, time

class GoogleRestClient():
	addon = xbmcaddon.Addon()
	__profile__ = xbmc.translatePath(addon.getAddonInfo('profile')).decode("utf-8")
	__credfile__ = __profile__ + 'creds.json'
	CREDS = None
	def __init__(self):
		if not os.path.exists(self.__profile__):
			os.mkdir(self.__profile__)
		if os.path.isfile(self.__credfile__):
			with open(self.__credfile__, 'r') as f:
				self.CREDS = json.load(f)
	
	def refreshToken(self):
		res = requests.post("https://oauth2.googleapis.com/token", json = {
			"client_id":self.CREDS.get("client_id"),
			"client_secret":self.CREDS.get("client_secret"),
			"refresh_token": self.CREDS.get("refresh_token"),
			"grant_type":"refresh_token"
		})
		if res.status_code == 200:
			data = res.json()
			self.CREDS["access_token"] = data.get("access_token")
			self.CREDS["expires_in"] = time.time() + data.get("expires_in")
			with open(self.__credfile__, 'w+') as f:
				json.dump(self.CREDS, f, indent=2)
			return True
		return False

	def doGet(self, url):
		res = requests.get(url, headers = {
			"Authorization": "Bearer {}".format(self.CREDS.get("access_token")),
			"Accept-Encoding":"gzip",
			"User-Agent":"kodi (gzip)"
		})
		if res.status_code == 200:
			return res.json()
		elif res.status_code == 401 and self.refreshToken():
			return self.doGet(url)
		else:
			return {}

	def getAlbumList(self):
		return self.doGet("https://photoslibrary.googleapis.com/v1/albums")

	def getMediaItems(self, pageToken = None):
		return self.doGet("https://photoslibrary.googleapis.com/v1/mediaItems"+ 
		"?fields=nextPageToken,mediaItems(baseUrl,mimeType,filename,mediaMetadata/width,mediaMetadata/height)"+
		"&pageSize=100"+
		("&pageToken={}".format(pageToken) if pageToken else ""))

	def getAlbumItems(self, albumId, pageToken = None):
		res = requests.post("https://photoslibrary.googleapis.com/v1/mediaItems:search"+
			"?fields=nextPageToken,mediaItems(baseUrl,mimeType,filename,mediaMetadata/width,mediaMetadata/height)",
			json={"albumId": albumId, "pageToken": pageToken, "pageSize":100 },
			headers={
				"Authorization": "Bearer {}".format(self.CREDS.get("access_token")),
				"Accept-Encoding":"gzip",
				"User-Agent":"kodi (gzip)"
			})
		if res.status_code == 200:
			return res.json()
		elif res.status_code == 401 and self.refreshToken():
			return self.getAlbumItems(albumId)
		else:
			return {}
