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

from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator, ClientFactory
from twisted.protocols import basic
import sys
import os

class FileSenderProtocol(basic.LineReceiver):
	def connectionMade(self):
		self.announceFile()

	def connectionLost(self, reason):
		print "Finsihed. Disconnected from server."

	def announceFile(self):
		if len(self.factory.local_remote_pairs) != 0:
			self.factory.current_pair = self.factory.local_remote_pairs.pop()
			remote_file = self.factory.current_pair[1]
			self.transport.write("RECV"+ remote_file +"\r\n")
		elif len(self.factory.remote_dirlist) != 0:
			remote_dir = self.factory.remote_dirlist.pop()
			print "Announcing dir : %s " % remote_dir
			self.transport.write("RECV" + remote_dir + "\r\n")
		else:
			reactor.stop()

	def lineReceived(self, line):
		print "Server responded"
		print line 
		if line.strip() == 'EXISTS':
			print "File already exists at target, skipping"
			# the file we wanted to send already exists, announce next
			self.announceFile()
		elif line.strip() == 'SEND':
			print "Okay to send file, sending"
			local_file = self.factory.current_pair[0]
			f = open(local_file, 'rb')
			self.setRawMode()
			self.transport.write(f.read())
			self.transport.write("\r\n")
			self.setLineMode()
			f.close()
		elif line.strip() == 'READY':
			# server is ready for next file, announce next
			self.announceFile()
		

class FileSenderFactory(ClientFactory):

	protocol = FileSenderProtocol

	def __init__(self, **kwargs):
		self.current_pair = None
		self.local_dir = kwargs['local_dir']
		self.remote_dir = kwargs['remote_dir']
		self.remote_dirlist = []
		self.local_remote_pairs = []
		self.local_remote_pairs, self.remote_dirlist =	scan_path(self.local_dir, self.remote_dir)


def scan_path(local_path, remote_path):
	local_root = os.path.abspath(os.path.expanduser(local_path))
	remote_root = remote_path
	remote_dirlist = []
	local_file = None
	remote_file = None
	local_remot_pairs = []
	for root, dirs, files in os.walk(local_root):
		remote_dirlist.append(
			os.path.normpath(
				remote_root + "/" + root.replace(local_root,'',1) + "D"
				))
		for f in files:
			local_file = os.path.normpath(root + "/" + f)
			remote_file = os.path.normpath(
				remote_root + "/" + root.replace(local_root,'',1) + "/" + f + "F"
				)
			local_remot_pairs.append((local_file, remote_file))
	return local_remot_pairs, remote_dirlist



if __name__ == '__main__':
	if len(sys.argv) < 4:
		print "Usage: ",sys.argv[0]," [host] [local_directory] [target_directory]"
		print "Mirrors [local_directory] to [target_directory]"
		sys.exit(0)

	reactor.connectTCP(sys.argv[1],1079, FileSenderFactory(
				local_dir=sys.argv[2],
				remote_dir=sys.argv[3]
				))
	reactor.run()
	
