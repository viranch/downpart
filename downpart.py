#!/usr/bin/env python
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import urllib2
import httplib
import os

def qtBytes (size):
	if size>=(1024*1024):
		qtString = str.format ('{0:.2f} MB', size/1024.0/1024.0)
	else:
		qtString = str.format ('{0:.2f} KB', size/1024.0)
	return qtString

class Download (QThread):
	
	def __init__ (self, parent=None):
		super (Download, self).__init__(parent)
		self.parent = parent
	
	def run (self):
		if not self.parent.chdir ():
			return None
		self.emit (SIGNAL('setSize(int)'), 0)
		self.setStatus ('Looking up...')
		url = str( self.parent.urlEdit.text() )
		singleUser = self.parent.singleUser.isChecked()
		if 'http://' not in url and url!='':
			url = 'http://' + url
		
		try:
			self.supported = True
			src = urllib2.urlopen( url )
		except urllib2.HTTPError as error:
			return self.setStatus ('Error: ' + str(error))
		except urllib2.URLError as error:
			return self.setStatus ('Error: Could not lookup name or service.')
		except ValueError:
			if url=='':
				msg = 'Please enter an URL!'
			else:
				msg = 'The URL entered is invalid.'
			return self.setStatus ('Error:' + msg)
		except httplib.InvalidURL:
			return self.setStatus ('Error: The URL entered is invalid.')
		except:
			return self.setStatus ('Unknown error. Retry downloading.')
		
		try:
			size = int ( src.info()['Content-Length'] )
		except KeyError:
			if not singleUser:
				return self.setStatus ('Error: Server does not support partial downloads.\nTry downloading in single-user mode.')
			self.supported = False
			partsize = 0
		
		self.setStatus ('Found. Connecting...')
		
		if not singleUser:
			src.close()
			total_users = self.parent.totalCombo.currentIndex()+1
			curr_user = self.parent.currSpin.value()-1
			partsize = size/total_users
			if size%total_users != 0:
				partsize += 1
			begin = partsize*curr_user
			end = min( (begin-1) + partsize , size-1 )
			partsize = end-begin+1
			request = urllib2.Request ( url, headers={'Range' : 'bytes='+str(begin)+'-'+str(end)} )
			src = urllib2.urlopen ( request )
			save = open ( url.split('/')[-1]+'.'+str(curr_user+1) , 'wb' )
		else:
			if self.supported:
				partsize = size
			save = open ( url.split('/')[-1], 'wb' )
		self.qt_size = qtBytes (partsize)
		self.emit (SIGNAL('setSize(int)'), partsize)
		self.setStatus ('Downloading...')
		done_size = 0
		while done_size<partsize or not self.supported:
			buff = src.read ( 1024 )
			sz = len ( buff )
			if sz == 0 and not self.supported:
				self.emit(SIGNAL('setSize(int)'), done_size)
				self.supported = True
				self.qt_size = qtBytes (done_size)
				self.emit(SIGNAL('doneBytes(int)'), done_size)
				break
			save.write (buff)
			done_size += sz
			self.emit (SIGNAL('doneBytes(int)'), done_size)
		save.close()
		src.close()
	
	def setStatus (self, caption):
		self.parent.status.setText (caption)
		return None

class DownDlg (QDialog):
	
	def __init__ (self, parent=None):
		super (DownDlg, self).__init__(parent)
		
		urlLabel = QLabel ('&URL:')
		self.urlEdit = QLineEdit()
		urlLabel.setBuddy (self.urlEdit)
		dirLabel = QLabel ('&Save to:')
		self.dirEdit = QLineEdit(str(os.getcwd()))
		dirLabel.setBuddy (self.dirEdit)
		tmp = QDialogButtonBox (QDialogButtonBox.Open)
		browseButton = tmp.button (QDialogButtonBox.Open)
		self.singleUser = QCheckBox ('S&ingle User Mode')
		self.singleUser.setCheckState (Qt.Unchecked)
		browseButton.setText ('')
		browseButton.setMaximumWidth (30)
		self.totalLabel = QLabel ('&Divide into')
		self.totalCombo = QComboBox()
		self.totalCombo.addItems( ['1','2','3','4','5','6','7','8','9','10'] )
		self.totalCombo.setToolTip ('Set the number of total users going to be downloading the file')
		self.totalLabel.setBuddy (self.totalCombo)
		self.currLabel = QLabel ('parts, and download &part')
		self.currSpin = QSpinBox()
		self.currSpin.setRange (1, self.totalCombo.currentIndex()+1)
		self.currSpin.setToolTip ('Select the current user out of the total users for whom you want to download the file')
		self.currLabel.setBuddy (self.currSpin)
		self.pbar = QProgressBar()
		self.pbar.setMinimum(0)
		self.status = QLabel ()
		self.status.setAlignment (Qt.AlignHCenter | Qt.AlignVCenter)
		tmp.addButton (QDialogButtonBox.Apply)
		self.downButton = tmp.button (QDialogButtonBox.Apply)
		self.downButton.setText ('Download')
		self.downButton.setDefault (True)
		self.downButton.setAutoDefault (True)
		tmp.addButton (QDialogButtonBox.Close)
		self.closeButton = tmp.button (QDialogButtonBox.Close)
		self.downThread = Download (self)
		
		grid = QGridLayout()
		grid.addWidget (urlLabel, 0, 0)
		grid.addWidget (self.urlEdit, 0, 1, 1, 5)
		grid.addWidget (dirLabel, 1, 0)
		grid.addWidget (self.dirEdit, 1, 1, 1, 4)
		grid.addWidget (browseButton, 1, 5)
		grid.addWidget (self.singleUser, 2, 0, 1, 6)
		grid.addWidget (self.totalLabel, 3, 0)
		grid.addWidget (self.totalCombo, 3, 1)
		grid.addWidget (self.currLabel, 3, 2)
		grid.addWidget (self.currSpin, 3, 3)
		grid.addWidget (self.pbar, 4, 0, 1, 6)
		grid.addWidget (self.status, 5, 0, 1, 6)
		hbox = QHBoxLayout()
		hbox.addStretch(1)
		hbox.addWidget (self.downButton)
		hbox.addWidget (self.closeButton)
		grid.addLayout (hbox, 6, 0, 1, 6)
		grid.setColumnStretch (4, 1)
		self.setLayout (grid)
		self.setWindowTitle ('DownPart')
		
		self.connect (browseButton, SIGNAL('clicked()'), self.getDownDir)
		self.connect (self.singleUser, SIGNAL('stateChanged(int)'), self.toggleSingleUser)
		self.connect (self.totalCombo, SIGNAL('currentIndexChanged(int)'), self.updateRange)
		self.connect (self.downButton, SIGNAL('clicked()'), self.startDownload)
		self.connect (self.closeButton, SIGNAL('clicked()'), self, SLOT('close()'))
		self.connect (self.downThread, SIGNAL('setSize(int)'), self.pbarSetMaximum)
		self.connect (self.downThread, SIGNAL('doneBytes(int)'), self.updateStatus)
		self.connect (self.downThread, SIGNAL('finished()'), self.restoreState)
	
	def updateRange (self, index):
		self.currSpin.setRange (1, index+1)

	def toggleSingleUser (self, state):
		state = not state
		self.totalLabel.setEnabled (state)
		self.totalCombo.setEnabled (state)
		self.currLabel.setEnabled (state)
		self.currSpin.setEnabled (state)

	def getDownDir (self):
		wd = QFileDialog(self).getExistingDirectory()
		if wd!='':
			self.dirEdit.setText(wd)

	def startDownload (self):
		self.status.clear()
		self.downButton.setEnabled (False)
		self.closeButton.setText ('Cancel')
		self.downThread.start()

	def pbarSetMaximum (self, size):
		self.pbar.setMaximum (size)
		if size>0:
			self.pbar.setFormat ( "%p% of "+self.downThread.qt_size )

	def updateStatus (self, done_size):
		if self.downThread.supported:
			self.pbar.setValue ( done_size )
		self.status.setText ( qtBytes(done_size)+' downloaded' )

	def chdir (self):
		wd = str(self.dirEdit.text())
		if wd!='':
			try:
				os.chdir(str(wd))
				return True
			except OSError as error:
				start = str(error).find(']')+2
				if 'permission' in str(error).lower():
					err = QMessageBox.critical (self, 'Permission Denied', str(error)[start:])
				else:
					ch = QMessageBox.question (self, 'Not found', str(error)[start:]+'\nDo you want to create it?', QMessageBox.Yes|QMessageBox.No, QMessageBox.Yes)
					if ch==QMessageBox.Yes:
						try:
							os.makedirs (wd)
							os.chdir (wd)
							return True
						except OSError as error:
							start = str(error).find(']')+2
							err = QMessageBox.critical (self, 'Error', str(error)[start:])
		else:
			error = QMessageBox.critical (self, 'Invalid path', 'The \'Save to\' path cannot be empty.')
		return False
	
	def restoreState (self):
		self.downButton.setEnabled (True)
		self.closeButton.setText ('Close')

if __name__=='__main__':
	app = QApplication(sys.argv)
	main = DownDlg()
	main.show()
	app.exec_()

