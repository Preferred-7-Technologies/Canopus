from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget,
                           QTreeWidgetItem, QPushButton, QComboBox, QLabel,
                           QMessageBox)
from PyQt5.QtCore import Qt
import logging
from typing import Dict
import json

logger = logging.getLogger(__name__)

class TemplateBrowser(QDialog):
    def __init__(self, template_sharing, parent=None):
        super().__init__(parent)
        self.template_sharing = template_sharing
        
        self.setWindowTitle("Template Browser")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Category filter
        filter_layout = QHBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All", "General", "System", "Media", "Custom"])
        self.category_combo.currentTextChanged.connect(self.refresh_templates)
        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addWidget(self.category_combo)
        layout.addLayout(filter_layout)
        
        # Template tree
        self.template_tree = QTreeWidget()
        self.template_tree.setHeaderLabels([
            "Name", "Author", "Rating", "Downloads"
        ])
        self.template_tree.setAlternatingRowColors(True)
        layout.addWidget(self.template_tree)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_templates)
        
        import_btn = QPushButton("Import Selected")
        import_btn.clicked.connect(self.import_selected)
        
        share_btn = QPushButton("Share Template")
        share_btn.clicked.connect(self.share_template)
        
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(import_btn)
        button_layout.addWidget(share_btn)
        layout.addLayout(button_layout)
        
        # Initial load
        self.refresh_templates()

    async def refresh_templates(self):
        try:
            category = self.category_combo.currentText()
            category = category if category != "All" else None
            
            templates = await self.template_sharing.get_shared_templates(category)
            self.template_tree.clear()
            
            for template in templates:
                item = QTreeWidgetItem()
                item.setText(0, template["name"])
                item.setText(1, template["author"])
                item.setText(2, str(template.get("rating", "N/A")))
                item.setText(3, str(template.get("downloads", 0)))
                item.setData(0, Qt.UserRole, template["id"])
                self.template_tree.addTopLevelItem(item)
                
        except Exception as e:
            logger.error(f"Failed to refresh templates: {str(e)}")
            QMessageBox.warning(self, "Error", str(e))

    async def import_selected(self):
        try:
            item = self.template_tree.currentItem()
            if not item:
                return
                
            template_id = item.data(0, Qt.UserRole)
            if await self.template_sharing.import_template(template_id):
                QMessageBox.information(
                    self,
                    "Success",
                    f"Template '{item.text(0)}' imported successfully"
                )
            else:
                raise Exception("Import failed")
                
        except Exception as e:
            logger.error(f"Failed to import template: {str(e)}")
            QMessageBox.warning(self, "Error", str(e))

    async def share_template(self):
        try:
            from .template_manager import TemplateManagerDialog
            dialog = TemplateManagerDialog(None, self)
            if dialog.exec_():
                template_data = dialog.get_template_data()
                template_id = await self.template_sharing.share_template(template_data)
                QMessageBox.information(
                    self,
                    "Success",
                    f"Template shared successfully with ID: {template_id}"
                )
                await self.refresh_templates()
                
        except Exception as e:
            logger.error(f"Failed to share template: {str(e)}")
            QMessageBox.warning(self, "Error", str(e))
