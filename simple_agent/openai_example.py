
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    raise ValueError(
        "OPENAI_API_KEY not found in environment variables. "
        "Make sure you have a .env file with your API key."
    )

# Create a client object with your API key
client = OpenAI(api_key=OPENAI_API_KEY)

user_msg = 'In simple terms explain what is algebra, and give an example'

system_msg = 'You are a helpful assistant'

# Your messages remain the same
messages = [
    {"role": "system", "content": system_msg},
    {"role": "user", "content": user_msg}
]

# Use the new method to create the chat completion
# Note the change from `openai.ChatCompletion.create` to `client.chat.completions.create`
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=messages
)

# Accessing the response content has also changed
# The response is now an object, and the content is nested within it
print(response)
print(response.choices[0].message.content)