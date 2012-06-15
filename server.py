#!/usr/bin/env python

COPYRIGHT="""
Copyright (C) 2009 Sivan Greenberg
"""

MIT_LIC="""
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""


from twisted.internet import protocol, reactor, defer
from twisted.protocols import basic
import os


DEBUG_MODE = True

def ensure_path(create, path):
    if not path: return
    comps = path.split("/")
    comps = [i for i in comps if i!='']
    root = ""
    filepart = None
    if path[0]!='/': root = "."
    if os.path.isfile(path):
            filepart = comps[-1]
            comps.remove(filepart)
    for part in comps:
        cur = root + "/" + part
        if not os.path.exists(cur): 
            if create: 
                os.mkdir(cur)
            if DEBUG_MODE: print "creating directory %s" % (cur)
        root = root + "/" + part

class SynchRecvProtocl(basic.LineReceiver):
	def lineReceived(self, line):
		line = line.strip()
		if line.startswith("RECV"):
			filename = line[4:-1]
			nodetype = line[-1:]
			print "nodetype:", nodetype
			if nodetype=="D":
				print "Creating directory : %s" % filename
				ensure_path(True,filename)
				self.transport.write('READY\r\n')
			else:
				print "Preapring to RECV %s" % filename
				if os.path.exists(filename):
					print "Oops, file already exists, skipping"
					self.transport.write('EXISTS\r\n')
				else:
					self.transport.write('SEND\r\n')
					self.factory.filename = filename
					newpath = "/".join(filename.split('/')[:-1])
				 	print "newpath: %s" % newpath
					ensure_path(True, newpath )
					self.setRawMode()

	def rawDataReceived(self, data):
			print "size of data: %s" % len(data)
			filename = self.factory.filename
			print "Getting raw data and saving to disk"
			f = open(filename,'ab')
			if data.endswith('\r\n'):
				data = data[:-2]
				f.write(data)
				print "last chunk of data"
				f.close()
				self.setLineMode()
				print "Finished transferring file"
				self.sendLine('READY\r\n')
			else:
				f.write(data)



class SynchFactory(protocol.ServerFactory):
	protocol = SynchRecvProtocl
	filelist = []
	filename = ''





reactor.listenTCP(1079, SynchFactory())
reactor.run()
