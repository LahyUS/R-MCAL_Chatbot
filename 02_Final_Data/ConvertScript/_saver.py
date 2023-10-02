from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from _utils import *
from _config import CONFIG
from _loader import *
config = CONFIG()

class SAVER:
    def __init__(self, save_format, type, encode):
        self.save_format = save_format
        self.type = type
        self.encode = encode
        if self.save_format == 1:
            self.embeddings = HuggingFaceEmbeddings(model_name = config.embedding_dir)

    def save(self, docs, save_path):
        if self.save_format == 1:
            db = FAISS.from_documents(docs, self.embeddings)
            db.save_local(save_path)

        content_array = [doc.page_content for doc in docs]
        metadata_array = [doc.metadata for doc in docs]
        if config.debug:
            print('+++ Data simplifying in process:')
        simplified_content_array = list(range(len(content_array)))
        for i in tqdm(range(len(content_array))):
            simplified_content_array[i] = simplifyData(content_array[i])

        if self.save_format == 2:
            encrypt_and_save(content_array, f'{save_path}/raw_content.bin')
            encrypt_and_save(simplified_content_array, f'{save_path}/simplified_content.bin')
            encrypt_and_save(metadata_array, f'{save_path}/metadata.bin')
            return

        if self.save_format == 3:
            if self.encode:
                content_array = encode_text(content_array)
            save_TFIDF_vector(simplified_content_array, save_path)
            save_data_json(content_array, metadata_array, f'{save_path}/data.json')
            return
            

