import asyncio
from datetime import date

import structlog

from app.db.session import SessionFactory, engine
from app.services.billing_engine import run_due_subscriptions

logger = structlog.get_logger(__name__)


async def main() -> None:
    async with SessionFactory() as session:
        invoices = await run_due_subscriptions(session, date.today())
        logger.info("scheduled_billing_completed", invoices_created=len(invoices))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
