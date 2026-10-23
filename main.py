import Tokenizer
import Preprocessor

source = "def add(a: int32, b: int32) -> int32:\n    return a + b\n"

processed = Preprocessor.preprocess(source)
result = Tokenizer.lex(processed)
for token in result:
    print(token)