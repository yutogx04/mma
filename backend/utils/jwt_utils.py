import requests

def call_protected_api(request, url):
    """
    Call protected API with JWT token - exactly as in course
    """
    token = request.session.get('access_token')
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"http://127.0.0.1:8000/api/{url}/", 
        headers=headers
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        if response.status_code == 401:
            return _refresh_token_and_retry(request, url)
        return None

def _refresh_token_and_retry(request, url):
    refresh_token = request.session.get('refresh_token')
    
    if refresh_token:
        response = requests.post(
            "http://127.0.0.1:8000/api/token/refresh/",
            data={"refresh": refresh_token}
        )
        
        if response.status_code == 200:
            tokens = response.json()
            request.session['access_token'] = tokens['access']
            
            headers = {"Authorization": f"Bearer {tokens['access']}"}
            response = requests.get(
                f"http://127.0.0.1:8000/api/{url}/", 
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
    
    return None

def get_user_profile(request):
    token = request.session.get('access_token')
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    response = requests.get(
        "http://127.0.0.1:8000/api/auth/profile/",
        headers=headers
    )
    
    if response.status_code == 200:
        return response.json()
    return None