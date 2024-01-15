from io import BytesIO
import requests
import re

from html_text import extract_text

header = {'host': 'brainly.co.id', 'content-type': 'application/json; charset=utf-8',
          'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}


class Attachment:
    def __init__(self, url):
        self.url = url["url"]
        self.size = None  # Since we're not downloading the content, size is set to None

    def __repr__(self):
        return f"<[ type: attachment ]>"


class Answers:
    def __init__(self, json):
        self.content = clean_text(extract_text(json["content"]))
        self.attachments = [Attachment(x) for x in json["attachments"]]

    def __repr__(self):
        return f"<[ type Text {'& ATTACHMENT' if self.attachments else ''}]>"


class Question:
    def __init__(self, node):
        self.content = clean_text(extract_text(node["node"]["content"]))
        self.attachments = [Attachment(x) for x in node["node"]["attachments"]]

    def __repr__(self):
        return f"<( QUESTION:1 ATTACHMENT: {len(self.attachments)})>"


class Content:
    def __init__(self, json):
        self.question = Question(json)
        self.answers = [Answers(x) for x in json["node"]["answers"]["nodes"]]

    def __repr__(self):
        return f"<( QUESTION: 1 ANSWER:{len(self.answers)} )>"


def clean_text(text):
    text = re.sub(r'\\[^{}]+', '', text)
    # Remove LaTeX-style formatting
    text = re.sub(r'/tex|\[\/tex\]|\frac\{(.*?)\}\{(.*?)\}', '', text)
    # Remove any remaining curly braces
    text = re.sub(r'\{|\}', '', text)
    # Remove double backslashes
    #text = text.replace('\\\\', ' ')
    # Remove single backslashes
    #text = text.replace('\\', '')
    # Remove LaTeX commands like \LARGE, \bf, \sf
    #text = re.sub(r'\\LARGE|\\bf|\\sf', '', text)
    return text


def brainly(query: str, first: int, after=None) -> list[Content]:
    body = {'operationName': 'SearchQuery', 'variables': {'query': query, 'after': after, 'first': first},
            'query': 'query SearchQuery($query: String!, $first: Int!, $after: ID) {\n\tquestionSearch(query: $query, first: $first, after: $after) {\n\tedges {\n\t  node {\ncontent\n\t\tattachments{\nurl\n}\n\t\tanswers {\n\t\t\tnodes {\ncontent\n\t\t\t\tattachments{\nurl\n}\n}\n}\n}\n}\n}\n}\n'}
    req = requests.post("https://brainly.co.id/graphql/id", headers=header, json=body).json()
    return [Content(js) for js in req["data"]["questionSearch"]["edges"]]
