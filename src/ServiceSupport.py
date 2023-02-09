#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2011 betonme, 2023 pjsharp
#
# In case of reuse of this source code please do not remove this copyright.
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	For more information on the GNU General Public License see:
#	<http://www.gnu.org/licenses/>.
#
from __future__ import absolute_import
import os
import struct
from datetime import datetime
from time import mktime

from Components.config import *
from enigma import eServiceCenter, iServiceInformation, eServiceReference
from ServiceReference import ServiceReference
from .EMCFileCache import movieFileCache
from .CutListSupport import CutList
from .CommonSupport import getInfoFile, readPlaylist
from .RecordingsControl import getRecording


instance = None


class ServiceCenter:
	def __init__(self):
		global instance
		instance = eServiceCenter.getInstance()
		instance.info = self.info

	@staticmethod
	def getInstance():
		global instance
		if instance is None:
			ServiceCenter()
		return instance

	def info(self, service):
		if service:		
			return ServiceInfo(service)
		else:
			return None


class ServiceInfo:
	def __init__(self, service):
		self.service = service
		self.serviceHandler = eServiceCenter.getInstance()
		self.info = self.serviceHandler and self.serviceHandler.info(service)
		self.event = ServiceEvent(service, self) 
		self.path = service.getPath()
		self.isfile = os.path.isfile(self.path)
		self.isdir = os.path.isdir(self.path)		

	def getName(self, service):
		return self.info and self.info.getName(service) or ""

	def getLength(self, service):
		return self.event and self.event.getDuration() or 0

	def getInfoString(self, service, type):
		return self.info and self.info.getInfoString(service, type) or ""

	def getEvent(self, service, *args):
		return self.event

	def isPlayable(self):
		return self.info and self.info.isPlayable() or False

	def getInfo(self, service, type):
		if type == iServiceInformation.sTimeCreate and not self.isfile:
			return 0
		return self.info and self.info.getInfo(service, type) or 0

	def getInfoObject(self, param1, param2=None):
		if param2:
			if param2 == iServiceInformation.sFileSize:
				return self.isfile and os.stat(self.path).st_size or self.isdir and (config.EMC.directories_info.value or config.EMC.directories_size_skin.value) and self.__getFolderSize(self.path) or None
			else:
				return self.info and self.info.getInfoObject(param1, param2) or None
		else:
			return self.info and self.info.getInfoObject(param1) or None

	def getTransponderData(self, service):
		return self.info and self.info.getTransponderData(service) or None

	def getFileSize(self, service):
		return self.info and self.info.getFileSize(service) or 0
		
	def __getFolderSize(self, path):
		folder_size = 0
		if config.EMC.directories_size_skin.value:
			getValues = movieFileCache.getCountSizeFromCache(path)
			if getValues is not None:
				count, size = getValues
				if size is not None:
					folder_size = size * 1024 * 1024 * 1024
		return folder_size
		

class ServiceEvent:
	def __init__(self, service, serviceInfo):
		self.service = service
		self.serviceInfo = serviceInfo
		self.event = self.serviceInfo.info and self.serviceInfo.info.getEvent(service)
		self.path = service.getPath()
		self.isfile = os.path.isfile(self.path)
		self.ext = self.path and os.path.splitext(self.path)[1].lower()
		
	def getBeginTime(self):
		beginTime = None
		if not config.EMC.record_show_real_length.value:
			beginTime = self.event and self.event.getBeginTime()
		if not beginTime:
			dt = self.isfile and hasattr(self.service, "date") and self.service.date or None
			if dt:
				beginTime = datetime.timestamp(dt)
		return beginTime

	def getDuration(self):
		return self.__getDuration()

	def getEventId(self):
		return self.event and self.event.getEventId() or 0

	def getPdcPil(self):
		return self.event and self.event.getPdcPil() or 0

	def getRunningStatus(self):
		return self.event and self.event.getRunningStatus() or 0

	def getEventName(self):
		return self.event and self.event.getEventName() or self.serviceInfo.getName(self.service) or self.service.getName() or ""

	def getShortDescription(self):
		return self.event and self.event.getShortDescription() or ""

	def getExtendedDescription(self):
		return self.__getExtendedDescription()
		
	def getExtraEventData(self):
		return self.event and self.event.getExtraEventData() or None

	def getEPGSource(self):
		return self.event and self.event.getEPGSource() or None

	def getBeginTimeString(self):
		beginTime = self.getBeginTime()
		dt = beginTime and datetime.fromtimestamp(beginTime)
		if dt:
			if config.EMC.movie_date_format.value:
				return dt.strftime(config.EMC.movie_date_format.value)
			else:
				return dt.strftime("%d.%m.%Y %H:%M")
		else:
			return None
			
	def getSeriesCRID(self):
		return self.event and self.event.getSeriesCRID() or None

	def getEpisodeCRID(self):
		return self.event and self.event.getEpisodeCRID() or None

	def getRecommendationCRID(self):
		return self.event and self.event.getRecommendationCRID() or None

	def __getDuration(self):
		duration = 0
		
		if config.EMC.record_show_real_length.value:
			# If it is a record we will force to use the timer duration		
			record = getRecording(self.path)
			if record:
				begin, end, service = record
				duration = end - begin # times = (begin, end) : end - begin
		else:
			duration = self.event and self.event.getDuration() or 0
			
		if not duration:
			if self.isfile:
				duration = self.serviceInfo.info and self.serviceInfo.info.getLength(self.service) or 0
			if duration <= 0:
				duration = self.__getCutListLength()
			if duration > 86400:
				duration = 0

		return duration or 0

	def __getExtendedDescription(self):
		extendedDescription = self.event and self.event.getExtendedDescription() or ""
	
		if not extendedDescription:
			if self.isfile:
				if not self.event or not self.event.getShortDescription() and not self.serviceInfo.getInfoString(self.service, iServiceInformation.sDescription):
					exts = [".txt"]
					txtpath = getInfoFile(self.path, exts)[1]

					# read the playlist-entrys to show the list as overview
					if self.ext == ".e2pls":
						plistdesc = ""
						plist = readPlaylist(self.path)
						for x in plist:
							plistdesc += x
						extendedDescription = plistdesc
					else:
						if os.path.exists(txtpath):
							txtdescarr = open(txtpath).readlines()
							txtdesc = ""
							for line in txtdescarr:
								txtdesc += line
							extendedDescription = txtdesc
						elif config.EMC.show_path_extdescr.value:
							if config.EMC.movie_real_path.value:
								extendedDescription = os.path.realpath(self.path)
							else:
								extendedDescription = self.path
						else:
							extendedDescription = ""
			else:
				extendedDescription = self.path			
		return extendedDescription
		
	def __getCutListLength(self):
		cutlist = self.path and CutList(self.path) or []
		length = cutlist and cutlist.getCutListLength() or 0
		return length
