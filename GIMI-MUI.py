from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QPushButton, QGraphicsScene, QGraphicsPixmapItem, QGraphicsTextItem
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QPixmap, QFont, QIcon
import sys, os, shutil, datetime

class Main(QMainWindow):
    def __init__(self):
        """
        Initialize the Main window.

        Load the UI file, initialize QSettings, and set up the initial UI settings.
        """
        super(Main, self).__init__()
        loadUi("main.ui", self)
        self.settings = QSettings("github.io/jvill171", "GIMI ModUI")  # Initialize QSettings
        self.initUI()
    

    def initUI(self):
        """
        Set up the initial UI settings.

        Connect signals (e.g., browseButton clicked signal), disable maximize button,
        and set up any initial settings using setupSettings().
        """
        self.setWindowTitle('GIMI ModUI')
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)  # Disable maximize button
        self.setSignals()
        self.setupSettings()    # Set up any values for settings
        
        # self.setFixedSize(500, 500);

        
    def setSignals(self):
        """
        Connects signals from various buttons to their respective slots.

        - browseButton: Opens a file dialog to select a directory.
        - refreshButton: Refreshes the list of active and inactive mods.
        - addModButton: Moves selected items from inactiveModList to activeModList.
        - removeModButton: Moves selected items from activeModList to inactiveModList.
        - activeModList: Updates the mod name label when the current item changes.
        - inactiveModList: Updates the mod name label when the current item changes.
        """
        # Buttons
        self.browseButton.clicked.connect(self.openFileDialog)
        self.refreshButton.clicked.connect(self.setModDirs)
        self.addModButton.clicked.connect(lambda: self.moveMods(self.inactiveModList, self.activeModList, "Inactive", "Active"))    # Inactive => Active
        self.removeModButton.clicked.connect(lambda: self.moveMods(self.activeModList, self.inactiveModList, "Active", "Inactive")) # Active => Inactive
        
        # Connect current item change to updateModName method
        self.activeModList.currentItemChanged.connect(lambda: self.updateModName("Active"))
        self.inactiveModList.currentItemChanged.connect(lambda: self.updateModName("Inactive"))


    def setupSettings(self):
        """
        Set up application settings on startup.

        Load the last selected directory from QSettings, display it in selectedDirectoryLabel,
        set tooltips, and initialize mod directories using setModDirs().
        """
        # This line should only trigger on app's first use. Needed to ensure a value exists for last_directory
        if not self.settings.value("last_directory", ""):
            self.settings.setValue("last_directory", os.getcwd())

        # Load last selected directory on startup, default current directory
        modding_dir = self.settings.value("last_directory", os.getcwd())
        self.selectedDirectoryLabel.setText(modding_dir)
        self.selectedDirectoryLabel.setToolTip(modding_dir)
        self.setModDirs()


    def setModDirs(self):
        """
        Set directories for "Active" and "Inactive" mods.

        Args:
            modding_dir (str): Directory path where "Active" and "Inactive" directories are located.
        """

        # Reload mod lists based on current directories
        modding_dir = self.selectedDirectoryLabel.text()
        active_dir = os.path.join(modding_dir, "Active")
        inactive_dir = os.path.join(modding_dir, "Inactive")

        if os.path.exists(active_dir):
            self.listDirectories(active_dir, self.activeModList)

        if os.path.exists(inactive_dir):
            self.listDirectories(inactive_dir, self.inactiveModList)

        # Update button states based on directories
        active_exists = os.path.exists(active_dir)
        inactive_exists = os.path.exists(inactive_dir)
        self.activeModList.setEnabled(active_exists)
        self.inactiveModList.setEnabled(inactive_exists)
        self.addModButton.setEnabled(active_exists and inactive_exists)
        self.removeModButton.setEnabled(active_exists and inactive_exists)


    def openFileDialog(self):
        """
        Open a file dialog to select the Mods folder.

        Update selectedDirectoryLabel with the chosen directory path, save it to QSettings,
        and update mod directories using setModDirs().
        """
        options = QFileDialog.Options(QFileDialog.DontUseNativeDialog | QFileDialog.ShowDirsOnly)   # Use Qt-specific dialog | Only show directories
        directory = QFileDialog.getExistingDirectory(self, "Select Mods Folder", options=options)

        # Display selected directory in QLabel
        if directory:
            self.selectedDirectoryLabel.setText(directory)
            self.selectedDirectoryLabel.setToolTip(directory)
            # Save selected directory to QSettings
            self.settings.setValue("last_directory", directory)
            self.setModDirs()
    

    def listDirectories(self, directory, list_widget):
        """
        List directories within a specified directory and populate a QListWidget.

        Args:
            directory (str): Directory path to list directories from.
            list_widget (QListWidget): QListWidget to populate with directory names.
        """
        list_widget.clear()
        try:
            for item_name in os.listdir(directory):
                item_path = os.path.join(directory, item_name)
                if os.path.isdir(item_path):
                    list_widget.addItem(item_name)
        except Exception as e:
            self.logError(f"Error accessing directory: {e}")
    

    def moveMods(self, source_list, target_list, source_dir, target_dir):
        """
        Move selected items from source_list to target_list within the specified directories.

        Args:
            source_list (QListWidget): The QListWidget containing items to be moved.
            target_list (QListWidget): The QListWidget where items will be moved to.
            source_dir (str): Directory name where items are currently located.
            target_dir (str): Directory name where items will be moved.

        Moves selected items from source_list to target_list by physically moving
        corresponding directories/files from source_dir to target_dir. Updates the UI
        accordingly by removing items from source_list and adding them to target_list.

        If any error occurs during the move operation, an error message is printed
        indicating the failed directory/file move.
        """
        selected_items = source_list.selectedItems()
        for item in selected_items:
            item_name = item.text()
            src_path = os.path.join(self.selectedDirectoryLabel.text(), source_dir, item_name)
            dest_path = os.path.join(self.selectedDirectoryLabel.text(), target_dir, item_name)
            
            try:
                shutil.move(src_path, dest_path)    # Actually move the files
                source_list.takeItem(source_list.row(item)) # Remove the item from source 
                target_list.addItem(item_name)              # Place item in target
            except Exception as e:
                self.logError(f"Error moving {item_name}. Please Refresh Mod List.\n\t {e}")


    def updateModName(self, mod_status):
        """
        Update the mod name label and image preview based on the current selection.
        """
        # Determine the selected list based on mod_status
        if mod_status == "Active":
            selected_list = self.activeModList
            base_subdir = "Active"
        elif mod_status == "Inactive":
            selected_list = self.inactiveModList
            base_subdir = "Inactive"

        if selected_list:
            selected_item = selected_list.currentItem()
            if selected_item:
                mod_name = selected_item.text()
                self.modNameLabel.setText(mod_name)
                
                # Construct directory paths
                base_dir = self.selectedDirectoryLabel.text()
                mod_dir = os.path.join(base_dir, base_subdir, mod_name)
                preview_path = os.path.join(mod_dir, "preview.png")
                
                # Prepare the QGraphicsScene
                scene = QGraphicsScene()
                if os.path.exists(preview_path):
                    # Load preview image
                    pixmap = QPixmap(preview_path)
                    pixmap_item = QGraphicsPixmapItem(pixmap)
                    scene.addItem(pixmap_item)
                else:
                    # No preview image found
                    placeholder_text = QGraphicsTextItem("[ No Preview ]")
                    placeholder_text.setFont(QFont("Arial", 12))
                    scene.addItem(placeholder_text)
                
                # Set the scene for modPreview QGraphicsView
                self.modPreview.setScene(scene)
            else:
                # Handle case where no item is selected in the list
                self.modNameLabel.setText("")
                scene = QGraphicsScene()
                self.modPreview.setScene(scene)
        else:
            # Handle unknown mod_status
            self.modNameLabel.setText("")
            scene = QGraphicsScene()
            self.modPreview.setScene(scene)





    def logError(self, error_message):
        """
        Logs an error message with a timestamp.

        Parameters:
        error_message (str): The error message to log.
        """
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{current_time}] {error_message}"
        self.errorLogTextEdit.append(log_entry)
    


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Main()
    
    window.show()
    app.exec_()
