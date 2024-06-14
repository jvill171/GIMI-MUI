from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidgetItem, QFileDialog
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, QSettings
import sys, os

class Main(QMainWindow):
    def __init__(self):
        super(Main, self).__init__()
        loadUi("main.ui", self)
        self.settings = QSettings("github.io/jvill171", "GIMI ModUI")  # Initialize QSettings
        self.initUI()
    

    def initUI(self):
        self.setWindowTitle('GIMI ModUI')
        self.browseButton.clicked.connect(self.openFileDialog)
        # Disable maximize button
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        
        # self.setFixedSize(500, 500);

        # Set up any values for settings
        self.setupSettings()


    def setupSettings(self):

        # Load last selected directory on startup, default current directory
        modding_dir = self.settings.value("last_directory", os.getcwd())
        self.selectedDirectoryLabel.setText(modding_dir)
        self.selectedDirectoryLabel.setToolTip(modding_dir)
        self.setModdingDirs(modding_dir=modding_dir)


    def setModdingDirs(self, modding_dir):
        # Set locations of expected "Active" & "Inactive" directories
        active_dir, inactive_dir = modding_dir + "/Active", modding_dir + "/Inactive"
        # Verify "Active" & "Inactive" directories exist
        active_exists, inactive_exists = os.path.exists(active_dir), os.path.exists(inactive_dir)

        if active_exists:
            self.listDirectories(active_dir, self.activeModList)
        else:
            self.activeModList.setEnabled(False)

        if inactive_exists:
            self.listDirectories(inactive_dir, self.inactiveModList)
        else:
            self.inactiveModList.setEnabled(False)
        
        if not (active_exists and inactive_exists):
            self.addModButton.setEnabled(False)
            self.removeModButton.setEnabled(False)
        

    def openFileDialog(self):
        options = QFileDialog.Options(QFileDialog.DontUseNativeDialog | QFileDialog.ShowDirsOnly)   # Use Qt-specific dialog | Only show directories
        directory = QFileDialog.getExistingDirectory(self, "Select Mods Folder", options=options)

        # Display selected directory in QLabel
        if directory:
            self.selectedDirectoryLabel.setText(directory)
            self.selectedDirectoryLabel.setToolTip(directory)
            # Save selected directory to QSettings
            self.settings.setValue("last_directory", directory)
    

    def listDirectories(self, directory, list_widget):
        list_widget.clear()
        try:
            for item_name in os.listdir(directory):
                item_path = os.path.join(directory, item_name)
                if os.path.isdir(item_path):
                    list_widget.addItem(item_name)
        except Exception as e:
            print(f"Error accessing directory: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Main()
    
    window.show()
    app.exec_()
