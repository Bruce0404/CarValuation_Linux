import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import List
import asyncio
from datetime import datetime

from src.models.car import CarListing
from loguru import logger

class SupabaseManager:
    def __init__(self):
        load_dotenv()
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Supabase URL and Key must be set in .env file.")
        
        self.client: Client = create_client(url, key)
        logger.info("Supabase client initialized.")

    def batch_upsert_cars(self, cars: List[CarListing], table_name: str = "market_listings"):
        """
        Batch upserts a list of CarListing objects to a Supabase table.
        Handles datetime to string conversion for JSON serialization.
        """
        if not cars:
            logger.warning("Car list is empty, skipping upsert.")
            return

        try:
            # Convert Pydantic models to dicts
            data_to_upsert = [car.model_dump() for car in cars]

            # Convert datetime objects to ISO 8601 strings
            for record in data_to_upsert:
                if 'crawled_at' in record and isinstance(record['crawled_at'], datetime):
                    record['crawled_at'] = record['crawled_at'].isoformat()

            response = self.client.table(table_name).upsert(
                data_to_upsert,
                on_conflict="link"
            ).execute()
            
            if response.data:
                 logger.success(f"Successfully upserted {len(response.data)} records to '{table_name}'.")
            else:
                 logger.info("Upsert executed, but no new data was returned. This may be expected if all records already exist.")

        except Exception as e:
            logger.error(f"An error occurred during Supabase upsert: {e}")
            if hasattr(e, 'details'):
                logger.error(f"Error details: {e.details}")

