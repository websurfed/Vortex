import Tokenizer
import Preprocessor

source = "\nx"

processed = Preprocessor.preprocess(source)
result = Tokenizer.lex(processed)
for token in result:
    print(token)