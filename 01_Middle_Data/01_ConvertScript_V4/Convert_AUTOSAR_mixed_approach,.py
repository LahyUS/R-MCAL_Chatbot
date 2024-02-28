import os
import json
import sys

from pdf2docx import Converter
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
import subprocess 
import aspose.words as aw
from bs4 import BeautifulSoup
from PIL import Image
import shutil
from tqdm import tqdm
import fitz
import re


def convert_docx_to_pdf(input_path, output_path):
    command = [
        'soffice', 
        '--headless', 
        '--convert-to', 'pdf', 
        '--outdir', output_path,
        input_path
    ]
    subprocess.run(command)


def convert_pptx_to_pdf(pptx_path, pdf_path):
    command = ['unoconv', '-f', 'pdf', '-o', pdf_path, pptx_path]
    subprocess.run(command)


def generatejson(json, level):
    header={
        "level":[],
        "name":[],
        "pragraph":[],
        "table":[],
        "subheader":list()
    }

    header['subheader'] = json
    return header


def extract_table(element):
    table_data = []
    table_color = []
    table_bold = []
    istable = True
    rows = element.find_all('tr')
    for row in rows:
        row_data = [] 
        color =[]
        row_bold = []
        cells = row.find_all('td')
        if(len(cells) ==0):
            continue
        for cell in cells:
            # extract text
            colorin4 = cell.find_all('p')
            row_data.append(cell.text.replace('\u00a0','')) 
            # extract color
            cell_color = cell.get('style')

            if('background-color:' in cell_color):
                cell_color = 'true'
            else:
                cell_color = 'none'

            # extract bold status
            font_weight = cell.get('style')

            if len(colorin4) >0:
                if 'font-weight:bold' in str(colorin4[0]):
                    row_bold.append('true')
                else:
                    row_bold.append('false')
            else:
                row_bold.append('false')

            color.append(cell_color)
        table_data.append(row_data)
        table_color.append(color)
        table_bold.append(row_bold)

    return table_data,table_bold,table_color


def check_header(element):
    bold = False
    sub_elements = element.find_all()

    for sub_element in sub_elements:
        try:
            text_style = sub_element.get('style').split(";")
            for style in text_style:
                if "font-weight" in style:
                    bold = True
                    break
        except :
            continue

        if bold:
            break   

    if bold:
        for sub_element in sub_elements:
            sub_sub_element = sub_element.text.split(' ')[0]  
            try: 
                count = 0
                for num in sub_sub_element.split('.'):
                    if len(num) == 0:
                        continue

                    int(num)
                    count += 1

                if count > 0:
                    return True

            except:
                return False  

    return False 


def check_useless_word(element, i, num_pages):
    if (check_header(element) == False) and (
        ("Evaluation Only. Created with Aspose.Words. Copyright 2003-2023 Aspose Pty Ltd." in element.text)
        or ("Requirements on" in element.text) or ((str(i+1) + " of " + str(num_pages)) in element.text)
        or ("- AUTOSAR confidential - " in element.text) or (("Specification of" in element.text))
        or ("Document ID" in element.text) or ("AUTOSAR CP" in element.text) or ("General Requirements on" in element.text)): 
        return True

    return False


def check_bold(element):
    bold = False
    sub_elements = element.find_all()
    for sub_element in sub_elements:
        try:
            text_style = sub_element.get('style').split(";")
            for style in text_style:
                if "font-weight" in style:
                    bold = True
                    break

        except :
            continue

    return bold


def check_table_header(table_bold,table_color):
    table_type=[]
    if(len(table_bold)>1):
        if(not(len(table_color[0]) < len(table_color[1]))):
            if((table_color[0][0] == table_color[len(table_color)-1][0]) and (table_color[0][0] !='none')):
                table_type.append("vertical")
            elif((table_color[0][0] == table_color[0][len(table_color[0])-1]) and (table_color[0][0] !='none')):
                table_type.append("horizontal")
            elif((table_bold[0][0] == table_bold[len(table_color)-1][0]) and (table_bold[0][0] !='false')):
                table_type.append("vertical")
            elif((table_bold[0][0] == table_bold[0][len(table_color[0])-1]) and (table_bold[0][0] !='false')):
                table_type.append("horizontal")
            else:
                table_type.append('undefined')

        else:
            if((table_color[1][0] == table_color[len(table_color)-1][0]) and (table_color[1][0] !='none')):
                table_type.append("vertical")
            elif((table_color[1][0] == table_color[1][len(table_color[0])-1]) and (table_color[1][0] !='none')):
                table_type.append("horizontal")
            elif((table_bold[1][0] == table_bold[len(table_color)-1][0]) and (table_bold[1][0] !='false')):
                table_type.append("vertical")
            elif((table_bold[1][0] == table_bold[1][len(table_color[0])-1]) and (table_bold[1][0] !='false')):
                table_type.append("horizontal") 
            else:
                table_type.append('undefined')

    else :
            if((table_color[0][0] == table_color[len(table_color)-1][0]) and (table_color[0][0] !='none')):
                table_type.append("vertical")
            elif((table_color[0][0] == table_color[0][len(table_color[0])-1]) and (table_color[0][0] !='none')):
                table_type.append("horizontal")
            elif((table_bold[0][0] == table_bold[len(table_color)-1][0]) and (table_bold[0][0] !='false')):
                table_type.append("vertical")
            elif((table_bold[0][0] == table_bold[0][len(table_color[0])-1]) and (table_bold[0][0] !='false')):
                table_type.append("horizontal")
            else:
                table_type.append('undefined')

    return table_type


def flags_decomposer(flags):
    """Make font flags human readable."""
    l = []
    if flags & 2 ** 0:
        l.append("superscript")
    if flags & 2 ** 1:
        l.append("italic")
    if flags & 2 ** 2:
        l.append("serifed")
    else:
        l.append("sans")
    if flags & 2 ** 3:
        l.append("monospaced")
    else:
        l.append("proportional")
    if flags & 2 ** 4:
        l.append("bold")
    return ", ".join(l)


def get_offset_text(full_text, split_text):
    try:
        # Get the position of the split_text in the full_text
        offset = full_text.index(split_text)
        return full_text[:offset]

    except:
        print('[DEBUG] Invalid values passed in for get_offset_text')
        return ''


def get_digits_from_text(text):
    header_digits = []

    if text != '':
        # Extract digits in the expected header format (sequences separated by periods)
        matches = re.findall(r'^\d+(?:\.\d+)*', text)
        if matches:
            res = matches[0]
            if len(text) > len(res):
                if text[len(res)] == ' ':
                    split_match = res.split('.')
                    if all(part.isdigit() for part in split_match if part):  # Check if all parts are digits
                        header_digits.extend(map(int, split_match))  # Extract all numbers in each match
            else:
                split_match = res.split('.')
                if all(part.isdigit() for part in split_match if part):  # Check if all parts are digits
                    header_digits.extend(map(int, split_match))  # Extract all numbers in each match
        
        # if not header_digits and text.strip()[0].isdigit() and all(char.isdigit() or char == '.' for char in text.strip()):
        #     header_digits = [int(part) for part in text.strip().split('.') if part.isdigit()]

        if not header_digits:
            # Check if the text starts with a standalone digit followed by a space or a period
            standalone_digit = re.match(r'^(\d+)\s|\.(\d+)', text)

            if standalone_digit:
                header_digits.append(int(standalone_digit.group(1) or standalone_digit.group(2)))

            # Check if the extracted header digits are located at the beginning of the text
            if header_digits:
                text_start = text.split()[0]
                if text_start.isdigit() and int(text_start) == header_digits[0]:
                    return header_digits

    return header_digits


def is_valid_header(current_digits, previous_digits):
    # Check if the difference between current and previous digits is not more than 1
    diff = abs(len(current_digits) - len(previous_digits))
    if diff <= 1:
        for cd, pd in zip(current_digits, previous_digits):
            if abs(cd - pd) > 1:
                return False  # Invalid header if the difference exceeds 1
        return True  # Valid header if all differences are within 1
    return False  # Invalid header if the difference in number of digits is more than 1


def is_valid_continous_header(current_text, previous_text):
    # Get the digits from current and previous texts
    current_digits = get_digits_from_text(current_text)
    previous_digits = get_digits_from_text(previous_text)

    # Check validity of the header
    valid_header = is_valid_header(current_digits, previous_digits)
    return valid_header


def get_next_header_in_hierarchy(header_index):
    next_header_main_name = ''
    next_header = ''

    try:
        next_header = hierarchy[header_index+1]
        next_header_main_name = next_header.lstrip(".0123456789").strip().replace(' ', '')
    except:
        next_header_main_name = ''

    return next_header, next_header_main_name


def find_digit_headers_indices(text):
    """
    Identifies and returns start and end indices of numeric pattern-based headers in the given text, 
    accommodating multi-line headers.
    """
    # Adjusted pattern to match headers, even if they span multiple lines, until the next numeric header
    pattern = r'\n(\d+(?:\.\d+)*)\s+([^\n]+(?:\n(?!\d+(?:\.\d+)*\s).*)*)'
    matches = re.finditer(pattern, text)
    indices = []
    for match in matches:
        start_index = match.start()
        end_index = match.end()
        indices.append((start_index+1, end_index-1))
    return indices


def post_process_found_header(header_text, header_index, Cur_Section_Data={}):
    """
    Cleans and formats a raw header text by trimming content after the next numeric header and '⌈' character, 
    and normalizes line breaks.
    Also updates the header index to reflect the new end position of the processed header.
    """
    # if '2.1 Conventions used' in header_text:
    #     print()
    original_length = len(header_text)
    # Split at the start of the next header
    header_text = re.split(r'\n\d+(?:\.\d+)*\s', header_text)[0]
    # Split before the '⌈' character
    header_text = header_text.split('⌈')[0]

    if Cur_Section_Data:
        if Cur_Section_Data['first_texts'] != '':
            split_pattern = Cur_Section_Data['first_texts']
            header_split_patterns = ['\n', '\uf0b7', '\uf0a7', '\o']
            regex_pattern = '|'.join(map(re.escape, header_split_patterns))
            header_parts = re.split(regex_pattern, header_text)
            for part in header_parts:
                if part.strip() != '':
                    if part in Cur_Section_Data['first_texts'] or Cur_Section_Data['first_texts'] in part:
                        split_pattern = part
                        break
            # Splitting the string A at the first occurrence of string B
            parts = header_text.split(split_pattern, 1)
            # Getting the part before string B
            if len(parts) > 1:
                if parts[0] in header_text or header in parts[0]:
                    header_text = parts[0]

    # Replace newline characters and strip leading/trailing spaces
    header_text = header_text.replace('\n', ' ').strip()

    # Calculate the new length and update the end index
    new_length = len(header_text)
    updated_header_index = (header_index[0], header_index[0] + new_length)

    return header_text, updated_header_index


def format_bullet_list(bullet_points):
    """
    Transforms a list of strings containing bullet points into a formatted list. 
    It handles different bullet symbols, indenting each level appropriately. 
    The function also detects and formats sub-items under bullet points. 
    Non-bullet text is appended to the closest preceding bullet point. 
    The output is a list of formatted bullet point strings.
    """

    # Define symbols for different bullet levels and their replacements
    bullet_symbols = {
        '\uf0b7': '-',
        'o': '+',
        '\uf0a7': '*'
    }
    levels = list(bullet_symbols.keys())

    def get_level(line):
        # Determine the level of the bullet point
        for i, symbol in enumerate(levels):
            if line.strip().startswith(symbol):
                return i
        return -1  # Not a bullet point

    def format_line(line, level, has_sub_items=False):
        # Remove bullet symbol and format line
        line = line.strip()[len(levels[level]):].strip()
        if has_sub_items:
            line += ':'
        indent = '  ' * level
        return f"{indent}{bullet_symbols[levels[level]]} {line}"

    formatted_list = []
    current_level = 0

    for i, point in enumerate(bullet_points):
        level = get_level(point)

        if level == -1:
            # If it's not a bullet point, append it to the last bullet point
            formatted_list[-1] += ' ' + point.strip()
        else:
            # Check if this bullet point has sub-items
            has_sub_items = i + 1 < len(bullet_points) and get_level(bullet_points[i + 1]) > level
            # Format and append the bullet point
            formatted_list.append(format_line(point, level, has_sub_items))
            current_level = level

    return formatted_list


def find_bullet_patterns(text):
    """
    Identifies and extracts bullet points from text, then formats them using format_bullet_list. 
    It handles multiple bullet symbols and organizes them into a structured list.
    """
    # Single pattern to capture all bullet points
    pattern = r'(\n\uf0b7\s*.*?|\n\uf0a7\s*.*?|\no\s+\S.*?)(?=\n\uf0b7|\n\uf0a7|\no\s+\S|\n\s*\n|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    output = format_bullet_list(matches)
    return output


def find_pattern_in_text(text, pattern):
    """
    Searches the given text for occurrences of the specified regular expression pattern, 
    returning a list of tuples with start and end indices for each match.
    """
    matches = re.finditer(pattern, text)

    indices = []
    for match in matches:
        start_index = match.start(1)
        end_index = match.end(1)
        indices.append((start_index, end_index))

    return indices


def process_content(content):
    """
    Splits the input content into bullet and non-bullet sections using a regex pattern, processes each section accordingly, 
    and then combines them into a structured format. Bullet sections are formatted using find_bullet_patterns, 
    while non-bullet content is accumulated and appended as separate sections. 
    The function returns the combined, processed content as a single string.
    """
    # Define a regex pattern to split the content into bullet and non-bullet sections
    # pattern = r'(\n\uf0b7\s*.*?|\n\uf0a7\s*.*?|\no\s*.*?)(?=\n\uf0b7|\n\uf0a7|\no|\n\s*\n|$)'
    pattern = r'(\n\uf0b7\s*.*?|\n\uf0a7\s*.*?|\no\s+\S.*?)(?=\n\uf0b7|\n\uf0a7|\no\s+\S|\n\s*\n|$)'

    
    # Split the content using the regex pattern
    sections = re.split(pattern, content, flags=re.DOTALL)

    processed_sections = []
    current_section = ''

    for section in sections:
        if section.strip().startswith(('\uf0b7', '\uf0a7', 'o')):
            # Process the current section if it's not empty
            if current_section.strip():
                processed_sections.append(current_section.strip())
                current_section = ''
            # Process bullet section
            processed_bullet = find_bullet_patterns(section)
            processed_sections.extend(processed_bullet)
        else:
            # Accumulate non-bullet content
            current_section += '\n' + section

    # Add any remaining non-bullet content
    if current_section.strip():
        processed_sections.append(current_section.strip())

    return '\n'.join(filter(None, processed_sections))


def get_mapped_content(cur_header, raw_content, Cur_Section_Data={}):
    """
    Extracts content corresponding to a given header from raw_content, using header indices to delineate content sections. 
    Returns the mapped content and a flag indicating if the end of the page is reached.
    """
    end_of_page = False
    mapped_content = ''

    if cur_header == '':
        return raw_content, end_of_page

    # Utilize PyMuPDF to extract raw text. Then, get index list of headers in the current text page
    found_header_indices = find_digit_headers_indices(raw_content)
    mapped_content_raw = [raw_content[item[0]:item[1]] for item in found_header_indices]
    
    # Iterate through the found indices to get the bullet content
    for i, index in enumerate(found_header_indices):
        # Find part of the extracted content that matchs the current handling header
        header_text = raw_content[index[0]:index[1]]
        cleaned_header, updated_index = post_process_found_header(header_text, index, Cur_Section_Data)
        found_header_indices[i] = updated_index
        if cur_header.replace(' ', '') in cleaned_header.replace(' ', '')  or cleaned_header.replace(' ', '')  in cur_header.replace(' ', ''):
            content_start = found_header_indices[i][1]
            
            # The end position of the current part is the beginning of the next part 
            if i < len(found_header_indices) - 1:
                content_end = found_header_indices[i+1][0] 
            # Else, the end position is the end of the extracted text
            else:
                content_end =  len(raw_content)-1 
                # Due to all the content was captured, move to the next page
                if cur_header != '':
                    end_of_page = True
            if '6.1.1.1 [SRS_Adc_12307]' in cur_header:
                print(raw_content[2300:content_end])

            mapped_content = raw_content[content_start:content_end]
            break

    return mapped_content, end_of_page


def extract_bullet_data(cur_header, raw_content, Cur_Section_Data={}):
    """
    Retrieves and processes content associated with a specific header to extract bullet points and standard paragraphs. 
    Returns the processed content and a flag indicating page completion.
    """ 
    element_text_main_content = ''
    mapped_content, end_of_page = get_mapped_content(cur_header, raw_content, Cur_Section_Data)
    # Process the raw content to extract bullet points and normal paragraphs
    processed_content = process_content(mapped_content)
    element_text_main_content += '\n' + processed_content

    return element_text_main_content, end_of_page


def extract_content_by_keywords(text, keywords):
    """
    Extracts and organizes content segments from text based on specified keywords. 
    Each segment includes a keyword and its associated text, up to the next keyword or end of text. 
    Returns a list of keyword-content pairs.
    """
    # Create a pattern that matches each keyword followed by any text until the next keyword
    pattern = r'(' + '|'.join(re.escape(keyword) for keyword in keywords) + r')\s*:\s*(.*?)(?=' + '|'.join(re.escape(keyword) for keyword in keywords) + r'\s*:|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    # Create a list from the matches
    content_list = [(match[0], match[1].strip()) for match in matches]

    return content_list


def post_process_table(cur_header, raw_content, table, Cur_Section_Data={}):
    """
    Formats bullet data within a table after mapping content to the specified header. Extracts relevant sections based on table categories 
    and refines these sections for bullet points and paragraphs, updating the table with processed content.
    """
    if '6.1.1.3 [SRS_Adc_12817]' in cur_header:
        print()
    mapped_content, end_of_page = get_mapped_content(cur_header, raw_content, Cur_Section_Data)
    table_category_list = table_category_list = [item[0].replace(':', '').strip() for item in table if item[0].strip() != '']
    table_content = extract_content_by_keywords(mapped_content, keywords=table_category_list)

    if len(table_content) == len(table_category_list):
        for iter, item in enumerate(table_content):
            # Process the raw content to extract bullet points and normal paragraphs
            data = item[1]
            processed_content = process_content(data)
            table[iter][1] = '\n' + processed_content
    

def add_current_header_to_root(cur_header, current_headers, parent_header, sub_element, element_text, Tableofcontent):
    Cur_Section_Data = {
        'header': cur_header,
        'begin': True,
        'first_texts': ''
    }
    # Start create table of content
    # if paragraph is header
    for j in range (len(sub_element[0].text.split('.'))-1):
        Tableofcontent +='\t'

    Tableofcontent += element_text.replace('\u00a0', '') + '\n'

    # Start create Json
    #level = len(sub_element[0].text.split('.'))
    level = len(get_digits_from_text(cur_header))
    name = cur_header
    # Create a new header dictionary for each line
    new_header = {
        "page": str(i+1),
        "level": level,
        "name": name,
        "paragraph": [],
        "table": [],
        "tablename": [],
        "tabletype": [],
        "wkproduct_link": [],
        "guideline_link": [],
        "guideline": [],
        "subheader": []
    }


    mlevel = level

    # Add the new header as a subheader of the appropriate parent header
    while(1):
        try:
            parent_header = current_headers[mlevel - 1]
            break

        except:
            mlevel -= 1
            continue

    parent_header["subheader"].append(new_header)
    # Update the current headers list. Current header list contains upper level with regard to the current header
    # Remove all headers after the current level
    current_headers[:] = current_headers[:level]  
    # Add the new header to the list
    current_headers.append(new_header)  

    return level, Cur_Section_Data, Tableofcontent

# Handle file path
current_path = os.getcwd()

Workspace_path = current_path +'/Workspace'
if not (os.path.exists(Workspace_path)):
   os.makedirs(Workspace_path)

Output_path = current_path + '/Data Output'
if not (os.path.exists(Output_path)):
   os.makedirs(Output_path)
   
DocDirs =[]
tempdocdirs = []
OptionFlags = sys.argv[1]
Docfolder = sys.argv[2].split('/')[len(sys.argv[2].split('/'))-1]
folder_path = Output_path + '/' + Docfolder
folder_img_path = Output_path + '/' + Docfolder +'_img'

# Classify document type 
if( OptionFlags == '--pptx'):
    for filename in os.listdir(sys.argv[2]):
        if filename.endswith('.pptx'):
            DocDirs.append(os.path.join(sys.argv[2], filename))

elif (OptionFlags == '--pdf'):
    for filename in os.listdir(sys.argv[2]):
        if filename.endswith('.pdf'):
            if(sys.argv[3] =='--update'):
                if(os.path.exists(Output_path + '/' + Docfolder +'/' +filename.split('.')[0] + '.json')):
                    continue
                DocDirs.append(os.path.join(sys.argv[2], filename))
            DocDirs.append(os.path.join(sys.argv[2], filename))

elif (OptionFlags == '--docx'):
    for filename in os.listdir(sys.argv[2]):
        if filename.endswith('.docx'):
            DocDirs.append(os.path.join(sys.argv[2], filename))

# Get file paths 
if(OptionFlags == '--pptx'):
    for docdir in DocDirs:
        pptx_path = docdir
        docsub = docdir.split('/')# Replace with the actual path to your PPTX file
        pdf_path = Workspace_path + '/' +Docfolder + '/' + docsub[len(docsub)-1].split('.')[0] + '.pdf'

        if not os.path.exists(folder_path): 
            os.makedirs(folder_path)

        # Replace with the desired output path for the PDF file
        convert_pptx_to_pdf(pptx_path, pdf_path)
        tempdocdirs.append(pdf_path)
    DocDirs = tempdocdirs

if(OptionFlags == '--docx'):
    for docdir in DocDirs:
        docx_path = docdir
        docsub = docdir.split('/')# Replace with the actual path to your PPTX file
        pdf_path = Workspace_path + '/' + Docfolder

        if not os.path.exists(folder_path): 
            os.makedirs(folder_path)

        # Replace with the desired output path for the PDF file 
        convert_docx_to_pdf(docx_path, pdf_path)
        tempdocdirs.append(Workspace_path + '/' + docsub[len(docsub)-1].split('.')[0] + '.pdf')
    DocDirs = tempdocdirs

# Create required folders
if not os.path.exists(folder_path): 
    os.makedirs(folder_path)

# Create required folders
if not os.path.exists(folder_img_path): 
            os.makedirs(folder_img_path)

numdoc = len(DocDirs)
progress_bar = tqdm(total=numdoc, unit='iteration', colour="red")
progress_bar.set_postfix_str("\033[31m")


# ! Main process. Iterate through all files and handle them.
for DocDir in DocDirs:
    LDocName = DocDir.split('/')
    DocName = LDocName[len(LDocName)-1].split('.')[0]

    # if 'AUTOSAR_SRS_Eth' not in DocName:
    #     continue

    # Open the PDF file in read-binary mode
    with fitz.open(DocDir) as doc:
        # Create a PdfFileReader object
        num_pages = doc.page_count

        PyMuPDF_support_doc = fitz.open(DocDir)
        table_of_content = chr(12).join([page.get_text() for page in PyMuPDF_support_doc])
        doc = {
            "name": DocName,
            "version": Docfolder,
            "content": list()
        }

        header = {
            "page": list(),
            "level" : [],
            "name": [],
            "paragraph": list(),
            "table": list(),
            "tablename": list(),
            "tabletype": list(),
            "wkproduct_link": list(),
            "guideline_link": list(),
            "guideline": list(),
            "subheader": list()
        }

        log_err =""
        list_pages = list()

        Tableofcontent = ''
        current_headers = [header] 
        level = 1 # Add an initial header as the root
        within_main_content = False

        root_hierarchicy = []
        virtual_sub_digit = ''
        # Loop all page of a file  
        for i in range(num_pages):
            skip_this_page = False
            # Update progress bar 
            progress_bar.update(1/num_pages)
            count = 0

            # Extract the specific page
            page = PyMuPDF_support_doc.load_page(i)
            # Create a PDF document with just this page
            single_page_pdf = fitz.open()
            single_page_pdf.insert_pdf(PyMuPDF_support_doc, from_page=i, to_page=i)

            # Define output file paths
            single_page_pdf_path = os.path.join(Workspace_path, f"page_{i}.pdf")
            output_html_path = os.path.join(Workspace_path, f"page_{i}.html")
            # Save the single page PDF
            single_page_pdf.save(single_page_pdf_path)
            single_page_pdf.close()
            # Convert the single page PDF to HTML using Aspose.Words
            doc_word = aw.Document(single_page_pdf_path)

            html_save_options = aw.saving.HtmlSaveOptions()
            html_save_options.export_images_as_base64 = True  # Export images as base64
            html_save_options.css_style_sheet_type = aw.saving.CssStyleSheetType.EXTERNAL  # Use external CSS
            html_save_options.export_font_resources = True  # Export font resources
            html_save_options.fonts_folder = os.path.join(Workspace_path, "fonts")  # Specify fonts folder
            html_save_options.images_folder = os.path.join(Workspace_path, "images")   # Specify images folder

            doc_word.save(output_html_path, html_save_options)
            #doc_word.save(output_html_path, aw.SaveFormat.HTML)

            PyMuPDF_support_page = PyMuPDF_support_doc.load_page(i)
            PyMuPDF_support_page_blocks = PyMuPDF_support_page.get_text("dict", flags=11)["blocks"]
            PyMuPDF_support_page_text = PyMuPDF_support_page.get_text("text")
            hierarchy = []
            previous_text = ""
            previous_minus1_text = ""
            previous_minus2_text = ""
            previous_bold = False
            previous_minus1_bold = False
            previous_minus2_bold = False
            previous_digit = ''
            
            # Get the current page heading structure
            for b in PyMuPDF_support_page_blocks:  # iterate through the text blocks
                for l in b["lines"]:  # iterate through the text lines
                    for s in l["spans"]:  # iterate through the text spans
                        current_text = s["text"].strip()
                        current_bold = True if "bold" in flags_decomposer(s["flags"]) else False
                        current_digit_raw = re.search(r'^(\d+(\.\d+)*)', current_text.strip())
                        current_digit = ''
                        current_digit_level = 1
                        if current_digit_raw:
                            current_digit = current_digit_raw.group(1)
                            current_digit_level = len(current_digit.split('.'))

                        # Check conditions for forming a numeric heading pattern
                        is_cur_a_correct_head       = False
                        is_cur_an_add_text          = False
                        is_prev_a_correct_head      = False
                        is_splitted_head            = False
                        is_prev_an_uncompleted_head = False
                        is_correct_digit_header     = False
                        previous_continous_split_digit_header = ''
                        previous_continous_digit_header_text = ''

                        if current_text.strip() != '':
                            current_text_split_digit = current_text.lstrip(".0123456789")
                            #is_cur_a_correct_head = current_bold and current_text[0].isdigit() and any(not char.isdigit() for char in current_text_split_digit)
                            is_cur_a_correct_head = current_bold and bool(get_digits_from_text(current_text)) and any(not char.isdigit() for char in current_text_split_digit)
                            is_cur_an_add_text = current_bold and any(not char.isdigit() for char in current_text_split_digit) 
                            is_splitted_head = current_bold and previous_bold and current_text and previous_text and bool(get_digits_from_text(previous_text)) and any(not char.isdigit() for char in current_text_split_digit)
                            # General pattern to match any string within square brackets
                            code_pattern = r'\[.*?\]'
                            # Use re.search() to find the pattern
                            code_match = re.search(code_pattern, current_text)
                            if code_match:
                                current_text_is_code_def = True if code_match.start()==0 else False
                            else: current_text_is_code_def = False

                        if previous_text.strip() != '':
                            previous_text_split_digit = previous_text.lstrip(".0123456789")
                            is_prev_a_correct_head = previous_bold and bool(get_digits_from_text(previous_text)) and any(not char.isdigit() for char in previous_text_split_digit)
                            
                            try:
                                is_prev_an_uncompleted_head = previous_text[-2].isdigit() and previous_text[-1] == ']'
                            except: 
                                is_prev_an_uncompleted_head = False

                        if previous_minus1_text != '':
                            previous_minus1_text_split_digit = previous_minus1_text.lstrip(".0123456789")
                            is_prev_minus1_a_correct_head = bool(get_digits_from_text(previous_minus1_text))

                        if previous_minus2_text != '':
                            previous_minus2_text_split_digit = previous_minus2_text.lstrip(".0123456789")
                            is_prev_minus2_a_correct_head = bool(get_digits_from_text(previous_minus2_text))

                        if hierarchy: 
                            previous_continous_split_digit_header = hierarchy[-1].lstrip(".0123456789")
                            previous_continous_digit_header_text = hierarchy[-1]
                            previous_header_digit_part = previous_continous_digit_header_text.split(previous_continous_split_digit_header)[0]
                        elif root_hierarchicy:
                            previous_continous_split_digit_header = root_hierarchicy[-1].lstrip(".0123456789")
                            previous_continous_digit_header_text = root_hierarchicy[-1]
                            previous_header_digit_part = previous_continous_digit_header_text.split(previous_continous_split_digit_header)[0]
                        else:
                            previous_continous_split_digit_header = ''
                            previous_continous_digit_header_text = ''
                            previous_header_digit_part = ''

                        # Check if the current text is a correct format heading: bold digits + bold text
                        hierarchy_condition1 = is_cur_a_correct_head

                        # Check if the previous text is a correct format heading, and the current text is an additional text
                        hierarchy_condition2 = is_prev_a_correct_head and is_cur_an_add_text
                        
                        # Check if the current text is raw texts and previous text is a digit header (e.g: previous: 2.1, current: 'requirement')
                        hierarchy_condition3 = is_splitted_head
                        
                        # Check if the current text is empty and the preivous text is digit header and the next text might be an additional heading text
                        hierarchy_condition4 = previous_bold == False and previous_text and current_bold and current_text == ''

                        # Check if previous text is uncompleted head (e.g: prev: 2.1 [SRS_1234], curr: bold-ABC_XYZ)
                        hierarchy_condition5 = is_prev_a_correct_head and is_prev_an_uncompleted_head

                        # Check if this is a header with uncatched digit_header type 1: Uncatched but completed 
                        hierarchy_condition6 = previous_minus2_bold and not is_prev_minus2_a_correct_head and previous_minus1_bold and not is_prev_minus1_a_correct_head and previous_bold and not is_prev_a_correct_head and previous_text and current_text == '⌈'

                        # Check if this is a header with uncatched digit_header type 1: Uncatched but completed 
                        hierarchy_condition7 = previous_minus1_bold and not is_prev_minus1_a_correct_head and previous_bold and not is_prev_a_correct_head and previous_text and current_text == '⌈'

                        # Check if this is a header with uncatched digit_header type 1: Uncatched but completed 
                        #hierarchy_condition6 = previous_bold and not is_prev_a_correct_head and previous_text and previous_minus1_bold and not is_prev_minus1_a_correct_head and not current_bold and current_text == '⌈'

                        # Check if this is a header with uncatched digit_header type 2: Uncatched but not completed
                        hierarchy_condition8 = previous_bold and not is_prev_a_correct_head and previous_text and current_text == '⌈'
                        
                        catch_text = '4.2.1 Con'
                        if catch_text in current_text or catch_text in previous_text:
                            print()
                        # Main check conditions
                        if hierarchy_condition1 and current_digit != previous_digit:
                            hierarchy.append(current_text) 
                            previous_minus2_text = previous_minus1_text
                            previous_minus1_text = previous_text
                            previous_text = current_text

                        elif hierarchy_condition2:
                            previous_heading = hierarchy[-1]
                            del hierarchy[-1]
                            new_heading = previous_heading + " " + current_text
                            hierarchy.append(new_heading) 
                            previous_minus2_text = previous_minus1_text
                            previous_minus1_text = previous_text
                            previous_text = new_heading

                        elif hierarchy_condition3:
                            hierarchy.append(previous_text + " " + current_text) 
                            previous_minus2_text = previous_minus1_text
                            previous_minus1_text = previous_text
                            previous_text = previous_text + " " + current_text

                        elif hierarchy_condition4:
                            previous_minus2_text = previous_minus1_text
                            previous_minus1_text = previous_text
                            previous_text = previous_text
                            previous_minus2_bold = previous_minus1_bold
                            previous_minus1_bold = previous_bold
                            previous_bold = True
                            continue

                        elif hierarchy_condition5:
                            new_heading = hierarchy[-1] + ' ' + current_text
                            hierarchy[-1] = new_heading
                            previous_minus2_text = previous_minus1_text
                            previous_minus1_text = previous_text
                            previous_text = new_heading
                            previous_minus2_bold = previous_minus1_bold
                            previous_minus1_bold = previous_bold
                            previous_bold = True
                            continue

                        elif hierarchy_condition6 and (bool(hierarchy) or bool(root_hierarchicy)):
                            # Make digit header
                            if virtual_sub_digit == '':
                                virtual_sub_digit = previous_header_digit_part + '.1'

                            else:
                                virtual_sub_digit_list = get_digits_from_text(virtual_sub_digit)
                                current_digit_list = get_digits_from_text(previous_continous_digit_header_text)
                                if len(virtual_sub_digit_list) < len(current_digit_list):
                                    check_range = len(virtual_sub_digit_list)
                                else: 
                                    check_range = len(current_digit_list)

                                is_new_header_section = False
                                for i in range(0, check_range):
                                    if virtual_sub_digit_list[i] != current_digit_list[i]:
                                        is_new_header_section = True
                                        break
                                if is_new_header_section: 
                                    parent_digit = '.'.join(str(num) for num in current_digit_list)
                                    virtual_sub_digit = parent_digit + '.1'
                                else:
                                    # virtual_index = int(virtual_sub_digit[-1]) + 1
                                    # virtual_sub_digit = virtual_sub_digit[:-1] + str(virtual_index)

                                    # Split the virtual_sub_digit by '.', convert the last part, increment, and join back
                                    virtual_sub_digit_parts = virtual_sub_digit.split('.')
                                    virtual_sub_digit_parts[-1] = str(int(virtual_sub_digit_parts[-1]) + 1)
                                    virtual_sub_digit = '.'.join(virtual_sub_digit_parts)

                            new_heading = virtual_sub_digit + ' ' + previous_minus2_text + ' ' + previous_minus1_text + ' ' + previous_text
                            hierarchy.append(new_heading)
                            previous_text = new_heading
                            previous_bold = True
                            continue

                        elif hierarchy_condition7 and (bool(hierarchy) or bool(root_hierarchicy)):
                            # Make digit header
                            if virtual_sub_digit == '':
                                virtual_sub_digit = previous_header_digit_part + '.1'

                            else:
                                virtual_sub_digit_list = get_digits_from_text(virtual_sub_digit)
                                current_digit_list = get_digits_from_text(previous_continous_digit_header_text)
                                if len(virtual_sub_digit_list) < len(current_digit_list):
                                    check_range = len(virtual_sub_digit_list)
                                else: 
                                    check_range = len(current_digit_list)

                                is_new_header_section = False
                                for i in range(0, check_range):
                                    if virtual_sub_digit_list[i] != current_digit_list[i]:
                                        is_new_header_section = True
                                        break
                                if is_new_header_section: 
                                    parent_digit = '.'.join(str(num) for num in current_digit_list)
                                    virtual_sub_digit = parent_digit + '.1'
                                else:
                                    # virtual_index = int(virtual_sub_digit[-1]) + 1
                                    # virtual_sub_digit = virtual_sub_digit[:-1] + str(virtual_index)

                                    # Split the virtual_sub_digit by '.', convert the last part, increment, and join back
                                    virtual_sub_digit_parts = virtual_sub_digit.split('.')
                                    virtual_sub_digit_parts[-1] = str(int(virtual_sub_digit_parts[-1]) + 1)
                                    virtual_sub_digit = '.'.join(virtual_sub_digit_parts)

                            new_heading = virtual_sub_digit + ' ' + previous_minus1_text + " " + previous_text
                            hierarchy.append(new_heading)
                            previous_text = new_heading
                            previous_bold = True
                            continue

                        elif hierarchy_condition8 and (bool(hierarchy) or bool(root_hierarchicy)):
                            # Make digit header
                            if virtual_sub_digit == '':
                                virtual_sub_digit = previous_header_digit_part + '.1'

                            else:
                                virtual_sub_digit_list = get_digits_from_text(virtual_sub_digit)
                                current_digit_list = get_digits_from_text(previous_continous_digit_header_text)
                                if len(virtual_sub_digit_list) < len(current_digit_list):
                                    check_range = len(virtual_sub_digit_list)
                                else: 
                                    check_range = len(current_digit_list)

                                is_new_header_section = False
                                for i in range(0, check_range):
                                    if virtual_sub_digit_list[i] != current_digit_list[i]:
                                        is_new_header_section = True
                                        break
                                if is_new_header_section: 
                                    parent_digit = '.'.join(str(num) for num in current_digit_list)
                                    virtual_sub_digit = parent_digit + '.1'
                                else:
                                    # virtual_index = int(virtual_sub_digit[-1]) + 1
                                    # virtual_sub_digit = virtual_sub_digit[:-1] + str(virtual_index)
                                    # Split the virtual_sub_digit by '.', convert the last part, increment, and join back
                                    virtual_sub_digit_parts = virtual_sub_digit.split('.')
                                    virtual_sub_digit_parts[-1] = str(int(virtual_sub_digit_parts[-1]) + 1)
                                    virtual_sub_digit = '.'.join(virtual_sub_digit_parts)
                                    
                            new_heading = virtual_sub_digit + ' ' + previous_text
                            hierarchy.append(new_heading)
                            previous_text = new_heading
                            previous_bold = True
                            continue

                        else: 
                            previous_minus2_text = previous_minus1_text
                            previous_minus1_text = previous_text
                            previous_text = current_text

                        previous_digit = current_digit
                        previous_minus2_bold = previous_minus1_bold
                        previous_minus1_bold = previous_bold
                        previous_bold = current_bold
            
            # Add to the main document heading structure
            root_hierarchicy.extend(hierarchy)
            print(hierarchy)
            
            # If the main content begins
            hierarchy_lower = [sub.lower().replace(' ', '') for sub in hierarchy]
            if '1scopeofdocument' in hierarchy_lower or '1scopeofthisdocument' in hierarchy_lower:
                within_main_content = True

            # Read the text from the saved HTML document  
            try: 
                with open(output_html_path, 'r', encoding='utf-8') as file:
                    # Load HTML data
                    html_content = file.read()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    soup = soup.div
                    # Find all elements in the <body> section
                    body_elements = soup.find_all(recursive=False)

                    if not within_main_content:
                        # Loop all elements of a page html 
                        for element in body_elements:
                            element_text = element.text
                            element_name = element.name
                            if element_name == 'p':# or element_name == 'ol': # Check for paragraph element
                                if (check_useless_word(element, i, num_pages)): # Skip useless words
                                    continue

                                sub_element = element.find_all()

                                if check_header(element): # If this is a heading of content
                                    # Start create table of content
                                    # if paragraph is header
                                    for j in range (len(sub_element[0].text.split('.'))-1):
                                        Tableofcontent +='\t'

                                    Tableofcontent += element_text.replace('\u00a0','') + '\n'

                                    # Start create Json
                                    level = len(sub_element[0].text.split('.'))
                                    # Remove the indentation and store the name in the header dictionary
                                    name = element_text.replace('\u00a0','')
                                    # Create a new header dictionary for each line
                                    new_header = {
                                        "page": str(i+1),
                                        "level": level,
                                        "name": name,
                                        "paragraph": [],
                                        "table": [],
                                        "tablename": [],
                                        "tabletype": [],
                                        "subheader": []
                                    }
                                    mlevel = level

                                    # Add the new header as a subheader of the appropriate parent header
                                    while(1):
                                        try:
                                            parent_header = current_headers[mlevel - 1]
                                            break

                                        except:
                                            mlevel -= 1
                                            continue
                                            
                                    parent_header["subheader"].append(new_header)
                                    # Update the current headers list. Current header list contains upper level with regard to the current header
                                    # Remove all headers after the current level
                                    current_headers = current_headers[:level]  
                                    # Add the new header to the list
                                    current_headers.append(new_header)  
                                # If this is a paragraph  
                                else: 
                                    mlevel = level
                                    while(1):
                                        try:
                                            parent_header = current_headers[mlevel - 1]
                                            break

                                        except:
                                            mlevel -= 1
                                            continue
                                    
                                    mtext = []
                                    mtext.append(element_text.replace('\u00a0', ''))
                                    subheader_index = len(parent_header["subheader"]) - 1

                                    if mtext[0] != '':
                                        # If there is a table in paragraph, add table name to metadata
                                        if 'Table' in element_text and check_bold(element) and not ("Table of Contents " in element_text) :
                                            # If subheader is available
                                            try: 
                                                parent_header["subheader"][subheader_index]["tablename"].append(mtext)

                                            except:
                                                parent_header["tablename"].append(mtext)   

                                        # Else if there is just a paragraph, add paragraph
                                        else: 
                                            # If subheader is available 
                                            try: 
                                                parent_header["subheader"][subheader_index]["paragraph"].append(mtext)

                                            except:
                                                parent_header["paragraph"].append(mtext)

                            # If there is a table element
                            elif(element_name == 'table'): 
                                mlevel = level

                                # Get the parent header
                                while(1):
                                    try:
                                        parent_header = current_headers[mlevel - 1]
                                        break

                                    except:
                                        mlevel -= 1
                                        continue

                                table_data, table_bold, table_color = extract_table(element)
                                table_type = check_table_header(table_bold, table_color)
                                subheader_index = len(parent_header["subheader"]) - 1
                                
                                # If subheader is available
                                try:
                                    lentable = len(parent_header["subheader"][subheader_index]["table"])

                                    if table_type[0] == "undefined" and lentable > 0:
                                        for row in table_data:
                                            parent_header["subheader"][subheader_index]["table"][lentable-1].append(row) 

                                    else:
                                        parent_header["subheader"][len(parent_header["subheader"])-1]["table"].append(table_data)
                                        parent_header["subheader"][len(parent_header["subheader"])-1]["tabletype"].append(table_type)
                                
                                except:
                                    parent_header["table"].append(table_data)
                                    parent_header["tabletype"].append(table_type)

                    elif within_main_content:
                        # Loop all elements of a page html
                        header_index = -1
                        cur_header = ''
                        skip_this_section = False
                        # Raw text of the current section
                        Cur_Section_Data = {
                            'header': '',
                            'begin': False,
                            'first_texts': ''
                        }

                        for element in body_elements:
                            if skip_this_page: 
                                break

                            element_text = element.text
                            refined_element_text = element_text.replace('\u00a0', '').replace(' ', '').replace('\xa0', '').lower()
                            element_name = element.name
                            next_header, next_header_main_name       = get_next_header_in_hierarchy(header_index)
                            sub_element = element.find_all()
                            is_html_header = check_header(element)
                            is_header_in_text = refined_element_text and next_header_main_name and ((next_header_main_name.lower() in refined_element_text) or (refined_element_text in next_header_main_name.lower()))

                            if '4.2.1 Con' in next_header:
                                    print()
                            # If this is a miss-converted heading. Add to the current parent's subheader
                            if (element_name == 'ol' and is_header_in_text) or (element_name == 'ol' and is_html_header): 
                                # Initialize the list to hold detected headers in the current text
                                detected_headers = []

                                # Loop through the hierarchy to check for multiple continuous headers
                                for index in range(header_index, len(hierarchy)):
                                    next_header, next_header_main_name = get_next_header_in_hierarchy(index)
                                    if next_header_main_name and ((next_header_main_name.lower() in refined_element_text) or (refined_element_text in next_header_main_name.lower())) :
                                        detected_headers.append((next_header, index))

                                # Process each detected header
                                for detected_header, detected_index in detected_headers:
                                    header_index += 1
                                    cur_header = hierarchy[header_index]

                                    level, Cur_Section_Data, Tableofcontent = add_current_header_to_root(cur_header, current_headers, parent_header, sub_element, element_text, Tableofcontent)

                                skip_this_section = False  
                                
                            # If this element is a paragraph content
                            elif element_name == 'p' or element_name == 'ul':
                                if (check_useless_word(element, i, num_pages)): # Skip useless words
                                    continue
                                
                                # If this is a heading of content
                                if is_html_header or is_header_in_text: 
                                    # header_index += 1

                                    # cur_header = ''
                                    # if is_html_header:
                                    #     cur_header = element_text.replace('\u00a0','')
                                    # elif header_index < len(hierarchy):
                                    #     cur_header = hierarchy[header_index]
                                    
                                    # level, Cur_Section_Data, Tableofcontent = add_current_header_to_root(cur_header, current_headers, parent_header, sub_element, element_text, Tableofcontent)

                                    detected_headers = []
                                    # Loop through the hierarchy to check for multiple continuous headers
                                    for index in range(header_index, len(hierarchy)):
                                        next_header, next_header_main_name = get_next_header_in_hierarchy(index)
                                        if next_header_main_name and ((next_header_main_name.lower() in refined_element_text) or (refined_element_text in next_header_main_name.lower())) :
                                            detected_headers.append((next_header, index))

                                    # Process each detected header
                                    for detected_header, detected_index in detected_headers:
                                        header_index += 1
                                        if is_html_header:
                                            cur_header = element_text.replace('\u00a0','')
                                        elif header_index < len(hierarchy):
                                            cur_header = hierarchy[header_index]                                        
                                        level, Cur_Section_Data, Tableofcontent = add_current_header_to_root(cur_header, current_headers, parent_header, sub_element, element_text, Tableofcontent)

                                    skip_this_section = False

                                # If this is a paragraph content
                                else: 
                                    # Skip capturing data if the current section data is handled
                                    if skip_this_section:
                                        continue

                                    mlevel = level
                                    while(1):
                                        try:
                                            parent_header = current_headers[mlevel - 1]
                                            break

                                        except:
                                            mlevel -= 1
                                            continue
                                    
                                    mtext = []
                                    # If the element contains bullet data
                                    if element_name == 'ul':
                                        if Cur_Section_Data['first_texts'] == '':
                                           Cur_Section_Data['first_texts'] = element_text 
                                        element_text_main_content, skip_this_page = extract_bullet_data(cur_header, PyMuPDF_support_page_text, Cur_Section_Data)
                                        # Extract bullet data always handle all content of the current section, so then, skip this section
                                        skip_this_section = True

                                    # Else, element text does not contain bullet data
                                    else:
                                        element_text_main_content = element_text.replace('\u00a0', '')

                                    mtext.append(element_text_main_content)
                                    Cur_Section_Data['first_texts'] += mtext[-1]
                                    subheader_index = len(parent_header["subheader"]) - 1

                                    if mtext[0] != '':
                                        # If there is a table in paragraph, add table name to metadata
                                        if 'Table' in element_text and check_bold(element) and not ("Table of Contents " in element_text) :
                                            # If subheader is available
                                            try: 
                                                parent_header["subheader"][subheader_index]["tablename"].append(mtext)

                                            except:
                                                parent_header["tablename"].append(mtext)   

                                        # Else if there is just a paragraph, add paragraph
                                        else: 
                                            # If subheader is available 
                                            try: 
                                                parent_header["subheader"][subheader_index]["paragraph"].append(mtext)

                                            except:
                                                parent_header["paragraph"].append(mtext)
                        
                            # If there is a table element
                            elif(element_name == 'table'): 
                                mlevel = level

                                # Get the parent header
                                while(1):
                                    try:
                                        parent_header = current_headers[mlevel - 1]
                                        break

                                    except:
                                        mlevel -= 1
                                        continue

                                table_data, table_bold, table_color = extract_table(element)
                                table_type = check_table_header(table_bold, table_color)
                                subheader_index = len(parent_header["subheader"]) - 1
                                
                                # If subheader is available
                                element_text_main_content, skip_this_page = extract_bullet_data(cur_header, PyMuPDF_support_page_text)
                                post_process_table(cur_header, PyMuPDF_support_page_text, table_data)

                                try:
                                    lentable = len(parent_header["subheader"][subheader_index]["table"])

                                    if table_type[0] == "undefined" and lentable > 0:
                                        for row in table_data:
                                            parent_header["subheader"][subheader_index]["table"][lentable-1].append(row) 
                                            #Cur_Section_Data['text'] += row

                                    else:
                                        parent_header["subheader"][len(parent_header["subheader"])-1]["table"].append(table_data)
                                        parent_header["subheader"][len(parent_header["subheader"])-1]["tabletype"].append(table_type)
                                        #table_text = ' '.join(' '.join(item) for item in table_data)
                                        #Cur_Section_Data['text'] += table_text
                                
                                except:
                                    parent_header["table"].append(table_data)
                                    parent_header["tabletype"].append(table_type)
                                    #table_text = ' '.join(' '.join(item) for item in table_data)
                                    #Cur_Section_Data['text'] += table_text

            except UnicodeDecodeError:
                print("Error: Unable to decode the file with the specified encoding.")

        # Save handled data
        with open(folder_path + '/' + DocName + '.json', 'w') as f:
            json.dump(header, f)

        with open(folder_path + '/' + DocName + '.txt', 'w', encoding='utf-8') as file:
            file.write(Tableofcontent)


