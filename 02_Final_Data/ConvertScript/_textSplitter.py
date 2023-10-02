from transformers import AutoTokenizer
from langchain.docstore.document import Document
from tqdm import tqdm
from _config import CONFIG
config = CONFIG()

class MyTextSplitterr:
    def __init__(self, separator, chunk_size):
        self.separator = separator
        self.chunk_size = chunk_size
        self.tokenizer = AutoTokenizer.from_pretrained(config.tokenizer_path)

    def split_documents(self, document):
        remove_list = []
        for i in tqdm(range(len(document))):
            doc = document[i]
            # Calculates the number of tokens in the page_content
            token_length = self.tokenizer(doc.page_content, return_tensors='pt').input_ids.size(1)
            
            # If greater than the chunk_size, then this document needs to be split into smaller chunks.
            if token_length > self.chunk_size:
                # Add the document to the remove_list as it will be split
                remove_list.append(doc)
                metadata = doc.metadata
                # Split into smaller chunks using the separator.
                texts = doc.page_content.split(self.separator)
                
                start = 0
                end = 0
                # Loop to split the document into smaller chunks
                while end <= len(texts):
                    _token_length = 0
                     # Calculate the total token length of the current chunk (up to the chunk_size)
                    while _token_length <= self.chunk_size and end <= len(texts):
                        end += 1  # Increment the end index of the current chunk
                        text = ('\n*\n').join(texts[start:end]) # Join the text chunks to form the current chunk
                        _token_length = self.tokenizer(text, return_tensors='pt').input_ids.size(1)
                    
                    # Create a new Document object for the current chunk and add it to the document list
                    page_content = ('\n*\n').join(texts[start:end-1])  # Join the text chunks of the current chunk
                    _token_length = self.tokenizer(page_content, return_tensors='pt').input_ids.size(1)

                    if page_content != '':
                        if metadata['section_name'] != '' and start != 0:
                            page_content = metadata['section_name'] + '\n' + page_content
                        # Create a new Document object with the chunk's content and metadata
                        document.extend([Document(page_content=page_content, metadata=metadata)])
                    
                    # Move the start index for the next chunk
                    start = end - 1 
        # Remove the original documents that have been split from the document list       
        for item in remove_list:
            document.remove(item)

        # Return the modified document list with the large documents split into smaller chunks
        return document