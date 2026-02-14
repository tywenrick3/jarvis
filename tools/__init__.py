from tools import bash, read_file, search_web, web_fetch, write_file

_modules = [bash, read_file, search_web, web_fetch, write_file]

TOOLS = [m.schema for m in _modules]

_registry = {m.schema["name"]: m.execute for m in _modules}


def execute_tool(name: str, input: dict) -> str:
    func = _registry.get(name)
    if func is None:
        return f"Unknown tool: {name}"
    return func(**input)
