import asyncio
import json
import logging

import websockets
from sqlmodel import Session

from ..db import engine
from ..models.models import Token

WEBSOCKET_URI = "wss://pumpportal.fun/api/data"
SUBSCRIBE_MESSAGE = '{"method":"subscribeMigration"}'

logger = logging.getLogger(__name__)


async def ingest_tokens():
    """
    Connects to the WebSocket, listens for new tokens, and saves them to the database.
    """
    while True:
        try:
            async with websockets.connect(WEBSOCKET_URI) as websocket:
                logger.info("Connected to WebSocket.")
                await websocket.send(SUBSCRIBE_MESSAGE)
                logger.info("Subscribed to token migrations.")

                while True:
                    message = await websocket.recv()
                    logger.info(f"Received raw message: {message}") # Log raw message
                    try:
                        data = json.loads(message)
                        token_address = data.get("mint")

                        if token_address:
                            with Session(engine) as session:
                                # Check if token already exists to avoid duplicates
                                existing_token = session.query(Token).filter(Token.token_address == token_address).first()
                                if not existing_token:
                                    new_token = Token(token_address=token_address, status="Initial")
                                    logger.info(f"Attempting to save token: {token_address}") # New log message
                                    session.add(new_token)
                                    session.commit()
                                    logger.info(f"New token saved: {token_address}")

                    except json.JSONDecodeError:
                        logger.warning(f"Could not decode JSON: {message}")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")

        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"WebSocket connection closed: {e}. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"An unexpected WebSocket error occurred: {e}. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)
