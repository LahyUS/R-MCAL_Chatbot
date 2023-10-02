from langchain.docstore.document import Document
from _utils import *

class COMMON_FILE: # Support pdf, pptx, docs
    def __init__(self):
        pass

    def getDocumentContent(self, document_path, document_name, header, document):
        convertTool = TREE_FORMAT()
        convertTool.getMetadata(document_path, document_name, header)
        convertTool.getContent(document)
        subheaders = header['subheader']
        if len(subheaders) == 0:
            return
        else:
            for subheader in subheaders:
                self.getDocumentContent(document_path, document_name, subheader, document)

    def myLoader(self,json_data, document_path, document_name):            
        document = []
        self.getDocumentContent(document_path, document_name, json_data, document)
        return document
    
class TREE_FORMAT:
    def __init__(self):
        self.end_pattern = r'\u230b\s?\(.*?\)\s?'
        self.requirement_pattern = r'\u2308\n*\s*\u230b\s?\(.*?\)\s?'
        self.table_of_content = ''

    def getContent(self, document):
        content = ''
        for i in range(len(self.paragraphs)):
            paragraph = self.paragraphs[i]
            if paragraph[0] != '' and self.checkStartParagraph(paragraph[0]):
                if(self.checkTableOfContent(paragraph[0])):
                    self.table_of_content += paragraph[0].split('....')[0] + '\n'
                    continue
                
                if(self.checkEndParagraph(paragraph[0])):
                    content += paragraph[0].rstrip(' ') + '\n'
                else:
                    content += paragraph[0]
        
        self.getTable()

        if content == '' and len(self.tables) == 0:
            return
        elif content == '':
            pass
        else:
            content = self.section_name.rstrip(' ') + '\n' + content

        content = self.addRequirementTable(content)

        part_of_contents = content.split('\n')
        part_of_contents = [part for part in part_of_contents if part != '']

        for i in range(len(part_of_contents)):
            try:
                if i == 0:
                    pass
                elif self.checkEndRequirement(part_of_contents[i]) == True:
                    part_of_contents[i] = part_of_contents[i] + '**'
                elif self.startsWithValidCharacter(part_of_contents[i]) == True and \
                    self.startsWithValidCharacter(part_of_contents[i-1]) == False:
                    part_of_contents[i] = '*\n' + part_of_contents[i]
                elif self.startsWithValidCharacter(part_of_contents[i]) == True and \
                    self.startsWithValidCharacter(part_of_contents[i-1]) == True:
                    part_of_contents[i-1] = part_of_contents[i-1] + '*'
            except:
                pass
        content = ('\n').join(part_of_contents)

        if self.table_of_content != '':
            metadata = {"path": self.document_path, 
                        "source": self.document_name, 
                        "page": '',
                        "section_name": 'Table_of_content', 
                        "section_number": ''}
            document.extend([Document(page_content=self.table_of_content.rstrip('\n'), metadata=metadata)])

        part_of_contents = content.split('**')

        start_table = 0
        for i in range(len(part_of_contents)):
            part_of_content = part_of_contents[i]
            if '{requirement_table}' in part_of_content:
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
                part_of_content = part_of_content.replace('{requirement_table}', table_content)          
            if part_of_content.strip() == '':
                continue
            if self.section_name != '' and i != 0:
                part_of_content = self.section_name.rstrip(' ') + '\n' + part_of_content
            self.section_name = self.removeRequirementName(self.section_name)
            document.extend([Document(page_content=part_of_content, metadata=self.metadata)])

        for i in range(len(self.tables)):
            if i < start_table:
                continue
            table = self.tables[i]
            info = table[0]
            table_name = table[1]
            table_type = table[2]

            if self.tableNambySectionName(table_name):
                for part in info:
                    if not part.strip():
                        continue
                    if table_name != '':
                        part = table_name + '\n' + part.rstrip('\n')
                    document.extend([Document(page_content=part.rstrip('\n'), metadata=self.metadata)])
            else:
                table_content = ''
                for part in info:
                    table_content += part
                document.extend([Document(page_content=self.section_name.rstrip(' ') + '\n' + table_content, metadata=self.metadata)])

    def removeRequirementName(self, text):
        if '[' in text and ']' in text:
            text = text.split('[', 1)[0]
        return text

    def addRequirementTable(self, text):
        def replace_match(match):
            return match.group().replace('\u230b', '{requirement_table}\u230b')
        modified_text = re.sub(self.requirement_pattern, replace_match, text)
        return modified_text

    def startsWithValidCharacter(self, text):
        # pattern = r'^[a-zA-Z0-9]'
        # match = re.search(pattern, text)
        # return match is not None
        start_lists = ['-', '\u2022']
        for start in start_lists:
            if text.split()[0] == start:
                return False
        return True

    def checkTableOfContent(self, text):
        if '......' in text:
            return True
        return False

    def checkStartParagraph(self, text):
        lists = ['Specification of', 'Requirements on', 'AUTOSAR CP', 'Table of Content']
        for string in lists:
            if text.startswith(string):
                return False
        return True

    def checkEndParagraph(self, text):
        end_lists = ['.', '. ', '\u2026 ', '\u2026', ': ', ':']
        for end in end_lists:
            if text.endswith(end):
                return True
        matches = re.findall(self.end_pattern, text)
        if matches:
            start_pos = text.find(matches[-1])
            end_pos = start_pos + len(matches[-1])
            if end_pos == len(text):
                return True
        return False
    
    def checkEndRequirement(self, text):
        matches = re.findall(self.end_pattern, text)
        if matches:
            start_pos = text.find(matches[-1])
            end_pos = start_pos + len(matches[-1])
            if end_pos == len(text):
                return True
        return False
    
    def tableNambySectionName(self, text):
        # Document Change History can be removed
        section_lists = ['Acronym', 'Requirements Tracing', 'Requirements traceability', 'Document Change History']
        for section in section_lists:
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
                    page_content = rawData(page_content)
                    horizontalTable.append(page_content+'\n')
        except:
            pass
        return horizontalTable

    def getVerticalTable(self, table):
        num_rows = len(table)      
        page_content = ''
        # page_content += '{'
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
        # page_content += '}'
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
                    if self.tableNambySectionName(self.section_name):
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

    def getMetadata(self, document_path, document_name, header):
        self.header = header
        self.paragraphs = header['paragraph']

        self.tables_info = header['table']
        self.tables_name = header['tablename']
        self.tables_type = header['tabletype']

        self.document_path = document_path
        self.document_name = document_name
        
        self.page = header['page'] if len(header['page']) > 0 else ''
        self.level = header['level'] if header['level'] != [] else 0
        self.section_name = header['name'] if len(header['name']) > 0 else ''
        self.section_number = self.extractNumbers(self.section_name) if self.section_name != '' else ''

        self.metadata = {"path": self.document_path, 
                         "source": self.document_name, 
                         "page": self.page, 
                         "section_name": self.section_name, 
                         "section_number": self.section_number}

    def extractNumbers(self, string):
        numbers = re.findall(r'\d+(?:\.\d+)*', string)
        return numbers[0]