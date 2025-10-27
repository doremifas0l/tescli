
import sys
import json
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QTableView
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import QThread, pyqtSignal

from ai import configure_ai, process_transaction_text, get_category_suggestion
from database import create_table, add_transaction, get_transactions

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
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_transactions)

        layout.addWidget(self.transaction_view)
        layout.addWidget(self.refresh_button)
        self.transactions_tab.setLayout(layout)

        self.model = QStandardItemModel()
        self.transaction_view.setModel(self.model)
        self.load_transactions()

    def load_transactions(self):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["ID", "Description", "Amount", "Type", "Category", "Date"])
        transactions = get_transactions()
        for transaction in transactions:
            row = []
            for item in transaction:
                row.append(QStandardItem(str(item)))
            self.model.appendRow(row)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
