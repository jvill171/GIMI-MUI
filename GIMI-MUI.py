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
        self.populatePatchSelector()
        
        # self.setFixedSize(500, 500);

        
    def setSignals(self):
        """
        Connects signals from various buttons to their respective slots.

        - browseButton: Opens a file dialog to select a directory.
        - refreshButton: Refreshes the list of enabled and disabled mods.
        - addModButton: Moves selected items from disabledModList to enabledModList.
        - removeModButton: Moves selected items from enabledModList to disabledModList.
        - enabledModList: Updates the mod name label when the current item changes.
        - disabledModList: Updates the mod name label when the current item changes.
        """
        # Buttons
        self.browseButton.clicked.connect(self.openFileDialog)
        self.refreshButton.clicked.connect(self.setModDirs)
        self.addModButton.clicked.connect(lambda: self.moveMods(self.disabledModList, self.enabledModList, "Disabled", "Enabled"))    # Disabled => Enabled
        self.removeModButton.clicked.connect(lambda: self.moveMods(self.enabledModList, self.disabledModList, "Enabled", "Disabled")) # Enabled => Disabled
        
        # Connect current item change to updatePreview method
        self.enabledModList.currentItemChanged.connect(lambda: self.updatePreview("Enabled"))
        self.disabledModList.currentItemChanged.connect(lambda: self.updatePreview("Disabled"))



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
        Set directories for "Enabled" and "Disabled" mods.

        This function recursively searches for .ini files within the "Mods" directory.
        Once an .ini file is found, its parent directory is listed in the Enabled or 
        Disabled section based on its prefix.
        """
        modding_dir = self.selectedDirectoryLabel.text()
        
        if not os.path.exists(modding_dir):
            self.logError(f"Directory {modding_dir} does not exist.")
            return

        enabled_mods = []
        disabled_mods = []

        for root, dirs, files in os.walk(modding_dir):
            for file in files:
                if file.endswith(".ini"):
                    mod_dir = os.path.basename(root)
                    if mod_dir.startswith("DISABLED_"):
                        disabled_mods.append(mod_dir)
                    else:
                        enabled_mods.append(mod_dir)
                    # Stop searching deeper once an .ini file is found
                    dirs[:] = []
                    break

        # Populate the lists in the UI
        self.enabledModList.clear()
        self.disabledModList.clear()

        self.enabledModList.addItems(enabled_mods)
        self.disabledModList.addItems(disabled_mods)


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
    

    def moveMods(self, source_list, target_list, source_status):
        """
        Enable/Disable every directory within source_list by adding/removing the "DISABLED_" based on source_status

        Args:
            source_list (QListWidget): The QListWidget containing items to be moved.
            target_list (QListWidget): The QListWidget where items will be moved to.
            source_status (str): Status of the source items ("Enabled" or "Disabled").

        Moves selected items from source_list to target_list by renaming the corresponding directories
        to add or remove the "DISABLED" prefix. Updates the UI accordingly by removing items from source_list
        and adding them to target_list.

        If any error occurs during the rename operation, an error message is printed indicating the failed 
        directory rename.
        """
        selected_items = source_list.selectedItems()
        for item in selected_items:
            item_name = item.text()
            mod_dir = self.findModDirectory(item_name)
            prefix = "DISABLED_"

            if not mod_dir:
                self.logError(f"Error finding directory for {item_name}.")
                continue
            
            if source_status == "Enabled":
                dest_path = mod_dir[:-len(item_name)] + prefix + item_name
            elif source_status == "":
                dest_path = mod_dir[:-len(item_name)] + item_name[len(prefix):]
            
            try:
                os.rename(mod_dir, dest_path)  # Rename the directory
                source_list.takeItem(source_list.row(item))  # Remove the item from source
                target_list.addItem(dest_path.split(os.sep)[-1])  # Place item in target
            except Exception as e:
                self.logError(f"Error renaming {item_name}. Please Refresh Mod List.\n\t {e}")


    def findModDirectory(self, mod_name):
        """
        Find the directory containing the mod.

        Args:
            mod_name (str): The name of the mod to find.

        Returns:
            str: The full path to the directory containing the mod, or None if not found.
        """
        for root, dirs, files in os.walk(self.selectedDirectoryLabel.text()):
            for name in dirs:
                if name == mod_name or name == f"DISABLED_{mod_name}":
                    return os.path.join(root, name)
        return None





    def updatePreview(self, mod_status):
        """
        Update the mod name label and image preview based on the current selection.
        """
        # Determine the selected list based on mod_status
        if mod_status == "Enabled":
            selected_list = self.enabledModList
            base_subdir = "Enabled"
        elif mod_status == "Disabled":
            selected_list = self.disabledModList
            base_subdir = "Disabled"

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


    def populatePatchSelector(self):
        patch_dir = os.path.join(self.selectedDirectoryLabel.text(), "PatchScripts")  # Directory containing .py and .exe files

        if not os.path.exists(patch_dir):
            print(f"Directory {patch_dir} does not exist.")
            return
        
        # Clear any existing items
        self.patchSelector.clear()
        
        # List all files in the patch directory
        files = os.listdir(patch_dir)
        
        # Filter files to include only .py and .exe files
        py_exe_files = [f for f in files if f.endswith(".py") or f.endswith(".exe")]
        
        # Add filtered files to the combobox
        self.patchSelector.addItems(py_exe_files)




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
