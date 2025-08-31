import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,  # type: ignore
                             QHBoxLayout, QPushButton, QLabel, QListWidget, 
                             QLineEdit, QFileDialog, QStackedWidget, QMessageBox,
                             QShortcut, QListWidgetItem, QProgressBar) 
from PyQt5.QtCore import Qt, QSize # type: ignore
from PyQt5.QtGui import QPixmap, QKeySequence, QFont # type: ignore
import pandas as pd # type: ignore

class ImageClassifierApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Label Flow")
        self.setGeometry(100, 100, 800, 600)
        
        self.image_paths = []
        self.labels = {} 
        self.classifications = [] 
        self.current_image_index = 0
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.screen1 = FolderSelectionScreen()
        self.screen2 = LabelCreationScreen()
        self.screen3 = ImageClassificationScreen()
        self.screen4 = ExportResultsScreen()
        
        self.stacked_widget.addWidget(self.screen1)
        self.stacked_widget.addWidget(self.screen2)
        self.stacked_widget.addWidget(self.screen3)
        self.stacked_widget.addWidget(self.screen4)
        
        self.screen1.next_button.clicked.connect(self.go_to_screen2)
        self.screen2.next_button.clicked.connect(self.go_to_screen3)
        self.screen2.back_button.clicked.connect(self.go_to_screen1)
        self.screen3.next_button.clicked.connect(self.go_to_screen4)
        self.screen3.back_button.clicked.connect(self.go_to_screen2)
        self.screen4.back_button.clicked.connect(self.go_to_screen3)
        self.screen4.export_button.clicked.connect(self.export_results)
        
        self.screen2.add_button.clicked.connect(self.add_label)
        self.screen2.remove_button.clicked.connect(self.remove_label)
        
        self.stacked_widget.setCurrentIndex(0)
    
    def go_to_screen1(self):
        self.stacked_widget.setCurrentIndex(0)
    
    def go_to_screen2(self):
        folder_path = self.screen1.folder_path.text()
        
        if not folder_path:
            QMessageBox.warning(self, "Warning", "Please select a folder first.")
            return
        
        self.image_paths = self.load_image_paths(folder_path)
        
        if not self.image_paths:
            QMessageBox.warning(self, "Warning", "No images found in the selected folder.")
            return
        
        self.stacked_widget.setCurrentIndex(1)
    
    def go_to_screen3(self):
        if not self.labels:
            QMessageBox.warning(self, "Warning", "Please create at least one label.")
            return
        
        self.classifications = []
        self.current_image_index = 0
        
        self.screen3.setup_classification(self, self.image_paths, self.labels)
        
        self.stacked_widget.setCurrentIndex(2)
    
    def go_to_screen4(self):
        if len(self.classifications) != len(self.image_paths):
            QMessageBox.warning(self, "Warning", "Please classify all images before proceeding.")
            return
        
        self.screen4.update_results_count(len(self.classifications))
        
        self.stacked_widget.setCurrentIndex(3)
    
    def load_image_paths(self, folder_path):
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
        image_paths = []
        
        for file in os.listdir(folder_path):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                image_paths.append(os.path.join(folder_path, file))
        
        return image_paths
    
    def add_label(self):
        label_text = self.screen2.label_input.text().strip()
        shortcut_text = self.screen2.shortcut_input.text().strip().upper()
        
        if not label_text or not shortcut_text:
            QMessageBox.warning(self, "Warning", "Please enter both label and shortcut.")
            return
        
        if len(shortcut_text) != 1:
            QMessageBox.warning(self, "Warning", "Shortcut must be a single character.")
            return
        
        if shortcut_text in self.labels:
            QMessageBox.warning(self, "Warning", "This shortcut is already in use.")
            return
        
        self.labels[shortcut_text] = label_text
        
        item_text = f"{shortcut_text}: {label_text}"
        self.screen2.labels_list.addItem(item_text)
        
        self.screen2.label_input.clear()
        self.screen2.shortcut_input.clear()
    
    def remove_label(self):
        current_row = self.screen2.labels_list.currentRow()
        if current_row >= 0:
            item = self.screen2.labels_list.takeItem(current_row)
            shortcut = item.text().split(":")[0].strip()
            del self.labels[shortcut]
    
    def export_results(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel File", "", "Excel Files (*.xlsx)"
        )
        
        if file_path:
            try:
                df = pd.DataFrame(self.classifications, columns=['image_path', 'label'])
                
                df.to_excel(file_path, index=False)
                
                QMessageBox.information(self, "Success", f"Results exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export results: {str(e)}")


class FolderSelectionScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        title = QLabel("Select Image Folder")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        instructions = QLabel(
            "This application will help you classify images for training machine learning models.\n\n"
            "Please select a folder containing the images you want to classify."
        )
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        folder_layout = QHBoxLayout()
        self.folder_path = QLineEdit()
        self.folder_path.setReadOnly(True)
        folder_layout.addWidget(self.folder_path)
        
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_folder)
        folder_layout.addWidget(browse_button)
        
        layout.addLayout(folder_layout)
        
        self.next_button = QPushButton("Next →")
        self.next_button.setFixedHeight(40)
        layout.addWidget(self.next_button)
        
        self.setLayout(layout)
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder:
            self.folder_path.setText(folder)


class LabelCreationScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        title = QLabel("Create Classification Labels")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        instructions = QLabel(
            "Create labels for classification and assign keyboard shortcuts to them.\n\n"
            "For example, create a label 'cat' and assign the shortcut 'C' to it."
        )
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        input_layout = QHBoxLayout()
        
        label_input_layout = QVBoxLayout()
        label_input_layout.addWidget(QLabel("Label Name:"))
        self.label_input = QLineEdit()
        label_input_layout.addWidget(self.label_input)
        
        shortcut_input_layout = QVBoxLayout()
        shortcut_input_layout.addWidget(QLabel("Keyboard Shortcut:"))
        self.shortcut_input = QLineEdit()
        self.shortcut_input.setMaxLength(1)
        shortcut_input_layout.addWidget(self.shortcut_input)
        
        input_layout.addLayout(label_input_layout)
        input_layout.addLayout(shortcut_input_layout)
        
        button_layout = QVBoxLayout()
        button_layout.addWidget(QLabel(" ")) 
        self.add_button = QPushButton("Add Label")
        button_layout.addWidget(self.add_button)
        
        input_layout.addLayout(button_layout)
        layout.addLayout(input_layout)
        
        layout.addWidget(QLabel("Current Labels:"))
        self.labels_list = QListWidget()
        layout.addWidget(self.labels_list)
        
        self.remove_button = QPushButton("Remove Selected Label")
        layout.addWidget(self.remove_button)
        
        nav_layout = QHBoxLayout()
        self.back_button = QPushButton("← Back")
        self.next_button = QPushButton("Next →")
        nav_layout.addWidget(self.back_button)
        nav_layout.addWidget(self.next_button)
        layout.addLayout(nav_layout)
        
        self.setLayout(layout)


class ImageClassificationScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.shortcuts = {}
    
    def initUI(self):
        layout = QVBoxLayout()
        
        title = QLabel("Classify Images")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.progress_label = QLabel("Image 0 of 0")
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet("border: 1px solid gray;")
        layout.addWidget(self.image_label)
        
        instructions = QLabel("Press the assigned keyboard shortcut to classify the current image.")
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)
        
        self.shortcuts_label = QLabel()
        self.shortcuts_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.shortcuts_label)
        
        nav_layout = QHBoxLayout()
        self.back_button = QPushButton("← Back")
        self.next_button = QPushButton("Next →")
        nav_layout.addWidget(self.back_button)
        nav_layout.addWidget(self.next_button)
        layout.addLayout(nav_layout)
        
        self.setLayout(layout)
    
    def setup_classification(self, main_window, image_paths, labels):
        self.main_window = main_window  
        self.image_paths = image_paths
        self.labels = labels
        self.current_index = 0
        
        self.update_progress()
        
        self.display_current_image()
        
        self.create_shortcuts()
        
        self.update_shortcuts_label()
    
    def update_progress(self):
        total = len(self.image_paths)
        self.progress_label.setText(f"Image {self.current_index + 1} of {total}")
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(self.current_index)
    
    def display_current_image(self):
        if self.current_index < len(self.image_paths):
            pixmap = QPixmap(self.image_paths[self.current_index])
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    self.image_label.width() - 20, 
                    self.image_label.height() - 20,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(pixmap)
            else:
                self.image_label.setText("Unable to load image")
        else:
            self.image_label.setText("No more images to classify")
    
    def create_shortcuts(self):
        for shortcut in self.shortcuts.values():
            shortcut.deleteLater()
        self.shortcuts = {}
        
        for key in self.labels.keys():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(lambda k=key: self.classify_image(k))
            self.shortcuts[key] = shortcut
    
    def update_shortcuts_label(self):
        text = "Shortcuts: "
        for key, label in self.labels.items():
            text += f"{key}={label}   "
        self.shortcuts_label.setText(text)
    
    def classify_image(self, key):
        if self.current_index < len(self.image_paths):
            self.main_window.classifications.append((self.image_paths[self.current_index], self.labels[key]))
            
            self.current_index += 1
            self.update_progress()
            
            if self.current_index < len(self.image_paths):
                self.display_current_image()
            else:
                self.image_label.setText("All images classified!")
                self.shortcuts_label.setText("All images classified. Click 'Next' to continue.")


class ExportResultsScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        title = QLabel("Export Results")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.results_label = QLabel("0 images classified")
        self.results_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.results_label)
        
        instructions = QLabel(
            "Click the button below to export your classification results to an Excel file.\n\n"
            "The Excel file will contain two columns: 'image_path' and 'label'."
        )
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        self.export_button = QPushButton("Export to Excel")
        self.export_button.setFixedHeight(40)
        layout.addWidget(self.export_button)
        
        self.back_button = QPushButton("← Back")
        layout.addWidget(self.back_button)
        
        self.setLayout(layout)
    
    def update_results_count(self, count):
        self.results_label.setText(f"{count} images classified")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageClassifierApp()
    window.show()
    sys.exit(app.exec_())