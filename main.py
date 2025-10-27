import sys
import json
import csv
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QTableView,
    QDialog, QFormLayout, QComboBox, QDoubleSpinBox, QDialogButtonBox, QMessageBox, QFileDialog
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QAction
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QPoint

from ai import configure_ai, process_transaction_text, get_category_suggestion
from database import create_table, add_transaction, get_transactions, delete_transaction, update_transaction

# It's not recommended to hardcode the API key like this in a real application.
# It's better to use environment variables or other secure methods.
API_KEY = "AIzaSyDugWKcAZkzrNDrLfJlG9T-v04TL1sEWig"

class AIWorker(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        try:
            processed_text = process_transaction_text(self.text)
            cleaned_text = processed_text.strip().replace('\n', '').replace('```json', '').replace('```', '')
            transaction_data = json.loads(cleaned_text)
            
            if "error" not in transaction_data:
                description = transaction_data.get("description")
                if description:
                    category_suggestion = get_category_suggestion(description).strip()
                    transaction_data["category"] = category_suggestion
            
            self.finished.emit(transaction_data)
        except (json.JSONDecodeError, Exception) as e:
            self.finished.emit({"error": str(e)})

class EditTransactionDialog(QDialog):
    def __init__(self, transaction_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Transaction")
        self.transaction_data = transaction_data
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        self.description_input = QLineEdit(self.transaction_data.get("description", ""))
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, 1000000000.00)
        self.amount_input.setValue(self.transaction_data.get("amount", 0.00))
        self.type_input = QComboBox()
        self.type_input.addItems(["expense", "income"])
        self.type_input.setCurrentText(self.transaction_data.get("type", "expense"))
        self.category_input = QLineEdit(self.transaction_data.get("category", ""))

        layout.addRow("Description:", self.description_input)
        layout.addRow("Amount:", self.amount_input)
        layout.addRow("Type:", self.type_input)
        layout.addRow("Category:", self.category_input)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

        self.setLayout(layout)

    def get_edited_data(self):
        return {
            "id": self.transaction_data.get("id"),
            "description": self.description_input.text(),
            "amount": self.amount_input.value(),
            "type": self.type_input.currentText(),
            "category": self.category_input.text()
        }

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personal Finance App")

        # Configure AI
        configure_ai(API_KEY)
        # Create database table
        create_table()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.chat_tab = QWidget()
        self.transactions_tab = QWidget()

        self.tabs.addTab(self.chat_tab, "Chat")
        self.tabs.addTab(self.transactions_tab, "Transactions")

        self.setup_chat_tab()
        self.setup_transactions_tab()

    def setup_chat_tab(self):
        layout = QVBoxLayout()
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.input_field = QLineEdit()
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.process_message)

        layout.addWidget(self.chat_history)
        layout.addWidget(self.input_field)
        layout.addWidget(self.send_button)
        self.chat_tab.setLayout(layout)

    def process_message(self):
        user_message = self.input_field.text().strip()
        if not user_message:
            self.chat_history.append("Bot: Please enter a message.")
            return
            
        self.chat_history.append(f"You: {user_message}")
        self.input_field.clear()
        self.send_button.setEnabled(False)
        self.chat_history.append("Bot: is typing...")

        self.worker = AIWorker(user_message)
        self.worker.finished.connect(self.handle_ai_response)
        self.worker.start()

    def handle_ai_response(self, transaction_data):
        self.send_button.setEnabled(True)
        # Remove "Bot is typing..." message
        cursor = self.chat_history.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.movePosition(cursor.MoveOperation.StartOfLine, cursor.MoveMode.MoveAnchor)
        cursor.movePosition(cursor.MoveOperation.EndOfLine, cursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar() # remove the newline

        if "error" in transaction_data:
            if transaction_data["error"] == "not a transaction":
                self.chat_history.append("Bot: I can only process transactions. Please describe a transaction (e.g., 'bought coffee 25rb').")
            else:
                self.chat_history.append(f"Bot: Error: {transaction_data['error']}")
            return

        description = transaction_data.get("description")
        amount = transaction_data.get("amount")
        transaction_type = transaction_data.get("type")
        category = transaction_data.get("category")

        if description and amount and transaction_type:
            add_transaction(description, amount, transaction_type, category)
            self.chat_history.append(f"Bot: Added transaction: {description}, Amount: {amount}, Type: {transaction_type}, Category: {category}")
            self.load_transactions()
        else:
            self.chat_history.append("Bot: Sorry, I couldn't understand the transaction details.")

    def setup_transactions_tab(self):
        layout = QVBoxLayout()
        self.transaction_view = QTableView()
        self.transaction_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.transaction_view.customContextMenuRequested.connect(self.show_transaction_context_menu)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_transactions)

        self.export_button = QPushButton("Export to CSV")
        self.export_button.clicked.connect(self.export_transactions_to_csv)

        layout.addWidget(self.transaction_view)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.export_button)
        self.transactions_tab.setLayout(layout)

        self.model = QStandardItemModel()
        self.transaction_view.setModel(self.model)
        self.load_transactions()

    def show_transaction_context_menu(self, pos: QPoint):
        index = self.transaction_view.indexAt(pos)
        if not index.isValid():
            return

        menu = QMenu(self)

        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.edit_transaction(index.row()))
        menu.addAction(edit_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_selected_transaction(index.row()))
        menu.addAction(delete_action)

        menu.exec(self.transaction_view.viewport().mapToGlobal(pos))

    def edit_transaction(self, row):
        transaction_id = int(self.model.item(row, 0).text())
        description = self.model.item(row, 1).text()
        amount = float(self.model.item(row, 2).text())
        transaction_type = self.model.item(row, 3).text()
        category = self.model.item(row, 4).text()

        transaction_data = {
            "id": transaction_id,
            "description": description,
            "amount": amount,
            "type": transaction_type,
            "category": category
        }

        dialog = EditTransactionDialog(transaction_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            edited_data = dialog.get_edited_data()
            update_transaction(edited_data["id"], edited_data["description"], edited_data["amount"],
                               edited_data["type"], edited_data["category"])
            self.load_transactions()

    def delete_selected_transaction(self, row):
        confirm = QMessageBox.question(self, "Delete Transaction",
                                       "Are you sure you want to delete this transaction?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            transaction_id = int(self.model.item(row, 0).text())
            delete_transaction(transaction_id)
            self.load_transactions()

    def export_transactions_to_csv(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Transactions", "transactions.csv", "CSV Files (*.csv)")
        if file_name:
            try:
                with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                    csv_writer = csv.writer(csvfile)
                    # Write header
                    csv_writer.writerow(["ID", "Description", "Amount", "Type", "Category", "Date"])
                    # Write data
                    transactions = get_transactions()
                    for transaction in transactions:
                        csv_writer.writerow([transaction["id"], transaction["description"], transaction["amount"],
                                             transaction["type"], transaction["category"], str(transaction["date"])])
                QMessageBox.information(self, "Export Successful", f"Transactions exported to {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Error exporting transactions: {e}")

    def load_transactions(self):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["ID", "Description", "Amount", "Type", "Category", "Date"])
        transactions = get_transactions()
        for transaction in transactions:
            row = []
            # Extract data from sqlite3.Row object
            row_data = [transaction["id"], transaction["description"], transaction["amount"],
                        transaction["type"], transaction["category"], str(transaction["date"])]
            for item in row_data:
                row.append(QStandardItem(str(item)))
            self.model.appendRow(row)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
