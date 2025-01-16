from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, 
                           QTableWidgetItem, QPushButton, QHBoxLayout,
                           QHeaderView, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class HistoryViewer(QDialog):
    command_selected = pyqtSignal(dict)

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        
        self.setWindowTitle("Command History")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "Today", "Last 7 Days", "Last 30 Days", "All"
        ])
        self.period_combo.currentTextChanged.connect(self.refresh_history)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "All", "Completed", "Failed", "Pending"
        ])
        self.status_combo.currentTextChanged.connect(self.refresh_history)
        
        filter_layout.addWidget(self.period_combo)
        filter_layout.addWidget(self.status_combo)
        layout.addLayout(filter_layout)
        
        # History table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "Command", "Status", "Response"
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        layout.addWidget(self.table)
        
        # Export button
        export_btn = QPushButton("Export History")
        export_btn.clicked.connect(self.export_history)
        layout.addWidget(export_btn)
        
        self.refresh_history()

    def refresh_history(self):
        try:
            period = self.period_combo.currentText()
            status = self.status_combo.currentText()
            
            with self.db.get_session() as session:
                query = session.query(self.db.VoiceCommand)
                
                # Apply period filter
                if period == "Today":
                    query = query.filter(
                        self.db.VoiceCommand.timestamp >= datetime.now().date()
                    )
                elif period == "Last 7 Days":
                    query = query.filter(
                        self.db.VoiceCommand.timestamp >= datetime.now() - timedelta(days=7)
                    )
                elif period == "Last 30 Days":
                    query = query.filter(
                        self.db.VoiceCommand.timestamp >= datetime.now() - timedelta(days=30)
                    )
                
                # Apply status filter
                if status != "All":
                    query = query.filter(self.db.VoiceCommand.status == status.lower())
                
                commands = query.order_by(
                    self.db.VoiceCommand.timestamp.desc()
                ).all()
                
                self.populate_table(commands)
                
        except Exception as e:
            logger.error(f"Failed to refresh history: {str(e)}")

    def populate_table(self, commands):
        self.table.setRowCount(0)
        for command in commands:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(
                row, 0,
                QTableWidgetItem(command.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            )
            self.table.setItem(row, 1, QTableWidgetItem(command.command_text))
            self.table.setItem(row, 2, QTableWidgetItem(command.status))
            
            response = json.dumps(command.command_metadata, indent=2) if command.command_metadata else ""
            self.table.setItem(row, 3, QTableWidgetItem(response))

    def export_history(self):
        try:
            from pathlib import Path
            import csv
            from PyQt5.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export History",
                str(Path.home()),
                "CSV Files (*.csv)"
            )
            
            if filename:
                with open(filename, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([
                        "Timestamp", "Command", "Status", "Response"
                    ])
                    
                    for row in range(self.table.rowCount()):
                        writer.writerow([
                            self.table.item(row, col).text()
                            for col in range(self.table.columnCount())
                        ])
                logger.info(f"History exported to {filename}")
        except Exception as e:
            logger.error(f"Failed to export history: {str(e)}")
