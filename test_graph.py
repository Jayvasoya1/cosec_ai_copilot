import sys
import uuid
from langchain_core.messages import HumanMessage
from app.graph.graph import graph

config = {"configurable": {"thread_id": str(uuid.uuid4())}}

# First, run a successful user command to populate the state
graph.invoke({
    "messages": [HumanMessage(content="add user jay with id 1")]
}, config)

# Now, run "set door configuration"
result = graph.invoke({
    "messages": [HumanMessage(content="set door configuration")]
}, config)

print("STATE:")
print("tasks:", result.get("tasks"))
print("missing_fields:", result.get("missing_fields"))
print("completed_results:", result.get("completed_results"))
print("response_status:", result.get("response_status"))
print("response_message:", result.get("response_message"))

