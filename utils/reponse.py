def success_response(data: dict, message: str):
    return {"data": data, "message": message, "status": "success"}

def error_response(message: str):
    return {"message": message, "status": "error"}

