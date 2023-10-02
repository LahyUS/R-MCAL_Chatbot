import logging
import docx
import os
import json
from pdf2docx import Converter
from PyPDF2 import PdfReader, PdfWriter
import sys
from pdf2image import convert_from_path
import subprocess 
import aspose.words as aw
from PyPDF2 import PdfReader, PdfWriter
from bs4 import BeautifulSoup
from PIL import Image
import shutil
from tqdm import tqdm
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
if(OptionFlags == '--pptx'):
    for docdir in DocDirs:
        pptx_path = docdir
        docsub = docdir.split('/')# Replace with the actual path to your PPTX file
        pdf_path = Workspace_path + '/' + Docfolder + '/' + docsub[len(docsub)-1].split('.')[0] + '.pdf'
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
if not os.path.exists(folder_path): 
    os.makedirs(folder_path)
if not os.path.exists(folder_img_path): 
            os.makedirs(folder_img_path)
numdoc = len(DocDirs)
progress_bar = tqdm(total=numdoc, unit='iteration',colour="red")
progress_bar.set_postfix_str("\033[31m")
def generatejson(json,level):
    header={
        "level":[],
        "name":[],
        "pragraph":[],
        "table":[],
        "subheader":list()
    }

    header['subheader'] = json
    return header
def is_table_header(element):
    t_element =element.text
    sub_t_element=[]
    if '\xa0' in t_element and 'Table' not in t_element:
        sub_t_element = t_element.split('\xa0')
        
    return sub_t_element
def row_table(element):
    t_element =element.text
    sub_t_element=[]
    if '\xa0' in t_element:
        sub_t_element = t_element.split('\xa0')
    return sub_t_element
    
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
            #print((colorin4[0]))
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
                if '(' in sub_sub_element and ')' in sub_sub_element  :
                    return -1, True
                count = 0
                for num in sub_sub_element.split('.'):
                    if(len(num)==0):
                        continue
                    int(num)
                    count+=1
                if(count >0):
                    return count, True
            except:
                return 0, False      
    return 0, False 
def check_useless_word(element,i,num_pages):
    if (("Evaluation Only. Created with Aspose.Words. Copyright 2003-2023 Aspose Pty Ltd." in element.text)
        or ("Requirements on" in element.text) or ((str(i+1)+" of "+str(num_pages)) in element.text) 
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
def add_table(table_data, mlevel):
    while(1):
        try:
            parent_header = current_headers[mlevel - 1]
            break
        except:
            mlevel -= 1
            continue
    try:
        tabletype = 'horizontal'
        parent_header["subheader"][len(parent_header["subheader"])-1]["table"].append(table_data)
        parent_header["subheader"][len(parent_header["subheader"])-1]["tabletype"].append(tabletype)
    except:
        parent_header["table"].append(table_data)
        parent_header["tabletype"].append(tabletype)

    
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

for DocDir in DocDirs :

    LDocName = DocDir.split('/')
    DocName = LDocName[len(LDocName)-1].replace(".pdf",'')
    #cv = Converter(DocDir)
    # Open the PDF file in read-binary mode
    with open(DocDir, 'rb') as pdf_file:
        # Create a PdfFileReader object
        pdf_reader = PdfReader(pdf_file)
        # Get the number of pages in the PDF file
        num_pages = len(pdf_reader.pages)
        # Print the number of pages
        # print(f"The PDF file has {num_pages} pages.")

        doc = {
            "name":[],
            "version":[],
            "content":list()
        }
        doc['name'] = DocName
        doc['version'] = Docfolder
        header={
            "page":list(),
            "level":[],
            "name":[],
            "paragraph":list(),
            "table":list(),
            "tablename":list(),
            "tabletype":list(),
            "subheader":list()
        }

        log_err =""
        list_pages = list()

        Tableofcontent = ''
        current_headers = [header] 
        level = 1# Add an initial header as the root
        headerflag = False
        for i in range(num_pages):
            progress_bar.update(1/num_pages)
            count =0
            output_file_path = Workspace_path + '/' + "output.pdf"
            output_pdf = PdfWriter()
            output_pdf.add_page(pdf_reader.pages[i]) 
            with open(output_file_path, 'wb') as output_file:
                output_pdf.write(output_file)
            doc = aw.Document(output_file_path)
            doc.save(Workspace_path + '/' + "output.html")
           # read the text from the document  
            try:
                with open(Workspace_path + '/' + "output.html", 'r', encoding='utf-8') as file:
                    html_content = file.read()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    soup = soup.div
                    # Find all elements in the <body> section
                    body_elements = soup.find_all(recursive=False)
                    temp_tableheader = []
                
                    for element in body_elements:
                        if(element.name == 'p'):
                            if (check_useless_word(element,i,num_pages)): 
                                continue
                            sub_element = element.find_all()
                            text = element.text
                            
                            if(level != 0):
                                temp_level = level
                            level, isHeader = check_header(element)
                            if(level == -1):
                                if not headerflag:
                                    level = temp_level+1
                                    headerflag = True
                                elif(headerflag):
                                    level = temp_level
                            elif(level != 0) :
                                headerflag = False
                                    
                            if(check_bold(element) and not(isHeader) ):
                                temp_tableheader = is_table_header(element)
                                if(len(temp_tableheader) !=0 ):
                                    log_err+= "table error in page :" + str(i+1) +'\n'
                                    continue                                
                            if(isHeader):
                                #Start create table of content
                                #if paragraph is header
                                for j in range (level-1):
                                    Tableofcontent +='\t'
                                Tableofcontent +=element.text.replace('\u00a0','') + '\n'
                                #End create
                                #Start create Json
                                # level = len(sub_element[0].text.split('.'))
                                # Remove the indentation and store the name in the header dictionary
                                name = element.text.replace('\u00a0','')
                                # Create a new header dictionary for each line
                                new_header = {
                                    "page":str(i+1),
                                    "level": level,
                                    "name": name,
                                    "paragraph": [],
                                    "table": [],
                                    "tablename":[],
                                    "tabletype":[],
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
                                # Update the current headers list
                                current_headers = current_headers[:level]  # Remove all headers after the current level
                                current_headers.append(new_header)  # Add the new header to the list
                                
                            else:
                                mlevel = level
                                if mlevel == 0:
                                    mlevel = len(current_headers)
                                while(1):
                                    
                                    try:
                                        parent_header = current_headers[mlevel - 1]
                                        break
                                    except:
                                        mlevel -= 1
                                        continue
                                if 'Table' in element.text and check_bold(element) and not("Table of Contents " in element.text) :
                                    try:
                                        mtext=[]
                                        mtext.append(element.text.replace('\u00a0',''))
                                        parent_header["subheader"][len(parent_header["subheader"])-1]["tablename"].append(mtext)
                                    except:
                                        mtext=[]
                                        mtext.append(element.text.replace('\u00a0',''))
                                        parent_header["tablename"].append(mtext)     
                                else:  
                                    try:
                                        mtext=[]
                                        mtext.append(element.text.replace('\u00a0',''))
                                        parent_header["subheader"][len(parent_header["subheader"])-1]["paragraph"].append(mtext)
                                    except:
                                        mtext=[]
                                        mtext.append(element.text.replace('\u00a0',''))
                                        parent_header["paragraph"].append(mtext)
                        elif(element.name == 'table'):
                            mlevel = level
                            
                            while(1):
                                
                                try:
                                    parent_header = current_headers[mlevel - 1]
                                    break
                                except:
                                    mlevel -= 1
                                    continue
                            try:
                                table_data, table_bold,table_color = extract_table(element)
                                pass_check = False
                                if(len(temp_tableheader)!=0) and (len(temp_tableheader) == len(table_data[0])):
                                    table_data.insert(0,temp_tableheader)
                                    pass_check = True
                                    temp_tableheader = []
                                tabletype = check_table_header(table_bold,table_color)
                                lentable = len(parent_header["subheader"][len(parent_header["subheader"])-1]["table"])
                                if(check_table_header(table_bold,table_color)[0] == "undefined" and lentable > 0) and not pass_check :
                                    lenrow = len(parent_header["subheader"][len(parent_header["subheader"])-1]["table"][0][0])
                                    if( lenrow == len (table_data[0])):
                                        for row in table_data:
                                            parent_header["subheader"][len(parent_header["subheader"])-1]["table"][lentable-1].append(row) 
                                    else :
                                        parent_header["subheader"][len(parent_header["subheader"])-1]["table"].append(table_data)
                                        parent_header["subheader"][len(parent_header["subheader"])-1]["tabletype"].append(check_table_header(table_bold,table_color))
    
                                else:
                                    parent_header["subheader"][len(parent_header["subheader"])-1]["table"].append(table_data)
                                    parent_header["subheader"][len(parent_header["subheader"])-1]["tabletype"].append(check_table_header(table_bold,table_color))
                            except:
                                parent_header["table"].append(table_data)
                                parent_header["tabletype"].append(check_table_header(table_bold,table_color))
            except UnicodeDecodeError:
                print("Error: Unable to decode the file with the specified encoding.")
            
        with open(folder_path +'/' + DocName +'.json', 'w') as f:
                json.dump(header,f)
        print(Tableofcontent)
        with open(folder_path +'/' + DocName +'.txt', 'w') as file:
            file.write(Tableofcontent)
        with open(folder_path +'/' +"LOG_ERR_" +DocName +'.txt', 'w') as file:
            file.write(log_err)


