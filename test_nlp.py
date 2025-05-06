import spacy
import langid

# Test spacy
nlp = spacy.load("en_core_web_sm")
text = "Apple is looking at buying U.K. startup for $1 billion"
doc = nlp(text)

print("Spacy test:")
for token in doc:
    print(token.text, token.pos_, token.dep_)

# Test langid
print("\nLangid test:")
language, confidence = langid.classify(text)
print(f"Language: {language}, Confidence: {confidence}")
