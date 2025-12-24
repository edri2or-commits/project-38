"""Railway Ephemeral Identity Broker"""
import os, json, asyncio, logging
from playwright.async_api import async_playwright
from google.cloud import secretmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RailwayIdentityBroker:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.secret_client = secretmanager.SecretManagerServiceClient()
    
    async def bootstrap_railway_token(self) -> str:
        logger.info("🚂 Railway Bootstrap...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
            page = await (await browser.new_context()).new_page()
            try:
                await page.goto('https://railway.app/login')
                await page.click('button:has-text("Sign in with GitHub")')
                await page.wait_for_url('**/dashboard**', timeout=30000)
                await page.goto('https://railway.app/account/tokens')
                await page.click('button:has-text("Create Token")')
                await page.fill('input[placeholder*="Token name"]', f"auto-{os.getenv('GITHUB_RUN_ID')}")
                await page.click('button:has-text("Create")')
                token = await (await page.query_selector('[data-testid="token-value"]')).inner_text()
                
                secret_name = f"projects/{self.project_id}/secrets/railway-api-token"
                try:
                    self.secret_client.create_secret(
                        request={"parent": f"projects/{self.project_id}", 
                                "secret_id": "railway-api-token",
                                "secret": {"replication": {"automatic": {}}}}
                    )
                except: pass
                self.secret_client.add_secret_version(
                    request={"parent": secret_name, 
                            "payload": {"data": token.encode('utf-8')}}
                )
                return token
            finally:
                await browser.close()

async def main():
    broker = RailwayIdentityBroker(os.getenv('GCP_PROJECT_ID', 'project-38-ai'))
    try:
        token = await broker.bootstrap_railway_token()
        print(json.dumps({"success": True, "token_prefix": token[:10]}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
