import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("Starting integration tests...")
    
    # 1. Register a new user
    register_url = f"{BASE_URL}/auth/register"
    register_payload = {
        "username": "tourist_fan",
        "email": "tourist_fan@example.com",
        "codeforces_handle": "tourist",
        "password": "Password123"
    }
    
    print(f"Registering user 'tourist_fan' and triggering Codeforces sync for handle 'tourist'...")
    try:
        response = requests.post(register_url, json=register_payload)
        print(f"Registration status code: {response.status_code}")
        print(f"Registration response: {response.text}")
        if response.status_code != 201:
            print("Error: Registration failed.")
            sys.exit(1)
    except Exception as e:
        print(f"Connection error to {register_url}: {e}")
        sys.exit(1)
        
    # 2. Login to get token
    login_url = f"{BASE_URL}/auth/login"
    login_payload = {
        "username": "tourist_fan",
        "password": "Password123"
    }
    
    print("\nLogging in to get JWT token...")
    response = requests.post(login_url, json=login_payload)
    print(f"Login status code: {response.status_code}")
    if response.status_code != 200:
        print("Error: Login failed.")
        sys.exit(1)
        
    login_data = response.json()
    token = login_data["access_token"]
    print(f"JWT Token acquired successfully (length {len(token)})")
    
    # Headers for authenticated requests
    auth_headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 3. Call /auth/me
    me_url = f"{BASE_URL}/auth/me"
    print("\nFetching current user details from /auth/me...")
    response = requests.get(me_url, headers=auth_headers)
    print(f"Me status code: {response.status_code}")
    print(f"Me response: {response.text}")
    assert response.json()["username"] == "tourist_fan"
    
    # 4. Fetch protected analytics data for tourist
    analytics_url = f"{BASE_URL}/analytics/tourist"
    print("\nFetching protected Codeforces analytics for handle 'tourist'...")
    response = requests.get(analytics_url, headers=auth_headers)
    print(f"Analytics status code: {response.status_code}")
    print(f"Analytics response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert response.json()["handle"].lower() == "tourist"
    
    # 5. Fetch rating history for tourist
    ratings_url = f"{BASE_URL}/ratings/tourist"
    print("\nFetching protected rating history for handle 'tourist'...")
    response = requests.get(ratings_url, headers=auth_headers)
    print(f"Ratings status code: {response.status_code}")
    assert response.status_code == 200
    print(f"Successfully retrieved rating history logs (found {len(response.json())} contests)")

    print("\nAll integration tests passed successfully!")

if __name__ == "__main__":
    run_tests()
