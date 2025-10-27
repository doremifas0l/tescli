import json
from ai import configure_ai, process_transaction_text, get_category_suggestion

# It's not recommended to hardcode the API key like this in a real application.
# It's better to use environment variables or other secure methods.
API_KEY = "AIzaSyDugWKcAZkzrNDrLfJlG9T-v04TL1sEWig"

if __name__ == "__main__":
    configure_ai(API_KEY)

    # Test transaction processing
    transaction_text = "jajan 15rb"
    processed_text = process_transaction_text(transaction_text)
    # Clean the response to be a valid JSON
    cleaned_text = processed_text.strip().replace('\n', '').replace('```json', '').replace('```', '')
    transaction_data = json.loads(cleaned_text)
    print(f"Processed Transaction: {transaction_data}")

    # Test category suggestion
    description = transaction_data["description"]
    category_suggestion = get_category_suggestion(description)
    print(f"Category Suggestion: {category_suggestion}")