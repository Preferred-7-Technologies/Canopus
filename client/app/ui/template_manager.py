from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                           QPushButton, QFormLayout, QLineEdit, QTextEdit,
                           QMessageBox, QInputDialog)
from PyQt5.QtCore import Qt
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TemplateManagerDialog(QDialog):
    def __init__(self, template_manager, parent=None):
        super().__init__(parent)
        self.template_manager = template_manager
        self.setWindowTitle("Template Manager")
        self.setMinimumSize(600, 400)
        
        layout = QHBoxLayout(self)
        
        # Template list
        list_layout = QVBoxLayout()
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self.load_template)
        list_layout.addWidget(self.template_list)
        
        # Template list buttons
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_template)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_template)
        button_layout.addWidget(add_btn)
        button_layout.addWidget(delete_btn)
        list_layout.addLayout(button_layout)
        
        layout.addLayout(list_layout)
        
        # Template editor
        editor_layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.category_edit = QLineEdit()
        self.patterns_edit = QTextEdit()
        self.response_edit = QTextEdit()
        self.confidence_edit = QLineEdit()
        self.confidence_edit.setPlaceholderText("0.75")
        
        form_layout.addRow("Name:", self.name_edit)
        form_layout.addRow("Category:", self.category_edit)
        form_layout.addRow("Patterns (one per line):", self.patterns_edit)
        form_layout.addRow("Response Template:", self.response_edit)
        form_layout.addRow("Min Confidence:", self.confidence_edit)
        
        editor_layout.addLayout(form_layout)
        
        # Save button
        save_btn = QPushButton("Save Template")
        save_btn.clicked.connect(self.save_template)
        editor_layout.addWidget(save_btn)
        
        layout.addLayout(editor_layout)
        
        self.refresh_template_list()

    def refresh_template_list(self):
        self.template_list.clear()
        for name in self.template_manager.templates.keys():
            self.template_list.addItem(name)

    def load_template(self, current, previous):
        if not current:
            return
            
        template = self.template_manager.templates.get(current.text())
        if template:
            self.name_edit.setText(template.name)
            self.category_edit.setText(template.category)
            self.patterns_edit.setPlainText("\n".join(template.patterns))
            self.response_edit.setPlainText(template.response_template)
            self.confidence_edit.setText(str(template.min_confidence))

    def save_template(self):
        try:
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Error", "Template name is required")
                return

            template_data = {
                "name": name,
                "category": self.category_edit.text().strip(),
                "patterns": [p for p in self.patterns_edit.toPlainText().split("\n") if p],
                "response_template": self.response_edit.toPlainText().strip(),
                "variables": {},  # Updated when patterns are processed
                "min_confidence": float(self.confidence_edit.text() or 0.75)
            }

            template_dir = Path("data/templates")
            template_dir.mkdir(exist_ok=True)
            
            with open(template_dir / f"{name}.json", "w") as f:
                json.dump(template_data, f, indent=2)
            
            self.template_manager._load_templates()
            self.refresh_template_list()
            
            QMessageBox.information(self, "Success", "Template saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save template: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save template: {str(e)}")

    def add_template(self):
        name, ok = QInputDialog.getText(self, "New Template", "Template name:")
        if ok and name:
            self.name_edit.setText(name)
            self.category_edit.clear()
            self.patterns_edit.clear()
            self.response_edit.clear()
            self.confidence_edit.setText("0.75")

    def delete_template(self):
        current = self.template_list.currentItem()
        if not current:
            return
            
        if QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete template {current.text()}?"
        ) == QMessageBox.Yes:
            try:
                template_file = Path(f"data/templates/{current.text()}.json")
                if template_file.exists():
                    template_file.unlink()
                
                self.template_manager._load_templates()
                self.refresh_template_list()
                
            except Exception as e:
                logger.error(f"Failed to delete template: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to delete template: {str(e)}")
