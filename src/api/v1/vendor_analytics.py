from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import requests
import json
from urllib.parse import quote

router = APIRouter()

class VisionUrlRequest(BaseModel):
    email: str

@router.post('/get-vison-url')
def get_vison_url(request: VisionUrlRequest):
    email = request.email
    secret_key = os.getenv("VISION_SECRET_KEY", "4608545fc18c8ed7ef90cb3838c014bb5362b73bfa14f9d539651b8d08470e2a")

    try:
        response = requests.post(
            "http://localhost:5000/api/third-party-login",
            json={
                "secret_key": secret_key,
                "email": email
            },
            headers={"Content-Type": "application/json"}
        )
        
        # In case the response is not valid JSON
        try:
            data = response.json()
        except Exception:
            raise HTTPException(status_code=500, detail="Invalid response from 3Avision")

        if data.get("status") == "success":
            user_data = data.get("user", {})
            user_param = quote(json.dumps(user_data))
            access_token = data.get("access_token", "")
            
            sso_url = f"http://localhost:3000/sso-auth?token={access_token}&user={user_param}&redirect=/dashboard_view"
            
            return {"ssoUrl": sso_url}
        else:
            raise HTTPException(status_code=401, detail="Unauthorized by 3Avision")
            
    except requests.RequestException:
        raise HTTPException(status_code=500, detail="Error connecting to 3Avision")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
