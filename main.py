import Tokenizer
import Preprocessor

source = """
x = 5
"""

processed = Preprocessor.preprocess(source)
result = Tokenizer.lex(processed)
for token in result:
    print(token)