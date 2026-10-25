import Tokenizer
import Preprocessor

source = "a:\n    x\n    # note\n    y"

processed = Preprocessor.preprocess(source)
result = Tokenizer.lex(processed)
for token in result:
    print(token)