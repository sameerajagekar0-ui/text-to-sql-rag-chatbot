from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(google_api_key="AIzaSyBJC5eBEEUPUXPIYBevpj6iNpyi7euVEow")
print(llm.list_models())
