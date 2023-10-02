import PyPDF2
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
        sub_element = sub_elements[0]
        sub_sub_element = sub_element.text.split(' ')[0]  
        try: 
            count = 0
            if '.' in sub_sub_element:
                for num in sub_sub_element.split('.'):
                    if(len(num)==0):
                        continue
                    int(num)
                    count+=1
                if(count >0):
                    return count,True
        except:
            return count, False      
    return 0, False 

def split_pdf(input_file, output_prefix, start_page,end_page,name):
    with open(input_file, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        writer = PyPDF2.PdfWriter()
        for page_num in range(start_page, end_page):
            page = reader.pages[page_num]
            writer.add_page(page)

        output_file = f"{output_prefix}{name}.pdf"
        count = 0
        while(1):
            if( os.path.exists(output_file)):
                count +=1
                output_file = f"{output_prefix}{name + str(count)}.pdf"  
                continue
                 
            with open(output_file, 'wb') as output:
                writer.write(output)
            print(f"Part {name} created: {output_file}")
            break
        
# Example usage
input_file = 'D:/Training/AI_for_MCAL/source_code/Knowledge_Transfer/dataset/AUTOSAR/AUTOSAR_SWS_ADCDriver.pdf'
output_prefix = 'D:/Training/AI_for_MCAL/source_code/Knowledge_Transfer/output'
num_pages_per_part = 100
with open(input_file, 'rb') as pdf_file:
    # Create a PdfFileReader object
    pdf_reader = PdfReader(pdf_file)
    # Get the number of pages in the PDF file
    num_pages = len(pdf_reader.pages)
    # Print the number of pages
    # print(f"The PDF file has {num_pages} pages.")
    level = 1# Add an initial header as the root
    start_page = 0
    end_page = 0
    count = 0
    for i in range(num_pages):

        output_file_path =Workspace_path +"/output.pdf"
        output_pdf = PdfWriter()
        output_pdf.add_page(pdf_reader.pages[i]) 
        with open(output_file_path, 'wb') as output_file:
            output_pdf.write(output_file)
        doc = aw.Document(output_file_path)
        doc.save(Workspace_path +"/output.html")
        # read the text from the document  
        try:
            with open(Workspace_path +"/output.html", 'r', encoding='utf-8') as file:
                html_content = file.read()
                soup = BeautifulSoup(html_content, 'html.parser')
                soup = soup.div
                # Find all elements in the <body> section
                body_elements = soup.find_all(recursive=False)
                
                for element in body_elements:
                    if(element.name == 'p'):
                        text = element.text
                        level, isHeader = check_header(element)
                        if(isHeader and level == 1):
                            if start_page ==0:
                                sectionname = element.text.replace('\xa0','')
                                start_page =i
                            else :
                                end_page = i
                        if start_page != 0 and end_page !=0:
                            count+=1
                            split_pdf(input_file, output_prefix +'/', start_page,end_page,sectionname.replace('/',''))
                            start_page = end_page
                            end_page = 0
                            sectionname = element.text.replace('\xa0','')
        except UnicodeDecodeError:
            print("Error: Unable to decode the file with the specified encoding.")
 
