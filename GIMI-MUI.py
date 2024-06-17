from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QGraphicsScene, QGraphicsPixmapItem, QGraphicsTextItem
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QPixmap, QFont
import sys, os, datetime, subprocess
from enum import Enum

class Main(QMainWindow):
    
    # color of log messages
    class Color(Enum):
        SUCCESS = '#188524'
        WARNING = '#DC9752'
        ERROR = '#B30000'
        INFO = '#5050FF'


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

        self.addModButton.setText("\u2B9D")  # Unicode for ⮝
        self.removeModButton.setText("\u2B9F")  # Unicode for ⮟

        self.populatePatchSelector()
        
        # self.setFixedSize(500, 500);
        
    
    def normalizePath(self, path):
        """
        Normalizes the type of slashes to use. Mainly to be used when displaying paths rather than working with them.

        Args:
            path (str): A path to a resource
        """
        return path.replace("\\", "/")


    def setSignals(self):
        """
        Connects signals from various buttons to their respective slots.

        - browseButton: Opens a file dialog to select a directory.
        - refreshModsButton: Refreshes the list of enabled and disabled mods.
        - addModButton: Moves selected items from disabledModList to enabledModList.
        - removeModButton: Moves selected items from enabledModList to disabledModList.
        - enabledModList: Updates the mod name label when the current item changes.
        - disabledModList: Updates the mod name label when the current item changes.
        """
        # Buttons
        self.browseButton.clicked.connect(self.openFileDialog)
        self.refreshModsButton.clicked.connect(self.setModDirs)
        self.patchButton.clicked.connect(self.runPatch)
        self.refreshPatchButton.clicked.connect(self.populatePatchSelector)
        self.addModButton.clicked.connect(lambda: self.moveMods(self.disabledModList, self.enabledModList, "Disabled"))    # Disabled => Enabled
        self.removeModButton.clicked.connect(lambda: self.moveMods(self.enabledModList, self.disabledModList, "Enabled")) # Enabled => Disabled
        
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
            self.logMessage(f"MODS - Directory {self.normalizePath(modding_dir)} does not exist.", self.Color.ERROR)
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

        if len(enabled_mods) == 0 and len(disabled_mods) == 0:
             self.logMessage(f"MODS - No mods found in {modding_dir} and its children directories.", self.Color.WARNING)
        else:
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
            self.populatePatchSelector()
    

    def toggleWidget(self, widgets=[], enableWidget=None):
        """
        Toggle the enabled state of the specified widgets.

        This method flips the enabled state of each widget in the provided list.
        If a widget is currently enabled, it will be disabled, and vice versa.

        Parameters:
        widgets (list): A list of widgets to toggle the enabled state for.
        enableWidget (bool, optional): If provided, sets the widgets to this state. 
                                        If True, widgets are enabled. If False, widgets are disabled.
        """
        if enableWidget is None:
            for widget in widgets:
                widget.setEnabled(not widget.isEnabled())   # Flip the current state if no state is explicitly provided
        else:
            for widget in widgets:
                widget.setEnabled(enableWidget)    # If enabled, disable. If disabled, enable.


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
        self.toggleWidget([self.addModButton, self.removeModButton]) # Disable buttons while mods are being enabled/disabled
        for item in selected_items:
            item_name = item.text()
            mod_dir = self.findModDirectory(item_name)
            prefix = "DISABLED_"

            if not mod_dir:
                self.logMessage(f"MODS - Error: Could not find directory for {item_name}.[ Refresh Mod List ]", self.Color.ERROR)
                continue

            # Determine new directory name & path, for renaming
            if source_status == "Enabled":
                new_item_name = prefix + item_name
                new_status_msg = f"\u2796\u25BA Disabled {item_name}"
            else:
                new_item_name = item_name[len(prefix):]
                new_status_msg = f"\u2795\u25BA Enabled {new_item_name}"
            dest_path = mod_dir[:-len(item_name)] + new_item_name

            try:
                os.rename(mod_dir, dest_path)  # Rename the directory, thus enabling/disabling
                self.logMessage(new_status_msg)
                # Move from one widget to the other
                source_list.takeItem(source_list.row(item))
                target_list.addItem(dest_path.split(os.sep)[-1])
            except Exception as e:
                self.logMessage(f"MODS - Error renaming {item_name}. Try to [Refresh Mod List].\n\t {e}", self.Color.ERROR)
        self.toggleWidget([self.addModButton, self.removeModButton]) # Enable buttons once more after mods have been enabled/disabled


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
        return ""


    def updatePreview(self, mod_status):
        """
        Update the mod name label and image preview based on the current selection.
        """
        # Determine the selected list based on mod_status
        if mod_status == "Enabled":
            selected_list = self.enabledModList
        else:
            selected_list = self.disabledModList

        if selected_list:
            selected_item = selected_list.currentItem()
            if selected_item:
                mod_name = selected_item.text()
                self.modNameLabel.setText(mod_name)
                
                # Construct directory paths
                preview_path = os.path.join(self.findModDirectory(mod_name), "preview.png")
                
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
            self.logMessage(f'PATCH - Directory {self.normalizePath(self.normalizePath(patch_dir))} does not exist.', self.Color.WARNING)
            # Disable ability to patch directory if directory does not exist missing
            self.toggleWidget([self.patchSelector, self.patchButton], False)
            return

        # Clear any existing items
        self.patchSelector.clear()
        
        # List all files in the patch directory
        files = os.listdir(patch_dir)
        
        # Filter files to include only .py and .exe files
        py_exe_files = [f for f in files if f.endswith(".py") or f.endswith(".exe")]
        
        # Add filtered files to the combobox
        self.patchSelector.addItems(py_exe_files)

        # Enable/Disable ability to patch if a .py or .exe file exists
        if self.patchSelector.count() < 1:
            self.toggleWidget([self.patchSelector, self.patchButton], False)
            self.logMessage(f"PATCH - No patches found in {self.normalizePath(patch_dir)}")
        else:
            self.toggleWidget([self.patchSelector, self.patchButton], True)


    def runPatch(self):
        try:
            selected_script = os.path.join(os.getcwd(), "PatchScripts", self.patchSelector.currentText())
            if os.path.exists(selected_script) and os.path.isfile(selected_script):
                #*******************************************************************************************************************************************
                #               UNCOMMENT BEFORE CONVERTING TO EXE
                # self.runScript(selected_script, self.selectedDirectoryLabel.text())
                #*******************************************************************************************************************************************
                self.logMessage(f"RUNNING {selected_script}\n\tON {self.selectedDirectoryLabel.text()}")
            else:
                self.logMessage(f"PATCH - Failed to find [ {self.patchSelector.currentText()} ] in [{self.normalizePath(selected_script)}]", self.Color.WARNING)
        except Exception as e:
            self.logMessage(f"PATCH - Error: {e}", self.Color.ERROR)


    def runScript(self, script_path, target_directory):
        """
        Runs a given script (either .py or .exe) on the specified directory.

        Parameters:
        script_path (str): The path to the script file to be executed.
        target_directory (str): The directory on which the script should operate.
        """
        original_cwd = os.getcwd()  # Save current working directory

        try:
            # Validate script_path and target_directory
            if not os.path.isfile(script_path):
                raise ValueError(f"Script path {self.normalizePath(script_path)} does not point to a valid file.")

            if not os.path.isdir(target_directory):
                raise ValueError(f"Target directory {self.normalizePath(target_directory)} does not point to a valid directory.")
            
            # Change current working directory to target_directory
            os.chdir(target_directory)

            if script_path.endswith('.py'):
                # Use Popen to interact with subprocess
                proc = subprocess.Popen(["python", script_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            elif script_path.endswith('.exe'):
                proc = subprocess.Popen([script_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            else:
                raise ValueError("Script must be either a .py or .exe file.")
            
            # Optionally, you can send input to the subprocess
            # Here we simulate sending an 'enter' key press
            proc.communicate(input='\n')

            # Optionally, you can wait for the subprocess to finish
            proc.wait()

            # Check the result
            if proc.returncode == 0:
                self.logMessage(f"Script executed successfully!", self.Color.SUCCESS)
            else:
                self.logMessage(f"Script returned error code {proc.returncode}.", self.Color.ERROR)

        except Exception as e:
            self.logMessage(f"Error: {e}")
        finally:
            # Restore original working directory
            os.chdir(original_cwd)


    def logMessage(self, error_message, msg_type=Color.INFO):
        """
        Logs a message with a timestamp.

        Parameters:
        error_message (str): The error message to log.
        level (str): The type of message to log. Determines the color of the message.
        """
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = msg_type.value
        log_entry = f'[{current_time}] <span style="color:{color}">{error_message}</span>'
        self.errorLogTextEdit.append(log_entry)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Main()
    
    window.show()
    app.exec_()
