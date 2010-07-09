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
		self.connect (self.progress, SIGNAL('valueChanged(int)'), self.parent.progressBar, SLOT('setValue(int)'))
	
	def run (self):
		try:
			self.parent.status.setText ('Opening output file...')
			final = open ( self.parent.saveEdit.text(), 'wb' )
			total = self.parent.fileList.count()
			count = 0
			for file in self.parent.files:
				count += 1
				self.progress.setRange (0, os.path.getsize(file))
				size = os.path.getsize(file)
				self.parent.progressBar.setRange (0, size)
				self.progress.setValue (0)
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
		addButton = QPushButton ( QIcon('/usr/share/icons/oxygen/16x16/actions/list-add.png'), '')
		addButton.setMaximumWidth (30)
		addButton.setToolTip ('Add...')
		rmButton = QPushButton ( QIcon('/usr/share/icons/oxygen/16x16/actions/list-remove.png'), '')
		rmButton.setMaximumWidth (30)
		rmButton.setToolTip ('Remove')
		clearButton = QPushButton ( QIcon('/usr/share/icons/oxygen/16x16/actions/edit-clear.png'), '')
		clearButton.setMaximumWidth (30)
		clearButton.setToolTip ('Clear All')
		saveLabel = QLabel ('&Save to:')
		self.saveEdit = QLineEdit()
		saveLabel.setBuddy (self.saveEdit)
		saveButton = tmp.button (QDialogButtonBox.Save)
		saveButton.setText ('')
		saveButton.setMaximumWidth (30)
		self.progressBar = QProgressBar()
		self.status = QLabel('Select files to join and choose output file')
		self.status.setAlignment (Qt.AlignHCenter | Qt.AlignVCenter)
		self.buttonBox = QDialogButtonBox ( QDialogButtonBox.Ok | QDialogButtonBox.Cancel )
		self.buttonOk = self.buttonBox.button (QDialogButtonBox.Ok)
		self.buttonCancel = self.buttonBox.button (QDialogButtonBox.Cancel)
		self.buttonOk.setText ('Join')
		self.buttonCancel.setText ('Close')
		self.thread = Join(self)

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
		self.connect (clearButton, SIGNAL('clicked()'), self.fileList.clear)
		self.connect (saveButton, SIGNAL('clicked()'), self.getSaveFile)
		self.connect (self.buttonOk, SIGNAL('clicked()'), self.join)
		self.connect (self.buttonCancel, SIGNAL('clicked()'), self, SLOT('close()'))
		self.connect (self.thread, SIGNAL('finished()'), self.setStatus)

	def getFiles (self):
		fileNames = QFileDialog(self).getOpenFileNames()
		fileNames.sort()
		self.fileList.addItems (fileNames)
		for item in fileNames:
			self.files.append (str(item))
		self.progressBar.setRange (0, len(self.files))
		self.buttonOk.setText ('Join')
		self.buttonCancel.setText ('Close')

	def removeItems (self):
		x = self.fileList.currentRow()
		self.fileList.takeItem (x)
		self.files.pop (x)
		self.progressBar.setRange (0, len(self.files))
	
	def getSaveFile (self):
		self.saveEdit.setText ( QFileDialog(self).getSaveFileName() )

	def join (self):
		self.thread.start()
	
	def setStatus (self):
		if self.thread.done:
			self.status.setText ('Complete!')

app = QApplication (sys.argv)
dlg = JoinDlg()
dlg.show()
app.exec_()
