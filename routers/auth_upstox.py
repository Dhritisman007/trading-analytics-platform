# routers/auth_upstox.py

import httpx
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

from core.config import settings

router = APIRouter(prefix="/auth/upstox", tags=["Upstox Auth"])


@router.get("/login")
def upstox_login():
    """
    Visit http://127.0.0.1:8000/auth/upstox/login in your browser.
    It redirects you to Upstox login page.
    After login, Upstox sends you back to /callback with a code.
    """
    auth_url = (
        "https://api.upstox.com/v2/login/authorization/dialog"
        f"?response_type=code"
        f"&client_id={settings.upstox_api_key}"
        f"&redirect_uri={settings.upstox_redirect_uri}"
    )
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def upstox_callback(code: str):
    """
    Upstox redirects here after login.
    Exchanges the code for an access token.
    Copy the token shown here into your .env file.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.upstox.com/v2/login/authorization/token",
            data={
                "code": code,
                "client_id": settings.upstox_api_key,
                "client_secret": settings.upstox_api_secret,
                "redirect_uri": settings.upstox_redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    data = response.json()
    token = data.get("access_token", "NOT FOUND — check credentials")

    # Show as HTML so you can copy it easily
    return HTMLResponse(f"""
        <h2>Upstox Access Token</h2>
        <p>Copy this into your .env as <code>UPSTOX_ACCESS_TOKEN</code></p>
        <textarea rows="4" cols="80">{token}</textarea>
        <br/><br/>
        <p>Token expires at midnight. You need to do this once per day.</p>
        <p>After updating .env, restart your server.</p>
    """)
