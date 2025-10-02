from openai import OpenAI
client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")
import json
import random

def get_current_weather(location: str, unit: str = "celsius"):
    return f"The weather in {location} is Sunny and {random.randint(40, 80)} degrees."

messages = []

class Agent:
    def __init__(self, name, instructions, model, tools):
        self.name = name
        self.instructions = instructions
        self.messages = [
            {"role": "system", "content": self.instructions}
        ]
        self.model = model
        self.tools = tools
        
    def consolidate_context(self,messages):
        ## ask a language model to consolidate the context
        completion = client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[{"role": "user", "content": "Consolidate the following messages into a single message. Do not lose any information."+json.dumps(messages)}],
            tools=self.tools,
            tool_choice="auto"
        )
        ## recreate the messages list with the consolidated context
        messages = [
            {"role": "system", "content": self.instructions},
            {"role": "user", "content": completion.choices[0].message.content}
        ]
        return messages


    def prompt(self,messages):
        completion = client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=messages,
            tools=self.tools,
            tool_choice="auto"
        )
        print(completion.choices[0].message)
        result = completion.choices[0].message.content
        result = result.split("</think>")[1]
        print(result)
        ## handle tool calls if there are any 
        if completion.choices[0].message.tool_calls:
            print("Tool calls found")
            for tool_call in completion.choices[0].message.tool_calls:
                messages = self.handle_tool_call(tool_call,messages)
        
        
        return messages
    
    def handle_tool_call(self, tool_call,messages): # act
        for tool in self.tools:
            if tool.get("function").get("name") == tool_call.function.name:
                if tool_call.function.name == "get_current_weather":
                    tool_call_arguments = json.loads(tool_call.function.arguments)
                    result = get_current_weather(tool_call_arguments.get("location"), tool_call_arguments.get("unit"))
                messages.append({"role": "tool", "content": result})
                return messages

    def run(self, kickoff_message):
        self.messages.append({"role": "user", "content": kickoff_message})
        results = self.prompt(self.messages)
        self.messages = results
        return self.messages
    
    def agentic_run(self, kickoff_message):
        ## first run the kickoff message
        self.messages.append({"role": "user", "content": kickoff_message})
        results = self.prompt(self.messages)
        self.messages = results
        ## then run the agentic loop
        continue_flag = "yes"
        
        while continue_flag == "yes":
            messages = self.messages.copy() # observe 
            messages.append({"role": "user", "content": "Has the original kickoff prompt been completed, or should we continue? Respond with only yes (continue) or no (stop) with no other text."})
            results = self.prompt(messages) # decide
            continue_flag = results[-1].get("content").lower()
            if continue_flag == "no":
                break
            self.messages.append({"role": "user", "content": "Please continue with the original prompt."}) # decide
            results = self.prompt(self.messages)
            self.messages = results
        
        return self.messages
    
    
    
tools = [
    {
    "type": "function",
    "function": {
      "name": "get_current_weather",
      "description": "Get the current weather in a given location",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "The city and state, e.g. San Francisco, CA",
          },
          "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
        },
        "required": ["location"],
      },
    }
  }
]

agent = Agent(
    name="First-Mate Agent",
    instructions=f"""
    You are a helpful assistant that can use function tools to help the user.
    You can use the get_current_weather tool for real-time access to the weather.
    {tools}
    """,
    model="qwen/qwen3-32b",
    tools=tools
)

# agent.run("What's the weather like in Boston today?")
# print(agent.messages)

agent.agentic_run("What's the weather like in Boston, vs San Francisco, vs Tokyo, vs London vs Paris, vs Sydney, vs Beijing, vs Mumbai, vs Delhi, vs Seoul, vs Tokyo, vs London, vs Paris, vs Sydney, vs Beijing, vs Mumbai, vs Delhi, vs Seoul, vs Tokyo, vs London, vs Paris, vs Sydney, vs Beijing, vs Mumbai, vs Delhi, vs Seoul, vs Tokyo, vs London, vs Paris, vs Sydney, vs Beijing, vs Mumbai, vs Delhi, vs Seoul?")
print(agent.messages)