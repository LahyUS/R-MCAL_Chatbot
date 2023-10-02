from abc import ABC, abstractmethod
from langchain.docstore.document import Document
from tqdm import tqdm
from _utils import *
from _config import CONFIG
import glob
from extern_variables import *
config = CONFIG()

class LOADER:
    def __init__(self, type):
        self.type = type

    def getDocumentContent(self, document_path, document_type, header, document, error_log_path):
        if self.type == 'AUTOSAR':
            convert = AUTOSAR()
        elif self.type == 'BASE':
            convert = BASE_FORMAT()
        convert.getMetadata(document_path, document_type, header)
        convert.getContent(document, error_log_path)
        subheaders = header['subheader']
        if len(subheaders) == 0:
            return
        else:
            for subheader in subheaders:
                self.getDocumentContent(document_path, document_type, subheader, document, error_log_path)

    def singleFileLoad(self, json_data, document_path, document_type, error_log_path):            
        document = []
        self.getDocumentContent(document_path, document_type, json_data, document, error_log_path)
        return document

    def multipleFilesLoad(self, json_file_paths, document_type, error_log_path):            
        docs = []
        for i in tqdm(range(len(json_file_paths))):
            with open(json_file_paths[i], 'r', encoding='utf-8') as f:
                file_content = f.read()
                f.seek(0)  # Reset the file pointer to the beginning
                try:
                    json_data = json.load(f)
                except json.JSONDecodeError as e:
                    if config.debug:
                        print('Warning: Error loading JSON file', json_file_paths[i])
                        print('Error message:', e)
                    continue

            document_path = json_file_paths[i].replace(f'{config.middle_version_path}/','').replace('.json','.pdf')
            with open(error_log_path, 'a') as file:
                file.write('\nDocument ' + os.path.basename(document_path) + ':\n')
            docs.extend(self.singleFileLoad(json_data, document_path, document_type, error_log_path))
        return docs


class BASE_FORMAT():
    def __init__(self):
        self.startParagraphPhrases = []
        self.endParagraphPhrases = []
        self.invalidStartCharacter = []
        self.specialTableNamePhrases = []
        self.splitContentChunkPatterns = ''

    def getContent(self, document, error_log_path):
        self.error_log_path = error_log_path
        content = ''
        table_of_content = ''

        # Extract contents from each paragraph in the current document scope
        for i in range(len(self.paragraphs)):
            paragraph = self.paragraphs[i]
            if paragraph != '':
                if paragraph[0] != '' and self.checkStartParagraph(paragraph[0]):
                    if(self.checkTableOfContent(paragraph[0])):
                        table_of_content += paragraph[0].split('....')[0] + '\n'
                        continue
                    
                    if(self.checkEndParagraph(paragraph[0])):
                        content += paragraph[0].rstrip(' ') + '\n'
                    else:
                        content += paragraph[0]
        
        # Get content of the table
        self.getTable()

        # Check for valid content, return if empty
        if content == '' and len(self.tables) == 0: return
        elif content == '': pass
        # If exist content, parse and update content variable
        else: content = self.section_name.rstrip(' ') + '\n' + content

        # Finds specific substrings that match the defined pattern, and modify the current table by adding {requirement_table}
        content = self.addRequirementTable(content)

        # Split content into small chunks. Each line of content would be a chunk
        content_chunks = content.split('\n')
        content_chunks = [chunk for chunk in content_chunks if chunk != '']

        # Post process each content chunk
        for i in range(len(content_chunks)):
            try:
                if i == 0: # Skip the first chunk, it's always the heading of the content 
                    pass
                
                # Check for ending of a requirement
                elif self.checkEndRequirement(content_chunks[i]) == True: 
                    content_chunks[i] = content_chunks[i] + '**'

                # Check for starting with a valid character or not
                elif self.startsWithValidCharacter(content_chunks[i]) == True and self.startsWithValidCharacter(content_chunks[i-1]) == False:
                    content_chunks[i] = '*\n' + content_chunks[i]
                
                elif self.startsWithValidCharacter(content_chunks[i]) == True and self.startsWithValidCharacter(content_chunks[i-1]) == True:
                    content_chunks[i-1] = content_chunks[i-1] + '*'
            except:
                pass

        # Re-factory the content by joining chunks of content
        content = ('\n').join(content_chunks)

        # If this is a table of content, modify the metadata, then add into the returned document
        if table_of_content != '':
            metadata = {"guideline" : self.guideline,
                        "guideline_link" : self.guideline_link,
                        "wkproduct_link" : self.wkproduct_link,
                        "path": self.document_path, 
                        "source": self.document_name, 
                        "version": self.version, 
                        "page": '',
                        "section_name": 'Table_of_content', 
                        "section_number": ''}
            document.extend([Document(page_content=table_of_content.rstrip('\n'), metadata=metadata)])

        # To separate requirements if exist, Re-factory the content chunks into sub-strings by split it by '**'.     
        content_chunks = content.split(self.splitContentChunkPatterns)

        start_table = 0
        # Handle content and store in document
        for i in range(len(content_chunks)):
            content_chunk = content_chunks[i]  

            # If there is a requirement table in the content chunk, get its content
            if '{requirement_table}' in content_chunk:
                self.getTableContent(content_chunk, start_table)  

            # Remove spaces at the beginning and at the end of the string
            if content_chunk.strip() == '':
                continue

            # Check for valid section name
            if self.section_name != '' and i != 0:
                content_chunk = self.section_name.rstrip(' ') + '\n' + content_chunk

            # Check section name and correct if needed. By removing brackets [] in section name
            self.section_name = self.adjustSectionName(self.section_name)
            document.extend([Document(page_content=content_chunk, metadata=self.metadata)])

        # Handle table in list of tables and store in document
        for i in range(len(self.tables)):
            if i < start_table:
                continue
            table = self.tables[i]
            info = table[0]
            table_name = table[1]
            table_type = table[2]

            # If this is a special table
            if self.isSpecialTable(table_name):
                for part in info:
                    # If empty, skip it
                    if not part.strip():
                        continue
                    # Collect its data content, then store in document
                    if table_name != '':
                        part = table_name + '\n' + part.rstrip('\n')
                    document.extend([Document(page_content=part.rstrip('\n'), metadata=self.metadata)])
            # Else this is a normal table, collect its data content, then store in document        
            else:
                table_content = ''
                for part in info:
                    table_content += part
                document.extend([Document(page_content=self.section_name.rstrip(' ') + '\n' + table_content, metadata=self.metadata)])

    def checkStartParagraph(self, text:str) -> bool:
        for string in self.startParagraphPhrases:
            if text.startswith(string):
                return False
        return True

    def checkTableOfContent(self, text:str) -> bool:
        if '......' in text:
            return True
        return False

    @abstractmethod
    def checkEndParagraph(self, text:str) -> bool:
        pass

    @abstractmethod
    def checkEndRequirement(self, text:str) -> bool:
        pass

    def startsWithValidCharacter(self, text:str) -> bool:
        for start in self.invalidStartCharacter: # ['-', '\u2022']
            if text.split()[0] == start:
                return False
        return True

    @abstractmethod
    def addRequirementTable(self, text:str) -> str:
        pass
    
    @abstractmethod
    def adjustSectionName(self, text:str) -> str:
        pass

    @abstractmethod
    def getTableContent(self, content_chunk:str, start_table:int):
        pass
    
    def isSpecialTable(self, text:str) -> bool:
        for section in self.specialTableNamePhrases:
            if section in text:
                return True
        return False

    def getHorizontalTable(self, table):
        try:
            horizontalTable = []
            num_rows = len(table)
            start = 0
            if len(table[0]) == 1:
                start = 1
            num_cols_horizontal = len(table[start])
            for row in range(num_rows):
                if row > start:
                    num_cols_current = len(table[row])
                    if num_cols_current == num_cols_horizontal-1:
                        table[row].insert(0, table[row-1][0])
                    page_content = ''
                    page_content += '{'
                    for column in range(num_cols_horizontal):
                        if table[start][column][-1:] == ':':
                            table[start][column] = table[start][column][:-1]
                        page_content += table[start][column] + ": " + table[row][column]
                        if column != num_cols_horizontal-1:
                            page_content += ", "
                    page_content += "}"

                    if "Date" in page_content:
                        page_content = page_content.replace('Changed by', 'Version ' + self.version + ' , Changed by')
                    if "Satisfied by" in page_content:
                        page_content = page_content.replace('Description', 'Version ' + self.version + ' , Description')
                    
                    page_content = rawData(page_content)
                    horizontalTable.append(page_content+'\n')
        except:
            with open(self.error_log_path, 'a') as file:
                file.write('Table error in section ' + self.section_name + '\n')
            pass
        return horizontalTable

    def getVerticalTable(self, table):
        num_rows = len(table)      
        page_content = ''
        for row in range(num_rows):
            num_cols_vertical = len(table[row])
            for column in range(num_cols_vertical):
                table[row][column] = rawData(table[row][column])
                if column > 0:
                    if table[row][column] != table[row][column-1]:
                        if page_content[-2:] != ': ' and page_content[-1:] != ':':
                            page_content += ": "
                        if page_content[-1:] == ':':
                            page_content += " "
                        page_content += table[row][column]
                else:
                    page_content += table[row][column]
            if row != num_rows-1:
                page_content += "\n"
        return [page_content]

    def getTable(self):
        self.tables = []
        for t in range(len(self.tables_info)):
            table_info = self.tables_info[t]
            try:
                table_name = self.tables_name[t][0]
            except:
                if len(table_info[0]) == 1:
                    table_name = table_info[0][0]
                else:
                    # If this is a special table
                    if self.isSpecialTable(self.section_name):
                        table_name = self.section_name
                    else:
                        table_name = ''
            try:
                table_type = self.tables_type[t][0]
            except:
                table_type = 'horizontal'
                
            content = None
            if table_type == 'horizontal' or table_type == 'undefined':
                content = self.getHorizontalTable(table_info)
            elif table_type == 'vertical':
                content = self.getVerticalTable(table_info)
            else:
                print('Warning: undefined table !!!')

            self.tables.append([content, table_name, table_type])

    def extractNumbers(self, string):
        numbers = re.findall(r'\d+(?:\.\d+)*', string)
        if len(numbers) == 0:
            return ''
        return numbers[0]

    def getMetadata(self, document_path, document_type, header):
        self.header         = header
        self.paragraphs     = header['paragraph']
        self.tables_info    = header['table']
        self.tables_name    = header['tablename']
        self.tables_type    = header['tabletype']
        self.document_path  = document_path

        try: self.version   = document_path.split('/')[1]
        except:self.version = ''

        self.document_name  = os.path.basename(document_path)
        self.document_type  = document_type
        self.page           = header['page'] if len(header['page']) > 0 else ''
        self.level          = header['level'] if header['level'] != [] else 0
        self.section_name   = header['name'] if len(header['name']) > 0 else ''
        self.section_number = self.extractNumbers(self.section_name) if self.section_name != '' else ''
        self.wkproduct_link = header['wkproduct_link'] if len(header['wkproduct_link']) > 0 else ''
        self.guideline_link = header['guideline_link'] if len(header['guideline_link']) > 0 else ''
        self.guideline      = header['guideline'] if len(header['guideline']) > 0 else ''

        self.metadata = {"guideline"     : self.guideline,
                        "guideline_link" : self.guideline_link,
                        "wkproduct_link" : self.wkproduct_link,
                        "path"           : self.document_path, 
                        "type"           : self.document_type, 
                        "version"        : self.version, 
                        "page"           : self.page, 
                        "section_name"   : self.section_name, 
                        "section_number" : self.section_number
                        }


class HARDWARE_MANUAL(BASE_FORMAT):
    def __init__(self):
        self.startParagraphPhrases = []
        self.endParagraphPhrases = ['.']
        self.invalidStartCharacter = ['-', '\u2022']
        self.specialTableNamePhrases = []

    def getTableContent(self, content_chunk:str, start_table:int):
        # This type of document does not have the related process.
        return

    def adjustSectionName(self, text:str) -> str:
        # This type of document does not have the related process.
        return text

    def addRequirementTable(self, text:str) -> str:
        # This type of document does not have the related process.
        return text

    def checkEndRequirement(self, text:str) -> bool:
        # This type of document does not need to check end requirement. So just always return false
        return False

    def checkEndParagraph(self, text:str) -> bool:
        for end in self.endParagraphPhrases:
            if text.rstrip(' ').endswith(end):
                return True
        return False


class AUTOSAR(BASE_FORMAT):
    def __init__(self):
        # Call the constructor of the parent class using super()
        super().__init__()
        self.startParagraphPhrases = ['Specification of', 'Requirements on', 'AUTOSAR CP', 'Table of Content']
        self.endParagraphPhrases = ['.',':','\u2026']
        self.invalidStartCharacter = ['-', '\u2022']
        self.specialTableNamePhrases = ['Acronym', 'Requirements Tracing', 'Requirements traceability', 'Document Change History']
        self.splitContentChunkPatterns = '**'

    def getTableContent(self, content_chunk:str, start_table:int):
        start_table = 1
        table = self.tables[0]
        info = table[0]
        table_name = table[1]
        table_type = table[2]
        table_content = ''
        
        for part in info:
            table_content += part
        try:
            if table_type == 'vertical' and self.tables[1][2] == 'vertical':
                start_table = 2
                info = self.tables[1][0]
                table_content += '\n'
                for part in info:
                    table_content += part
        except:
            pass

        content_chunk = content_chunk.replace('{requirement_table}', table_content)  

    def adjustSectionName(self, text:str) -> str:
        if '[' in text and ']' in text:
            text = text.split('[', 1)[0]
        return text

    def addRequirementTable(self, text:str) -> str:
        '''
        \u2308: This is the left ceiling character (?).
        \n*: This matches zero or more newline characters.
        \s*: This matches zero or more whitespace characters.
        \u230b: This is the right ceiling character (?).
        \s?: This matches zero or one whitespace character.
        \(.*?\): This matches a string enclosed in parentheses.
        '''
        required_pattern = r'\u2308\n*\s*\u230b\s?\(.*?\)\s?'
        def replace_match(match):
            return match.group().replace('\u230b', '{requirement_table}\u230b')
        modified_text = re.sub(required_pattern, replace_match, text)
        return modified_text

    def checkEndRequirement(self, text:str) -> bool:
        end_pattern = r'\u230b\s?\(.*?\)\s?'
        # Find all occurrences of the end_pattern in the input text. 
        # The function returns a list of matches found in the text.
        matches = re.findall(end_pattern, text)

        # If there are any matches found in the text.
        if matches:
            start_pos = text.find(matches[-1])
            end_pos = start_pos + len(matches[-1])
            if end_pos == len(text):
                return True
        return False

    def checkEndParagraph(self, text:str) -> bool:
        for end in self.endParagraphPhrases: #  ['.',':','\u2026']
            if text.rstrip(' ').endswith(end):
                return True
        if self.checkEndRequirement(text):
            return True
        return False

    def GetAcronymsAndAbbreviations(self, document_path, document_type, header, path_to_destination):
        self.getMetadata(document_path, document_type, header)
        if 'Acronym' in self.section_name:
            self.getTable()
            with open(path_to_destination, 'r+') as file:
                data = json.load(file)
                if 'acronym' not in data:
                    data['acronym'] = {}
                document_name = os.path.basename(document_path).replace('.json','')
                if document_name not in data['acronym']:
                    data['acronym'][document_name] = []

                    for i in range(len(self.tables)):
                        table = self.tables[i]
                        info = table[0]

                        for part in info:
                            if len(part.split(':')) >= 2 and ('Acronym' in part or 'Abbreviation' in part):
                                part = part.rstrip('\n')

                                names, descriptions = part.split(',')[0], ('').join(part.split(',')[1:])
                                name = ''
                                description = ''
                                name = ('').join(names.split(':')[1:])
                                name = removeExtraSpaces(name)
                                description = ('').join(descriptions.split(':')[1:]).replace('}','')
                                description = removeExtraSpaces(description).rstrip(' ')

                                new_document = {
                                    "name": name,
                                    "description": description
                                }
                                data['acronym'][document_name].append(new_document)

                    file.seek(0)
                    json.dump(data, file, indent=4)
                    file.truncate()

        subheaders = header['subheader']
        if len(subheaders) == 0:
            return
        else:
            for subheader in subheaders:
                self.GetAcronymsAndAbbreviations(document_path, document_type, subheader, path_to_destination)

    def AcronymsAndAbbreviations(self, json_file_paths, document_type, path_to_destination):
        for i in tqdm(range(len(json_file_paths))):
            with open(json_file_paths[i], 'r', encoding='utf-8') as f:
                file_content = f.read()
                f.seek(0)  # Reset the file pointer to the beginning
                try:
                    json_data = json.load(f)
                except json.JSONDecodeError as e:
                    if config.debug:
                        print('Warning: Error loading JSON file', json_file_paths[i])
                        print('Error message:', e)
                    continue
            document_path = json_file_paths[i].replace(f'{config.middle_version_path}/','')
            self.GetAcronymsAndAbbreviations(document_path, document_type, json_data, path_to_destination)




                  