import Tokenizer
import Preprocessor

source = "\n\t\nx"

processed = Preprocessor.preprocess(source)
result = Tokenizer.lex(processed)
for token in result:
    print(token)