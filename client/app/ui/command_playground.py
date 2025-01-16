from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
                           QPushButton, QComboBox, QLabel, QSplitter,
                           QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class CommandPlayground(QDialog):
    execute_command = pyqtSignal(str)
    save_macro = pyqtSignal(dict)

    def __init__(self, macro_manager, parent=None):
        super().__init__(parent)
        self.macro_manager = macro_manager
        self.command_history = []
        
        self.setWindowTitle("Command Playground")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Command input and execution
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Command input
        self.command_input = QTextEdit()
        self.command_input.setPlaceholderText("Enter command here...")
        left_layout.addWidget(QLabel("Command Input:"))
        left_layout.addWidget(self.command_input)
        
        # Command type selector
        self.command_type = QComboBox()
        self.command_type.addItems(["Direct", "Template", "Macro"])
        left_layout.addWidget(self.command_type)
        
        # Execute button
        execute_btn = QPushButton("Execute")
        execute_btn.clicked.connect(self.execute)
        left_layout.addWidget(execute_btn)
        
        # Save as macro button
        save_macro_btn = QPushButton("Save as Macro")
        save_macro_btn.clicked.connect(self.save_as_macro)
        left_layout.addWidget(save_macro_btn)
        
        splitter.addWidget(left_widget)
        
        # Right side - Results and history
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Results tree
        right_layout.addWidget(QLabel("Execution Results:"))
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["Time", "Type", "Result"])
        self.results_tree.setAlternatingRowColors(True)
        right_layout.addWidget(self.results_tree)
        
        splitter.addWidget(right_widget)
        
        layout.addWidget(splitter)
        
        # Set splitter sizes
        splitter.setSizes([400, 400])

    def execute(self):
        command = self.command_input.toPlainText().strip()
        if not command:
            return
        
        command_type = self.command_type.currentText()
        self.execute_command.emit(json.dumps({
            "command": command,
            "type": command_type.lower()
        }))

    def add_result(self, result: dict):
        try:
            item = QTreeWidgetItem()
            item.setText(0, datetime.now().strftime("%H:%M:%S"))
            item.setText(1, result.get("type", "unknown"))
            
            # Format result based on type
            if isinstance(result.get("result"), dict):
                item.setText(2, json.dumps(result["result"], indent=2))
            else:
                item.setText(2, str(result.get("result", "")))
            
            self.results_tree.insertTopLevelItem(0, item)
            self.command_history.append({
                "command": self.command_input.toPlainText(),
                "type": self.command_type.currentText(),
                "result": result
            })
            
        except Exception as e:
            logger.error(f"Failed to add result: {str(e)}")

    def save_as_macro(self):
        try:
            if not self.command_history:
                return
                
            from .macro_editor import MacroEditorDialog
            editor = MacroEditorDialog(self.command_history, self)
            if editor.exec_():
                macro_data = editor.get_macro_data()
                self.save_macro.emit(macro_data)
                
        except Exception as e:
            logger.error(f"Failed to save macro: {str(e)}")
