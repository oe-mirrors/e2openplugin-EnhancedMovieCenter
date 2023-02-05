#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2023 pjsharp
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
import re
from .EMCTasker import emcDebugOut


## Import from MetaSupport.py (temporary)
def getInfoFile(path, exts=""):
	from .MovieCenter import extMedia
	fpath = p1 = p2 = p3 = ""
	name, ext = os.path.splitext(path)
	ext = ext.lower()

	if os.path.isfile(path) and ext in extMedia:			#files & movie structures
		dir = os.path.dirname(path)
		p1 = name						# filename.ext
		p2 = os.path.join(dir, os.path.basename(dir))		# folder.ext if no filename.ext

	elif os.path.isdir(path):
		if path.lower().endswith("/bdmv"):			# bluray structures
			dir = path[:-5]
			if dir.lower().endswith("/brd"):
				dir = dir[:-4]
		elif path.lower().endswith("video_ts"):			# DVD structures
			dir = path[:-9]
			if dir.lower().endswith("/dvd"):
				dir = dir[:-4]
		else:							# folders
			dir = path
			p2 = os.path.join(dir, "folder")		# "folder.ext"

		prtdir, dirname = os.path.split(dir)
		p1 = os.path.join(dir, dirname)				# /dir/dirname.ext
		p3 = os.path.join(prtdir, dirname)			# /prtdir/dirname.ext, show AMS-files

	pathes = [p1, p2, p3]
	for p in pathes:
		for ext in exts:
			fpath = p + ext
			if os.path.exists(fpath):
				break
		if os.path.exists(fpath):
			break
	return (p1, fpath)

	
def getMetaTitleFromDescription(desc): # taken over from MetaSupport.py, necessary ??
	#TODO make it better and --> for example get the right title from other meta like "title only"
	title = ""
	try:
		x1 = len(desc.split(',', -1)) - 1
		x2 = x1 - 1
		title = desc.replace(desc.split(',', -1)[x1], '').replace(desc.split(',', -1)[x2], '').replace(',,', '')
		if title == ",":
			if re.match('(\w+(?:/\w+|)(?:/\w+|)(?:/\w+|)(?:/\w+|)\s\d{4})', desc.rsplit(',', 1)[1].strip(), re.S):
				title = ''
			else:
				if len(desc) > 50:
					title = desc[:47] + "..."
				else:
					title = desc
		elif (len(title) >= 50) or (len(title) < 3):
			if len(desc) > 50:
				title = desc[:47] + "..."
			else:
				title = desc
	except Exception as e:
		emcDebugOut("[EMC] getMetaTitle failed !!!\n" + str(e))
	return title					
