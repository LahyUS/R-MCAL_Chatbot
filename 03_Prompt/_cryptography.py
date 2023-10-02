from fernet import Fernet

class CRYPTOGRAPHY:
    def __init__(self, key_path):
        with open(key_path, 'rb') as key_file:
            self.encryption_key = key_file.read()
            self.fernet = Fernet(self.encryption_key)

    def encode_text(self, text):
        return self.fernet.encrypt(text.encode()).decode()
    
    def encode_array(self, content_array):
        ecrypted_content = []
        for content in content_array:
            ecrypted_content.append(self.fernet.encrypt(content.encode()).decode())
        return ecrypted_content

    def decode_text(self, encoded_text):
        return self.fernet.decrypt(encoded_text.encode()).decode()
