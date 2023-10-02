import os
from PyPDF2 import PdfReader, PdfWriter
import subprocess 
import aspose.words as aw
from PyPDF2 import PdfReader, PdfWriter
from bs4 import BeautifulSoup
import json

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
                count = 0
                for num in sub_sub_element.split('.'):
                    if(len(num)==0):
                        continue
                    int(num)
                    count+=1
                if(count >0):
                    return True
            except:
                return False      
    return False 
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

def getLength(Document):
    if( Document.endswith('.pdf')):
        docname = Document
        pass
    elif ( Document.endswith('.docx')):
        docname = Document.replace('docx','pdf')
        convert_docx_to_pdf(Document,docname)
    elif ( Document.endswith('.pptx')):
        docname = Document.replace('pptx','pdf')
        convert_pptx_to_pdf(Document,docname)
    with open(docname, 'rb') as pdf_file:
        # Create a PdfFileReader object
        pdf_reader = PdfReader(pdf_file)
        # Get the number of pages in the PDF file
        num_pages = len(pdf_reader.pages)

        return num_pages

def Doc2MiddleData(Document):
    
    if( Document.endswith('.pdf')):
        docname = Document
        pass
    elif ( Document.endswith('.docx')):
        docname = Document.replace('docx','pdf')
        convert_docx_to_pdf(Document,docname)
    elif ( Document.endswith('.pptx')):
        docname = Document.replace('pptx','pdf')
        convert_pptx_to_pdf(Document,docname)
    with open(docname, 'rb') as pdf_file:
        # Create a PdfFileReader object
        pdf_reader = PdfReader(pdf_file)
        # Get the number of pages in the PDF file
        num_pages = len(pdf_reader.pages)
        # Print the number of pages
        # print(f"The PDF file has {num_pages} pages.")
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

        if not os.path.exists("../Temporaries/"):
            os.makedirs("../Temporaries/")

        Tableofcontent = ''
        current_headers = [header] 
        level = 1# Add an initial header as the root
        for i in range(num_pages):
            count =0
            output_file_path = os.path.join("../Temporaries/", f"output.pdf")
            output_pdf = PdfWriter()
            output_pdf.add_page(pdf_reader.pages[i]) 
            with open(output_file_path, 'wb') as output_file:
                output_pdf.write(output_file)
            doc = aw.Document(output_file_path)
            doc.save("../Temporaries/output.html")
           # read the text from the document  
            with open("../Temporaries/output.html", 'r') as file:
                html_content = file.read()
                soup = BeautifulSoup(html_content, 'html.parser')
                soup = soup.div
                # Find all elements in the <body> section
                body_elements = soup.find_all(recursive=False)
                for element in body_elements:
                    if(element.name == 'p'):
                        if (check_useless_word(element,i,num_pages)): 
                            continue
                        sub_element = element.find_all()
                        if(check_header(element)):
                            #Start create table of content
                            #if paragraph is header
                            for j in range (len(sub_element[0].text.split('.'))-1):
                                Tableofcontent +='\t'
                            Tableofcontent +=element.text.replace('\u00a0','') + '\n'
                            #End create
                            #Start create Json
                            level = len(sub_element[0].text.split('.'))
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
                            tabletype = check_table_header(table_bold,table_color)
                            lentable = len(parent_header["subheader"][len(parent_header["subheader"])-1]["table"])
                            if(check_table_header(table_bold,table_color)[0] == "undefined" and lentable > 0):
                                for row in table_data:
                                    parent_header["subheader"][len(parent_header["subheader"])-1]["table"][lentable-1].append(row) 
                            else:
                                parent_header["subheader"][len(parent_header["subheader"])-1]["table"].append(table_data)
                                parent_header["subheader"][len(parent_header["subheader"])-1]["tabletype"].append(check_table_header(table_bold,table_color))
                        except:
                            table_data, table_bold,table_color = extract_table(element)
                            parent_header["table"].append(table_data)
                            parent_header["tabletype"].append(check_table_header(table_bold,table_color))
            yield {}

    with open("../Temporaries/tmp.json", 'w') as file:
        json.dump(header, file)
    yield header
    return



