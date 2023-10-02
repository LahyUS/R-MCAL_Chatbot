# # Disable warning
import warnings
warnings.filterwarnings("ignore")

from time import time
from _QnA import QnA
from _utils import *

########### Generate prompt #################################
# prompt = """Use the following pieces of information to answer the instruction at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.
# {input}
# {history}
# ### Instruction: {question}
# ### Response:"""

prompt_for_common_query = '''### Instruction: AI Document Assistant
You are an AI Document assistant. User will you give you a task. Your goal is to complete the task as faithfully as you can.
Task: Response politely to the following user's query or question:
History: {history}
Information: {input}
Question: {question}
### Response:
'''

prompt_for_specific_inquiry = '''### Instruction: AI Document Assistant
You are a helpful AI Document assistant and you can understand any long document. Your goal is to obtain the following pieces of information to get your understand. Then answer the question at the end of the information pieces.
If you need more information in the previous context, please refer to the History part. Now read the following information pieces and answer the question:
History: {history}
Information: {input}
Question: {question}
### Response:
'''

relate_question_prompt = """Generate at least 2 questions that related to below conversation.
{history}
### Instruction: {question}
### Response: {answer}
### Related question:
"""
qna = QnA()

#questions = ['Hi guy', "What the hell", "What is CAN", "Keep going", "It's amazing",'Hi Tell me about What is ADC_init', 'Do ADC_init has related to it', 'could you explain more about it']
#questions = ['Hi guy', 'could you explain more about it']
questions = { 
"Hello" : False, 
"What is Renesas Generic Requirement Specification for Generation tool": False, 
"What is Device Driver Design": False,
"What is it?": True,
"Hello guy! how are you today?": False,
"Currently, I have 2 module of ADC. But it failed at the very first steps. I have to find other modules to replace. Could you provide me some?": False,
"Tell me more about the solution you mentioned earlier.": True,
"Could you provide me some ones that similar to those?": True,
"Regarding the project scope, could you clarify a few points?": False,
"does the requirement design phase relates to it?": True, 
"What are these, Give more example of those": True, 
"Compare AD vs UD": False,
"Hi, it is very interesting, could you say more about it?": True
}

questions = {"hello guy": False,
"How are you?": False,
"Compare AD vs UD": False,
"Hi, it is very interesting, could you say more about it?": True,
"What is Driver Functional Design ?": False,
"What is ADC_init?": False,
}


data = {'token': '2804bad6fe94a55f18b2b37e300919a5fd517b95aa81e95db574c0ba069a3740', 'question': 'what could you do?', 'path': 'internal/'}
#questions =  ["What is Unit Test and Integrated Test", "what is the difference between Integrated Test and Unit Test"]
dict_items = list(questions.items())
index = 1
for question, type in dict_items[1:]:
    previous_question, previous_type = dict_items[index-1]

    if "history" in data: history = data["history"]
    else: history = []

    if "path" in data: path = data["path"]
    else: path = ""
    
    print("\n\n####################################################################################\n")
    final_prompt, references, wkproduct_links, guideline_links, guidelines, conversation_type = qna.generate_prompt(path, question, prompt_for_common_query, prompt_for_specific_inquiry, history)

    completed_final_prompt = final_prompt 
    if conversation_type == True:
        additional_field_index = final_prompt.find(f"### Instruction:")
        if additional_field_index != -1:
            completed_final_prompt = final_prompt[:additional_field_index] + previous_question + "\n" + final_prompt[additional_field_index:]

    print(f"Question: {question}")
    print(f"Conversation Chain?: Infer:{conversation_type} - Ground Truth: {type}")
    index += 1

    print("############## FINAL PROMPT ##############")
    print(completed_final_prompt)

    # print("\n############## REFERENCE LINKS ##############")
    # for link in references:
    #     print(link)

    # print("\n############## WORKPRODUCT LINKS ##############")
    # for link in wkproduct_links:
    #      print(link)

    # print("\n############## GUIDELINE LINKS ##############")
    # for link in guideline_links:
    #     print(link)

    # print("\n############## GUIDELINE ##############")
    # for guideline in guidelines:
    #     print(guideline)


# from _correctSpelling import *
# from _classifyQuestion import *
# from _keyword import KEYWORD

# correcter = CORRECT_SPELLING()
# ClassifyQuestion = CLASSIFY_QUESTION()
# Keyword = KEYWORD()

# #question = "Hello guys!"
# greeting_words = ['hello guys','Hi What is ADC', 'hi', 'hmm', 'holy', 'oh', 'wow', 'oops', 'ah', 'haha', 'great', 'aw']
# intj = []
# keys = []
# classify = []

# for question in greeting_words:
#     corrected = correcter.run(question)
#     intj.append(corrected)

#     keyword = Keyword.get_key_query(corrected)
#     keys.append(keyword)

#     index_type = ClassifyQuestion.run(keyword)
#     classify.append(index_type)

# print()


##############################################################

########### External file chat ###############################
# import json
# json_path = '/home/banvien/PROJECT/Work/Chatbot/code/MCAL_BOT/tmp.json'
# with open(json_path, 'r') as file:
#     json_data = json.load(file)
# qna = QnA()
# ## Save external file
# qna.save_external_files(json_data,'external/id123','abc.pdf')
# ## Delete external file
# qna.delete_external_files('external/id123')
##############################################################

########## Correct spelling ##################################
# from _correctSpelling import CORRECT_SPELLING
# correct = CORRECT_SPELLING()
# questions = ['Tell me about adc',
#              'What is the rentranc of can_getversion']
# for question in questions:
#     print(correct.run(question))
##############################################################