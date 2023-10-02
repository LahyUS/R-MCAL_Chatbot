##########################################################
# Text Generation Code
##########################################################
def clear_torch_cache():
    gc.collect()
    torch.cuda.empty_cache()

class Stream(transformers.StoppingCriteria):
    def __init__(self, callback_func=None):
        self.callback_func = callback_func

    def __call__(self, input_ids, scores) -> bool:
        if self.callback_func is not None:
            self.callback_func(input_ids[0])
        return False

class Iteratorize:

    """
    Transforms a function that takes a callback
    into a lazy iterator (generator).
    Adapted from: https://stackoverflow.com/a/9969000
    """

    def __init__(self, func, kwargs=None, callback=None):
        self.mfunc = func
        self.c_callback = callback
        self.q = Queue()
        self.sentinel = object()
        self.kwargs = kwargs or {}
        self.stop_now = False

        def _callback(val):
            self.q.put(val)

        def gentask():
            try:
                ret = self.mfunc(callback=_callback, **self.kwargs)
            except ValueError:
                pass
            except:
                traceback.print_exc()
                pass

            clear_torch_cache()
            self.q.put(self.sentinel)
            if self.c_callback:
                self.c_callback(ret)

        self.thread = Thread(target=gentask)
        self.thread.start()

    def __iter__(self):
        return self

    def __next__(self):
        obj = self.q.get(True, None)
        if obj is self.sentinel:
            raise StopIteration
        else:
            return obj

    def __del__(self):
        clear_torch_cache()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_now = True
        clear_torch_cache()

def decode(output_ids, skip_special_tokens=True):
    return tokenizer.decode(output_ids, skip_special_tokens)

def get_reply_from_output_ids(output_ids, input_ids):
    new_tokens = len(output_ids) - len(input_ids[0])
    reply = decode(output_ids[-new_tokens:], skip_special_tokens = True)

    # Prevent LlamaTokenizer from skipping a space
    if len(output_ids) > 0:
        if tokenizer.convert_ids_to_tokens(int(output_ids[-new_tokens])).startswith('▁'):
            reply = ' ' + reply

    return reply

class StoppingCriteriaSub(StoppingCriteria):

    def __init__(self, stops = [], encounters=1):
        super().__init__()
        self.stops = [stop.to("cuda") for stop in stops]

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor):
        for stop in self.stops:
            if torch.all((stop == input_ids[0][-len(stop):])).item():
                return True

        return False

def chat(prompt):
    stop_words = ["### Human", "Unhelpful answer:"]
    stop_words_ids = [tokenizer(stop_word, return_tensors='pt')['input_ids'].squeeze() for stop_word in stop_words]
    stopping_criteria_list = StoppingCriteriaList([StoppingCriteriaSub(stops=stop_words_ids)])

    input_ids = tokenizer(prompt, return_tensors='pt').input_ids
    input_ids = input_ids.to('cuda')
    eos_token_ids = [tokenizer.eos_token_id] if tokenizer.eos_token_id is not None else []

    generate_params = {}
    generate_params['inputs'] = input_ids
    generate_params['max_new_tokens'] = 2048
    generate_params['temperature'] = 0.7
    generate_params['top_p'] = 0.95
    generate_params['repetition_penalty'] = 1.15
    generate_params['eos_token_id'] = eos_token_ids
    generate_params['stopping_criteria'] = stopping_criteria_list

    def generate_with_callback(callback=None, **kwargs):
        kwargs['stopping_criteria'].append(Stream(callback_func=callback))
        clear_torch_cache()
        with torch.no_grad():
            model.generate(**kwargs)

    def generate_with_streaming(**kwargs):
        return Iteratorize(generate_with_callback, kwargs, callback=None)

    with generate_with_streaming(**generate_params) as generator:
        for output in generator:
            yield get_reply_from_output_ids(output, input_ids)
            if output[-1] in eos_token_ids:
                break

def chatNew(prompt, related_question_prompt, references):
    print("Start generating ----------------")
    result = ""

    stop_words = ["### Human", "Unhelpful answer:"]
    stop_words_ids = [tokenizer(stop_word, return_tensors='pt')['input_ids'].squeeze() for stop_word in stop_words]
    stopping_criteria_list = StoppingCriteriaList([StoppingCriteriaSub(stops=stop_words_ids)])

    input_ids = tokenizer(prompt, return_tensors='pt').input_ids
    input_ids = input_ids.to('cuda')
    eos_token_ids = [tokenizer.eos_token_id] if tokenizer.eos_token_id is not None else []

    generate_params = {}
    generate_params['inputs'] = input_ids
    generate_params['max_new_tokens'] = 2048
    generate_params['temperature'] = 0.7
    generate_params['top_p'] = 0.95
    generate_params['repetition_penalty'] = 1.15
    generate_params['eos_token_id'] = eos_token_ids
    generate_params['stopping_criteria'] = stopping_criteria_list

    def generate_with_callback(callback=None, **kwargs):
        kwargs['stopping_criteria'].append(Stream(callback_func=callback))
        clear_torch_cache()
        with torch.no_grad():
            model.generate(**kwargs)

    def generate_with_streaming(**kwargs):
        return Iteratorize(generate_with_callback, kwargs, callback=None)

    with generate_with_streaming(**generate_params) as generator:
        for output in generator:
            result = get_reply_from_output_ids(output, input_ids)
            yield result
            if output[-1] in eos_token_ids:
                break

    print("DONE GENERATE RESULT +++++++++++++++")

    related_question_prompt.replace('{answer}', result)

    if references is not None and len(references) > 0:
        result += "\n **Reference documents:**\n"
        for link in references:
            result += link + "\n"
        result += "<br>."
        yield result

    result += "\n **Related question:**\n"
    input_ids = tokenizer(related_question_prompt, return_tensors='pt').input_ids
    input_ids = input_ids.to('cuda')
    eos_token_ids = [tokenizer.eos_token_id] if tokenizer.eos_token_id is not None else []

    generate_params['inputs'] = input_ids
    generate_params['eos_token_id'] = eos_token_ids

    print("START GENERATE RELATED QUESTION ++++++")

    with generate_with_streaming(**generate_params) as generator:
        for output in generator:
            yield result + get_reply_from_output_ids(output, input_ids)
            if output[-1] in eos_token_ids:
                break

def basic_test(question, path):
    import sys
    sys.path.append(google_colab_path)

    import warnings
    warnings.filterwarnings("ignore")
    from _QnA import QnA
    qna = QnA()
    final_prompt = qna.generate_prompt(path,question,prompt)
    print(f"final_prompt: {final_prompt}")