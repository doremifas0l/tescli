
import google.generativeai as genai

def configure_ai(api_key):
    genai.configure(api_key=api_key)

def process_transaction_text(text):
    model = genai.GenerativeModel('gemini-flash-latest')
    prompt = f"""
    You are a personal finance assistant. Your task is to extract transaction details from a given text.
    The text is: "{text}"
    Extract the description, amount, and type (expense or income) of the transaction.
    The amount should be in numbers.
    The type should be either "expense" or "income".
    Return the result in a JSON format with the keys "description", "amount", and "type".
    For example, if the text is "beli kopi 25rb", the output should be:
    {{"description": "beli kopi", "amount": 25000, "type": "expense"}}
    """
    response = model.generate_content(prompt)
    return response.text

def get_category_suggestion(description):
    model = genai.GenerativeModel('gemini-flash-latest')
    prompt = f"""
    You are a personal finance assistant. Your task is to suggest a category for a given transaction description.
    The transaction description is: "{description}"
    Suggest a suitable category for this transaction. The category should be a single word.
    For example, if the description is "beli kopi", a good category would be "food".
    Return the category as a single word.
    """
    response = model.generate_content(prompt)
    return response.text
