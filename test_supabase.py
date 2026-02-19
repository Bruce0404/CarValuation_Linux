import sys
import os
from loguru import logger

# Add project root to path
sys.path.append(os.getcwd())

from src.database.supabase_client import SupabaseManager
from src.models.car import CarListing

def run_supabase_test():
    """
    A standalone script to test Supabase connection and upsert logic.
    """
    logger.info("--- Starting Supabase Connection Test ---")

    # 1. Check for .env file
    if not os.path.exists('.env'):
        logger.error("`.env` file not found. Please create it and add your SUPABASE_URL and SUPABASE_KEY.")
        return

    # 2. Create some sample data
    # Using a unique link to ensure this test data doesn't conflict with real data.
    test_car = CarListing(
        source="supabase-test",
        external_id="test-001",
        title="[Test] Supabase Connect Test Car",
        link="https://example.com/test-car-dont-delete",
        year=2024,
        price=999.9,
        mileage="10公里", # Test the validator
        location="網路世界"
    )
    
    logger.info(f"Created test car object: {test_car.model_dump_json(indent=2)}")
    
    # 3. Attempt to connect and upsert
    try:
        logger.info("Initializing SupabaseManager...")
        manager = SupabaseManager()
        
        logger.info("Attempting to upsert test data to 'market_listings' table...")
        manager.batch_upsert_cars([test_car])
        
        logger.success("--- Supabase Connection Test Finished ---")
        logger.info("Please check your 'market_listings' table in Supabase to verify the data was inserted/updated.")

    except ValueError as e:
        logger.error(f"Initialization failed: {e}")
        logger.error("Please ensure your .env file has the correct SUPABASE_URL and SUPABASE_KEY.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during the test: {e}")

if __name__ == "__main__":
    run_supabase_test()
