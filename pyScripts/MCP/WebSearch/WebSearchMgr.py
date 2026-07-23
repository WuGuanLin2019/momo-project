import ollama

def web_search(query:str):
    result = ollama.web_search(query)

    # print(f"搜索结果{result}")
    return str(result)