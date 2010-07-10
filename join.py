#!/usr/bin/env python
import sys
import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class Join (QThread):
	
	def __init__ (self, parent):
		super (Join, self).__init__(parent)
		self.parent = parent
		self.done = False
		self.progress = QProgressBar()
	
	def run (self):
		try:
			self.parent.status.setText ('Starting...')
			final = open ( self.parent.saveEdit.text(), 'wb' )
			total = len(self.parent.files)
			count = 0
			for file in self.parent.files:
				count += 1
				size = os.path.getsize(file)
				self.progress.setValue (0)
				self.progress.setRange (0, size)
				self.parent.progressBar.setRange (0, size)
				self.parent.status.setText ( 'Appending file ' + str(count)+'/'+str(total) + '...' )
				part = open ( file, 'rb' )
				while True:
					buff = part.read(size/50)
					if len(buff)==0:
						break
					final.write(buff)
					self.progress.setValue (self.progress.value()+len(buff))
				part.close()
			final.close()
			self.done = True
		except IOError as error:
			self.parent.status.setText (str(error))
			pass

class JoinDlg (QDialog):

	def __init__ (self, parent=None):
		super (JoinDlg, self).__init__(parent)

		fileLabel = QLabel ('Files:')
		self.fileList = QListWidget()
		self.files = []
		tmp = QDialogButtonBox (QDialogButtonBox.Open | QDialogButtonBox.Save)
		if os.access ('/usr/share/icons/oxygen/16x16/actions/list-add.png', os.F_OK):
			addButton = QPushButton ( QIcon('/usr/share/icons/oxygen/16x16/actions/list-add.png'), '')
			addButton.setMaximumWidth (30)
		else:
			addButton = QPushButton ('Add...')
		addButton.setToolTip ('Add files...')
		if os.access ('/usr/share/icons/oxygen/16x16/actions/list-remove.png', os.F_OK):
			rmButton = QPushButton ( QIcon('/usr/share/icons/oxygen/16x16/actions/list-remove.png'), '')
			rmButton.setMaximumWidth (30)
		else:
			rmButton = QPushButton ('Remove')
		rmButton.setToolTip ('Remove')
		if os.access ('/usr/share/icons/oxygen/16x16/actions/edit-clear.png', os.F_OK):
			clearButton = QPushButton ( QIcon('/usr/share/icons/oxygen/16x16/actions/edit-clear.png'), '')
			clearButton.setMaximumWidth (30)
		else:
			clearButton = QPushButton ('Clear')
		clearButton.setToolTip ('Clear All')
		saveLabel = QLabel ('&Save to:')
		self.saveEdit = QLineEdit()
		saveLabel.setBuddy (self.saveEdit)
		saveButton = tmp.button (QDialogButtonBox.Save)
		saveButton.setText ('')
		saveButton.setMaximumWidth (30)
		saveButton.setToolTip ('Browse...')
		self.progressBar = QProgressBar()
		self.status = QLabel()
		self.status.setAlignment (Qt.AlignHCenter | Qt.AlignVCenter)
		self.buttonBox = QDialogButtonBox ( QDialogButtonBox.Ok | QDialogButtonBox.Cancel )
		self.buttonOk = self.buttonBox.button (QDialogButtonBox.Ok)
		self.buttonCancel = self.buttonBox.button (QDialogButtonBox.Cancel)
		self.buttonOk.setText ('Join')
		self.buttonCancel.setText ('Close')
		self.joinThread = Join(self)

		grid = QGridLayout()
		grid.addWidget (fileLabel, 0, 0)
		grid.addWidget (self.fileList, 1, 0, 5, 2)
		grid.addWidget (addButton, 2, 2)
		grid.addWidget (rmButton, 3, 2)
		grid.addWidget (clearButton, 4, 2)
		grid.addWidget (saveLabel, 6, 0)
		grid.addWidget (self.saveEdit, 6, 1)
		grid.addWidget (saveButton, 6, 2)
		grid.addWidget (self.progressBar, 7, 0, 1, 3)
		grid.addWidget (self.status, 8, 0, 1, 3)
		grid.addWidget (self.buttonBox, 9, 0, 1, 3)
		self.setLayout (grid)
		self.setWindowTitle ('Join')

		self.connect (addButton, SIGNAL('clicked()'), self.getFiles)
		self.connect (rmButton, SIGNAL('clicked()'), self.removeItems)
		self.connect (clearButton, SIGNAL('clicked()'), self.clear)
		self.connect (saveButton, SIGNAL('clicked()'), self.getSaveFile)
		self.connect (self.buttonOk, SIGNAL('clicked()'), self.join)
		self.connect (self.buttonCancel, SIGNAL('clicked()'), self, SLOT('close()'))
		self.connect (self.joinThread.progress, SIGNAL('valueChanged(int)'), self.progressBar, SLOT('setValue(int)'))
		self.connect (self.joinThread, SIGNAL('finished()'), self.setStatus)

	def getFiles (self):
		fileNames = QFileDialog(self).getOpenFileNames()
		self.buttonOk.setText ('Join')
		self.buttonCancel.setText ('Close')
		files = []
		for i in range(len(fileNames)):
			self.files.append (str(fileNames[i]))
			self.fileList.addItem ( str(fileNames[i]).rsplit('/',1)[1] )

	def removeItems (self):
		x = self.fileList.currentRow()
		self.fileList.takeItem (x)
		self.files.pop (x)

	def clear (self):
		self.fileList.clear()
		self.files = []
		self.status.setText ('')

	def getSaveFile (self):
		self.saveEdit.setText ( QFileDialog(self).getSaveFileName() )

	def join (self):
		self.buttonOk.setEnabled (False)
		self.buttonCancel.setText ('Cancel')
		self.joinThread.start()
	
	def setStatus (self):
		self.buttonOk.setEnabled (True)
		self.buttonCancel.setText ('Close')
		if self.joinThread.done:
			self.status.setText ('Complete')

app = QApplication (sys.argv)
dlg = JoinDlg()
dlg.show()
app.exec_()
