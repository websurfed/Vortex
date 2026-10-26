import Tokenizer
import Preprocessor

source = """
a:
    x
  # badly indented comment
    y
"""

processed = Preprocessor.preprocess(source)
result = Tokenizer.lex(processed)
for token in result:
    print(token)