import unittest
from cmd_bot import ask_chatgpt  # Import your function

class TestChatGPTFunction(unittest.TestCase):
    def test_ask_chatgpt(self):
        response = ask_chatgpt("What is AI?")
        self.assertIsInstance(response, str)  # Ensure output is a string
        self.assertGreater(len(response), 5)  # Response should not be empty
    
    def test_empty_query(self):
        response = ask_chatgpt("")
        self.assertIn("⚠️", response)  # Should return an error or warning

if __name__ == "__main__":
    unittest.main()
