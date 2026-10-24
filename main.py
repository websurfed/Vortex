import Tokenizer
import Preprocessor

source = "def add(a, b):\n    return a + b"

processed = Preprocessor.preprocess(source)
result = Tokenizer.lex(processed)
for token in result:
    print(token)