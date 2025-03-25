from src.rag_chatbot.crawlers.custom_article import CustomArticleCrawler

crawler = CustomArticleCrawler()

url = "https://maximelabonne.substack.com/p/uncensor-any-llm-with-abliteration-d30148b7d43e"

doc = crawler.extract(url)
print(doc)