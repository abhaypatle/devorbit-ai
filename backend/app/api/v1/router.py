from fastapi import APIRouter

from app.api.v1 import ai, auth, clients, invoices, metrics, orders, subscriptions

router = APIRouter()
router.include_router(auth.router)
router.include_router(clients.router)
router.include_router(orders.router)
router.include_router(subscriptions.router)
router.include_router(ai.router)
router.include_router(invoices.router)
router.include_router(metrics.router)
