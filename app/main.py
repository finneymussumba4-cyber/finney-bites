from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import APP_NAME, BUSINESS_SETTINGS
from app.routers import categories, products, auth, admin, orders, engagement, customers

app = FastAPI(
    title=APP_NAME,
    description="FINNEY BITES Fast Food Management API",
    version="1.0.0"
)

# Register API routers
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(orders.router)
app.include_router(engagement.router)
app.include_router(customers.router)


@app.get("/api/health")
async def health():
    return {
        "status": "success",
        "message": "FINNEY BITES backend is running"
    }


@app.get("/api/settings")
async def get_settings():
    return BUSINESS_SETTINGS


# Serve the website frontend
app.mount(
    "/",
    StaticFiles(directory="public", html=True),
    name="public"
)

