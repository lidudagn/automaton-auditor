from src.graph import create_full_graph
from src.state import AgentState

graph = create_full_graph()
state = AgentState(repo_url='https://github.com/langchain-ai/langgraph', pdf_path='test_report.pdf', rubric_dimensions=[{'id': 'test', 'name': 'Test'}])
res = graph.invoke(state)
print("Type of res:", type(res))
print("Keys in res:", res.keys() if isinstance(res, dict) else dir(res))
if isinstance(res, dict):
    print("Evidences count:", sum(len(v) for v in res.get("evidences", {}).values()))
