from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QGraphicsScene, QGraphicsPixmapItem, QGraphicsTextItem, QListWidgetItem
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QPixmap, QFont, QIcon
import sys, os, datetime, subprocess, warnings
from main_ui import Ui_MainWindow  # Ui_MainWindow is the class in main_ui.py
from enum import Enum
from assets import resources_rc  # Import the compiled resource module


# Ignore the deprecation warning
warnings.filterwarnings(action='ignore', category=DeprecationWarning, lineno=21)

# Helper class for defining colors of logged messages
class Color(Enum):
    SUCCESS = '#188524'
    WARNING = '#DC9752'
    ERROR = '#B30000'
    INFO = '#5050FF'


class Main(QMainWindow):

    def __init__(self):
        """
        Initialize the Main window.

        Load the UI file, clear the image carousel data, and set up the initial UI settings.
        """
        super(Main, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.settings = QSettings("github.io/jvill171", "GIMI ModUI")  # Initialize QSettings
        self.initUI()
        self.setIcon()  # Set the application icon
        
        self.carousel_images = []
        self.carousel_idx = 0
    

    def setIcon(self):
        """
        Apply the logo icon
        """
        for root, _, files in os.walk(os.getcwd()):
            for file in files:
                if file == "LogoImg.png" or file == "LogoImg.jpg":
                    self.setWindowIcon(QIcon(os.path.join(root, file)))
                    return;
            return; # Only observe top level


    def initUI(self):
        """
        Set up the initial UI settings.

        Connect signals, and set up any initial settings.
        """
        self.setWindowTitle('GIMI ModUI')
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)  # Disable maximize button
        self.setSignals()
        self.setUnicodeText()
        
        if self.settings.value("key"): self.ui.swapKeyLineEdit.setText(self.settings.value("key"))
        if self.settings.value("name"): self.ui.mergeNameLineEdit.setText(self.settings.value("name"))

        self.updateMergeButton()
        self.clearPreviewAndRefresh()
        self.setIconGraphicsView()
        self.setLightDark() # Set light/dark mode from saved settings


    def setUnicodeText(self):
        """
        Set unicode text for specific widgets
        """
        # Enable/Disable buttons
        self.ui.addModButton.setText("\u2B9D")  # Unicode for ⮝
        self.ui.removeModButton.setText("\u2B9F")  # Unicode for ⮟
        # Image preview buttons
        self.ui.previewModBackButton.setText("\u25c0")     # Unicode for ◀
        self.ui.previewMergeBackButton.setText("\u25c0")   # Unicode for ◀
        self.ui.previewModNextButton.setText("\u25b6")     # Unicode for ▶
        self.ui.previewMergeNextButton.setText("\u25b6")   # Unicode for ▶


    def setSignals(self):
        """
        Connects signals from various buttons to their respective slots.
        """
        # Buttons
        self.ui.switchModeButton.clicked.connect(self.toggle_mode) # Light/Dark mode
        self.ui.findFolderButton.clicked.connect(self.browseMergeDir)
        self.ui.mergeModsButton.clicked.connect(self.runMerge)
        self.ui.refreshModsButton.clicked.connect(self.populateModLists)
        self.ui.refreshMergeButton.clicked.connect(self.populateMergeList)
        self.ui.patchButton.clicked.connect(self.runPatch)
        self.ui.addModButton.clicked.connect(lambda: self.moveMods(self.ui.disabledModList, self.ui.enabledModList, "Disabled"))     # Disabled => Enabled
        self.ui.removeModButton.clicked.connect(lambda: self.moveMods(self.ui.enabledModList, self.ui.disabledModList, "Enabled"))   # Enabled => Disabled

        # Add signals for image preview navigation buttons
        self.ui.previewModBackButton.clicked.connect(self.showPrevImage)
        self.ui.previewMergeBackButton.clicked.connect(self.showPrevImage)
        self.ui.previewModNextButton.clicked.connect(self.showNextImage)
        self.ui.previewMergeNextButton.clicked.connect(self.showNextImage)

        # Enable or Disable the "Merge Mods" Button based its dependencies
        self.ui.swapKeyLineEdit.textChanged.connect(self.updateMergeButton)
        self.ui.mergeDirLineEdit.textChanged.connect(self.updateMergeButton)
        
        # Connect current item change to updatePreview method
        self.ui.enabledModList.currentItemChanged.connect(lambda: self.updatePreview("Enabled"))
        self.ui.disabledModList.currentItemChanged.connect(lambda: self.updatePreview("Disabled"))
        self.ui.mergeModList.currentItemChanged.connect(self.updatePreview)
        
        # When tab is changed
        self.ui.tabWidget.currentChanged.connect(self.clearPreviewAndRefresh)
        
        
    def setLightDark(self):
        """
        Get dark_mode setting from self.settings & set up light/dark mode
            Default: False (Light mode)
        """
        self.dark_mode = self.settings.value("dark_mode", defaultValue=False, type=bool)
        if self.dark_mode:
            self.set_dark_mode()
        else:
            self.set_light_mode()
    

    def toggle_mode(self):
        """
        Toggle between light and dark mode
        """
        if self.dark_mode:
            self.set_light_mode()
        else:
            self.set_dark_mode()
        self.dark_mode = not self.dark_mode
        self.settings.setValue("dark_mode", self.dark_mode)
        
    
    def set_light_mode(self):
        """
        Apply Light mode styles to QMainWindow
        """
        self.ui.switchModeCircle.move(2, 2)
        self.ui.switchModeCircle.setStyleSheet("background-color: white; border-radius: 6px; border: 1px solid gray;")
        self.ui.switchModeFrame.setStyleSheet("background-color: lightgray; border-radius: 7px;")
        
        self.setStyleSheet(getMainStyles())

    
    def set_dark_mode(self):
        """
        Apply Dark mode styles to QMainWindow
        """
        self.ui.switchModeCircle.move(18, 2)
        self.ui.switchModeCircle.setStyleSheet("background-color: gray; border-radius: 6px; border: 1px solid white;")
        self.ui.switchModeFrame.setStyleSheet("background-color: darkgray; border-radius: 7px;")

        self.setStyleSheet(getMainStyles() + """ 
            #MainWindow, #centralwidget, #manageTab, #mergeTab{
                background-color: #252530;
            }
            .QLabel, .QGroupBox, .QCheckBox:unchecked:enabled{
                color: white;
            }
            """)


    def clearPreviewAndRefresh(self, index=0):
        """
        Clear the image preview data and refresh the respective mod lists
        """
        # Clear image preview
        self.carousel_images = []
        self.ui.previewModImage.setScene(QGraphicsScene())
        self.ui.previewMergeImage.setScene(QGraphicsScene())

        # Refresh tab's list data, in the case files were moved/renamed
        tab_name = self.ui.tabWidget.tabText(index).lower()
        if tab_name == "manage":
            self.populateModLists()
            self.toggleWidget([self.ui.previewModBackButton, self.ui.previewModNextButton], enableWidget=False)
        if tab_name == "merge":
            self.populateMergeList()
            self.toggleWidget([self.ui.previewMergeBackButton, self.ui.previewMergeNextButton], enableWidget=False)


    def updateMergeButton(self):
        """
        Enables/Disables Merge Mods button.

        If swapKeyLineEdit or mergeDirLineEdit has any text, the button is enabled. Else it is disabled.
        """
        # Enable the button only if both QLineEdits are not empty
        if self.ui.swapKeyLineEdit.text() and self.ui.mergeDirLineEdit.text() and self.ui.mergeModList.count() > 1:
            self.toggleWidget([self.ui.mergeModsButton], enableWidget=True)
        else:
            self.toggleWidget([self.ui.mergeModsButton], enableWidget=False)


    def saveSetting(self, dict_data):
        """
        Save the last attempted settings the user tried to merge mods with.

        dict_data (dictionary): Key-value pairs to save into settings.
        """
        for key, value in dict_data.items():
            self.settings.setValue(key, value)


    def populateModLists(self):
        """
        Set directories for "Enabled" and "Disabled" mods.

        This function recursively searches for .ini files within the "Mods" directory.
        Once an .ini file is found, its parent directory is listed in the Enabled or 
        Disabled section based on its prefix.
        """
        modding_dir = os.path.join(os.getcwd(), "Mods")

        if not os.path.exists(modding_dir):
            self.logMessage(f"Directory {os.path.normpath(modding_dir)} does not exist.", Color.ERROR)
            return

        enabled_mods = []
        disabled_mods = []

        for root, dirs, files in os.walk(modding_dir):
            if "BufferValues" in root or "ShaderCache" in root or "ShaderFixes" in root:
                continue;
            for file in files:
                if file.endswith(".ini"):
                    mod_item = QListWidgetItem(os.path.basename(root))
                    mod_item.setToolTip(os.path.normpath(root))
                    
                    if os.path.basename(root).startswith("DISABLED"):
                        disabled_mods.append(mod_item)
                    else:
                        enabled_mods.append(mod_item)
                        
                    # Stop searching deeper once an .ini file is found
                    dirs[:] = []
                    break

        # Populate the lists in the UI
        self.ui.enabledModList.clear()
        self.ui.disabledModList.clear()

        if len(enabled_mods) == 0 and len(disabled_mods) == 0:
            self.logMessage(f"No mods found in {modding_dir} or its children directories.", Color.WARNING)
        else:
            for item in enabled_mods:
                self.ui.enabledModList.addItem(item)
            for item in disabled_mods:
                self.ui.disabledModList.addItem(item)


    def populateMergeList(self):
        """
        Populate the QListWidget with items based on the provided directory.

        This function recursively searches for .ini files within the directory
        specified in QLineEdit.mergeDirLineEdit QWidget. Once an .ini file is
        found, its parent directory is listed in the Merge list.
        """
        merge_dir = os.path.normpath( self.ui.mergeDirLineEdit.text() )

        if not os.path.exists(merge_dir):
            if merge_dir != "": self.logMessage(f"Directory {os.path.normpath(merge_dir)} does not exist.", Color.ERROR)
            return
        
        self.ui.mergeModList.clear()
        
        for root, dirs, files in os.walk(merge_dir):
            for file in files:
                if file.endswith(".ini"):
                    item = QListWidgetItem(os.path.basename(root))
                    item.setToolTip(os.path.normpath(root))
                    self.ui.mergeModList.addItem(item)
                    # Stop searching deeper once an .ini file is found
                    dirs[:] = []
                    break

        self.updateMergeButton()    # Check if Merge button can be enabled
        if self.ui.mergeDirLineEdit.text() != "" and self.ui.mergeModList.count() <= 1:
            self.logMessage("Less than 2 mods found. Unable to merge anything.", Color.WARNING)
        

    def browseMergeDir(self):
        """
        Open a file dialog to select the folder contianing mods to be merged.

        Update mergeDirLineEdit with the chosen directory path and update
        mod directories using populateMergeList().
        """
        options = QFileDialog.Options(QFileDialog.ShowDirsOnly)   # Only show directories
        directory = QFileDialog.getExistingDirectory(self, "Select folder containing mods to merge", options=options)

        # Display selected directory in QLabel
        if directory:
            self.ui.mergeDirLineEdit.setText(directory)
            self.ui.mergeDirLineEdit.setToolTip(directory)
            self.populateMergeList()
    

    def toggleWidget(self, widgets=[], enableWidget=None):
        """
        Toggle the enabled state of the specified widgets passed in.

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
        Enable/Disable every directory within source_list by adding/removing the "DISABLED" prefix as necessary.

        Parameters:
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
        self.toggleWidget([self.ui.addModButton, self.ui.removeModButton]) # Disable buttons while mods are being enabled/disabled
        for item in selected_items:
            item_name = item.text()
            mod_dir = findModDirectory(item_name)
            prefix = "DISABLED"

            if not mod_dir:
                self.logMessage(f"Error: Could not find directory for {item_name}. Please [ Refresh Mod List ]", Color.ERROR)
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

                # User manually renamed file to use "DISABLED" and did not refresh the mod list.
                if new_item_name != os.path.basename(dest_path):
                    self.logMessage("Detected issue with directory name. Please [Refresh Mod List]", Color.WARNING)

                # Create a new QListWidgetItem with updated text and tooltip
                new_item = QListWidgetItem(new_item_name)
                new_item.setToolTip(os.path.normpath(dest_path))
                target_list.addItem(new_item)

            except Exception as e:
                self.logMessage(f"Error: {e}", Color.ERROR)
        self.toggleWidget([self.ui.addModButton, self.ui.removeModButton]) # Enable buttons once more after mods have been enabled/disabled


    def updatePreview(self, mod_status=""):
        """
        Update the mod name label and image preview based on the current selection.
        """
        # Determine the selected list based on mod_status
        if mod_status == "Enabled": 
            selected_list = self.ui.enabledModList
        elif mod_status == "Disabled":
            selected_list = self.ui.disabledModList
        else:
            selected_list = self.ui.mergeModList

        if selected_list:
            selected_item = selected_list.currentItem()
            if selected_item:
                mod_name = selected_item.text()
                mod_directory = findModDirectory(mod_name)
                self.ui.previewModLabel.setText(mod_name)
                
                # Load images from the mod directory
                self.carousel_images = [] # Empty existing carousel_images
                for root, dirs, files in os.walk(mod_directory):
                    for file in files:
                        if(file.lower().endswith(('.png', '.jpg'))):
                            self.carousel_images.append(os.path.join(root, file))
                self.toggleWidget([self.ui.previewModBackButton, self.ui.previewModNextButton], len(self.carousel_images) > 1) # Enable carousel if more than 1 image, else disable
                self.carousel_idx = 0
                self.displayCurrentImage()  # Display the first image in the carousel
            else:
                # Handle case where no item is selected in the list
                self.ui.previewModLabel.setText("")
                scene = QGraphicsScene()
                self.ui.previewModImage.setScene(scene)
        else:
            # Handle unknown mod_status
            self.ui.previewModLabel.setText("")
            scene = QGraphicsScene()
            self.ui.previewModImage.setScene(scene)


    def displayCurrentImage(self):
        """Display the current image in the carousel."""
        scene = QGraphicsScene()
        if self.carousel_images:
            image_path = self.carousel_images[self.carousel_idx]
            pixmap = QPixmap(image_path)
            
            if pixmap.isNull():
                placeholder_text = QGraphicsTextItem("[ Image Load Failed ]")
                placeholder_text.setFont(QFont("Arial", 12))
                scene.addItem(placeholder_text)
            else:
                # Get the dimensions of the QGraphicsView
                view_width = self.ui.previewModImage.viewport().width()
                view_height = self.ui.previewModImage.viewport().height()
                # Scale the pixmap
                scaled_pixmap = pixmap.scaled(view_width, view_height, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                # Calculate cropping area
                x_offset = (scaled_pixmap.width() - view_width) / 2
                y_offset = (scaled_pixmap.height() - view_height) / 2
                cropped_pixmap = scaled_pixmap.copy(x_offset, y_offset, view_width, view_height)

                pixmap_item = QGraphicsPixmapItem(cropped_pixmap)
                scene.addItem(pixmap_item)
        else:
            placeholder_text = QGraphicsTextItem()
            placeholder_text = QGraphicsTextItem("[ No Preview ]")
            placeholder_text.setFont(QFont("Arial", 12))
            scene.addItem(placeholder_text)
        
        # Set the scene for previewModImage QGraphicsView
        self.ui.previewModImage.setScene(scene)
        self.ui.previewMergeImage.setScene(scene)


    def showNextImage(self):
        """Show the next image in the carousel."""
        if self.carousel_images:
            self.carousel_idx = (self.carousel_idx + 1) % len(self.carousel_images)
            self.displayCurrentImage()


    def showPrevImage(self):
        """Show the previous image in the carousel."""
        if self.carousel_images:
            self.carousel_idx = (self.carousel_idx - 1) % len(self.carousel_images)
            self.displayCurrentImage()


    def runScript(self, script_path, target_directory, args=[], input_data="\n"):
        """
        Runs a given script (either .py or .exe) on the specified directory.

        Parameters:
        script_path (str): The path to the script file to be executed.
        target_directory (str): The directory on which the script should operate.
        args: (str): an array of flags and values to pass with the script's command
        input_data (str, optional): Any key presses necessary to run the specified script
        """
        original_cwd = os.getcwd()  # Save current working directory

        try:
            # Validate script_path and target_directory
            if not os.path.isfile(script_path):
                raise ValueError(f"Script path {os.path.normpath(script_path)} does not point to a valid file.")

            if not os.path.isdir(target_directory):
                raise ValueError(f"Target directory {os.path.normpath(target_directory)} does not point to a valid directory.")
            
            # Change current working directory to target_directory
            os.chdir(target_directory)

            if script_path.endswith('.py'):
                # Use Popen to interact with subprocess
                proc = subprocess.Popen(["python", script_path, *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            elif script_path.endswith('.exe'):
                proc = subprocess.Popen([script_path, *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            else:
                raise ValueError("Script must be either a .py or .exe file.")
            
            # Optionally, you can send input to the subprocess
            # Here we simulate sending an 'enter' key press
            input_data = "\n"
            stdout, stderr = proc.communicate(input=input_data)
            print(f"stdout {stdout}\t\t stderr {stderr}")
            # proc.communicate(input='\n')

            # Optionally, you can wait for the subprocess to finish
            proc.wait()

            # Check the result
            if proc.returncode == 0:
                self.logMessage(f"Script executed successfully!\n", Color.SUCCESS)
            else:
                self.logMessage(f"Script returned error code {proc.returncode}.", Color.ERROR)

        except Exception as e:
            self.logMessage(f"Error: {e}")
        finally:
            # Restore original working directory
            os.chdir(original_cwd)


    def runPatch(self):
        """
        Runs the Patch script. Logs messages as necessary using logMessage().
        """
        try:
            patch_script = getScript(os.path.join(os.getcwd(), "Scripts"),"PATCH")
            target_dir = os.path.join(os.getcwd(), "Mods")

            self.logMessage("Running [PATCH] script")
            self.runScript(patch_script, target_dir, [], "\n")
        except Exception as e:
            self.logMessage(f"Error: {e}", Color.ERROR)


    def getMergeFlags(self):
        """
        Determines and compiles flags to use based on values set in the application.

        Returns a dictionary containing all relevant flags.
        """
        # Flags that take args
        kFlagVal = self.ui.swapKeyLineEdit.text()              # --key
        nFlagVal = (self.ui.mergeNameLineEdit.text() if self.ui.mergeNameLineEdit.text() != "" else "merged") + ".ini"    # --name
        rFlagVal = self.ui.mergeDirLineEdit.text() if self.ui.mergeDirLineEdit.text() != "" else "."                      # --root

        # Flags dont take args
        aFlag = self.ui.activeFlagCheckBox.isChecked()         # --active
        cFlag = self.ui.compressFlagCheckBox.isChecked()       # --compress
        eFlag = self.ui.enabledFlagCheckBox.isChecked()        # --enable
        sFlag = self.ui.storeFlagCheckBox.isChecked()          # --store
        refFlag = self.ui.reflectionFlagCheckBox.isChecked()   # --reflection DEPRECATED

        result = {
               "key": ["-k", kFlagVal],
              "name": ["-n", nFlagVal],
              "root": ["-r", rFlagVal],
        }

        if aFlag: result["active"] = ["-a"]
        if cFlag: result["compress"] = ["-c"]
        if eFlag: result["enable"] = ["-e"]
        if sFlag: result["store"] = ["-s"]
        if refFlag: result["reflection"] = ["-ref"] # DEPRECATED

        # Save the last attempted key and name
        self.saveSetting({"key": kFlagVal, "name": nFlagVal[:-4]})
        
        return result


    def getModOrder(self, path, ignore):
        base_dict = {}  # Dictionary holding base assumed order
        new_order = []  # List taking assumed order user desires
        
        for root, dir, files in os.walk(path):
            if "disabled" in root.lower():
                continue
            for file in files:
                if "disabled" in file.lower() or ignore.lower() in file.lower():
                    continue
                if os.path.splitext(file)[1] == ".ini":
                    base_dict[os.path.basename(root)] = len(base_dict)  # mod_name: idx
        
        for index in range(self.ui.mergeModList.count()):
            new_order.append( base_dict[self.ui.mergeModList.item(index).text()] )

        print(f"base_dict: {base_dict}")
        print(f"\nnew : {new_order}\n")
        return new_order


    def runMerge(self):
        """
        Runs the Merge script. Logs messages as necessary using logMessage().
        """
        try:
            merge_script = getScript(os.path.join(os.getcwd(), "Scripts", "Merge"),"MERGE")
        except Exception as e:
            self.logMessage(f"Error: {e}", Color.ERROR)
            return
        
        # Gather selected flags & target directory
        flags = self.getMergeFlags()
        target_dir = flags["root"][1]

        if not os.path.exists(target_dir):
            self.logMessage(f"Merge directory may have been renamed or removed: {target_dir}", Color.ERROR)
            return

        # Enable flag ignores all other flags
        if "enable" in flags:
            self.logMessage(f"Enable flag detected. Will <u><i>NOT<i/></u> merge mods. Will only re-enable .ini files and mod directories", Color.WARNING)

            # Enable any disabled directories
            for root, dirs, files in os.walk(target_dir):
                for dir in dirs:
                    if dir.upper().startswith("DISABLED"):
                        old_name = os.path.normpath( os.path.join(root, dir) )
                        new_name = old_name[:-len(dir)] + dir[len("DISABLED"):]
                        os.rename(old_name, new_name)
                        self.logMessage(f"Enabled mod folder for mod: {os.path.basename(new_name)}")

            # Enable .ini files via the merge script
            use_flags = [*flags["root"], *flags["enable"]]

            self.logMessage("Running [MERGE] script")
            self.runScript(merge_script, target_dir, use_flags, "")
        else:
            use_flags = [item for sublist in flags.values() for item in sublist]
            mod_order = self.getModOrder(flags["root"][1], flags["name"][1])
            input_data = "\n"+ " ".join(map(str, mod_order)) + "\n"
            
            self.logMessage("Running [MERGE] script")
            self.runScript(merge_script, target_dir, use_flags, input_data)
    

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
        self.ui.logTextEdit.append(log_entry)

    
    def setIconGraphicsView(self):
        """
        Set the logo image in the QGraphicsView.
        If a user-provided image is not found, display the default LogoImg.ico.
        """
        scene = QGraphicsScene()

        # Try to load user-provided image
        image_path = findLogoImg()
        user_pixmap = QPixmap(image_path)

        # Use user-provided image if it exists, otherwise use the embedded default image
        if not user_pixmap.isNull():
            pixmap = user_pixmap
        else:
            pixmap = QPixmap(":/LogoImg")

        # Get the dimensions of the QGraphicsView
        view_width = self.ui.IconGraphicsView.viewport().width()
        view_height = self.ui.IconGraphicsView.viewport().height()

        # Scale the pixmap
        scaled_pixmap = pixmap.scaled(view_width, view_height, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        # Calculate cropping area
        x_offset = (scaled_pixmap.width() - view_width) / 2
        y_offset = (scaled_pixmap.height() - view_height) / 2
        cropped_pixmap = scaled_pixmap.copy(x_offset, y_offset, view_width, view_height)

        # Add the pixmap to the scene
        pixmap_item = QGraphicsPixmapItem(cropped_pixmap)
        scene.addItem(pixmap_item)

        self.ui.IconGraphicsView.setScene(scene)
        self.setWindowIcon(QIcon(":/LogoImg"))


'''
=========================================================
Class agnostic helpers
These helper methods can be used independently of Main
and are meant to improve code legibility or consistency.
=========================================================
'''

def findLogoImg():
    """
    On the top level of the cwd, find and return the Logo image.
    
    Returns:
        The path to the image. If no image is found, return an empty string
    """
    for root, dirs, files in os.walk(os.getcwd()):
        for file in files:
            if file.startswith("LogoImg.") and file.lower().endswith((".png", ".jpg")):
                return os.path.join(root, file)
        return "" # Not found on top level

def findModDirectory(mod_name):
    """
    Find the directory containing the mod.

    Args:
        mod_name (str): The name of the mod to find.

    Returns:
        str: The full path to the directory containing the mod, or None if not found.
    """
    modding_dir = os.path.join(os.getcwd(), "Mods")
    for root, dirs, files in os.walk(modding_dir):
        for name in dirs:
            if name == mod_name or name == f"DISABLED{mod_name}":
                return os.path.join(root, name)
    return ""

def getScript(path, script_type="SCRIPT"):
    """
    Attempt to find a .py or .exe script at the top-most level of a path.

    Parameters:
    path (str): The path to check for scripts
    script_type (str, optional): The type of script it is. Ex: MERGE
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing folder(s): {os.path.normpath(path)}")
    
    for _, _, files in os.walk(path):
        for file in files:
            if isExeOrPy(file):
                return os.path.normpath(os.path.join(path, file))
        # No valid file found    
        raise FileNotFoundError(f"No valid [{script_type}] file found. Please ensure you have a valid [{script_type}] file in {os.path.normpath(path)}")

def isExeOrPy(path):
    """
    Checks if a path ends at a .exe or .py file. Case insensetive.

    Args:
        path (str): A path to a resource
    Returns:
        bool: True if path is a ".exe" or ".py" file. False if not.
    """
    return path.lower().endswith((".exe", ".py"))

def getMainStyles():
    styles = """
    QPushButton {
        color: black;
        background-color: #C7E5C9; /* Green background */
        border-radius: 5px;
        border: 1px solid black;
    }

    QPushButton:hover {
        color: black;
        background-color: #A4CFA5; /* Darker green background on hover */
    }

    QPushButton:disabled {
        background-color: #E5E5E5; /* Light grey background for disabled state */
        border: 1px solid #BBBBBB; /* Light grey border for disabled state */
        color: #999999; /* Light grey text for disabled state */
    }

    QListWidget {
        border: 1px solid #AAAAAA;
        padding: 1px;
        border-radius: 5px;
    }

    #previewMergeNextButton, #previewMergeBackButton, #previewModNextButton, #previewModBackButton{
        border: 1px solid #C0C0C0;
        background-color: rgba(255, 255, 255, 0.3)
    }
    #previewMergeNextButton:hover, #previewMergeBackButton:hover, #previewModNextButton:hover, #previewModBackButton:hover{
        border: 1px solid #AAAAAA;
        background-color: rgba(255, 255, 255, 0.75)
    }

    QListWidget::item {
        color: black;
        padding: 2px;
        margin: 2px; 
        border: 1px solid rgba(0,0,0,0.2);
    }
    QListWidget::item:selected{
        background-color: rgba(0,0,0, 0.15);
        color: black;
    }

    QScrollBar::handle:vertical {
        color: black;
        background: lightgray; 
        border: 1px solid gray;
    }
                           """
    return styles

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Main()
    
    window.show()
    app.exec_()
