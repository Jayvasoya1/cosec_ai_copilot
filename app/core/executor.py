from app.services.api_builder import build_url
from app.services.device_api import call_device_api
from app.config import USE_MOCK

def execute_task(route_data):
    if "need_input" in route_data:
        return route_data

    if "error" in route_data:
        return route_data

    url = build_url(route_data["group"], route_data["params"])

    if USE_MOCK:
        return {
            "url": url,
            "message": f"Executed: {route_data['params']}"
        }

    response = call_device_api(url)

    return {
        "url": url,
        "response": response
    }


def execute_tasks(tasks, router):
    results = []

    for task in tasks:
        route_data = router(task)

        result = execute_task(route_data)

        # 🔥 stop if need user input
        if "need_input" in result:
            return [result]

        results.append(result)

    return results