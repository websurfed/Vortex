import Tokenizer
import Preprocessor

source = """
def a:
    b
       # STOP
    c
"""

processed = Preprocessor.preprocess(source)
result = Tokenizer.lex(processed)
for token in result:
    print(token)