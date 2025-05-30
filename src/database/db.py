# src/database/db.py
import asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel
from contextlib import asynccontextmanager

from src.utils.logger import get_logger
from src.database.models import EspritData # <--- ADD THIS IMPORT
from src.utils.config_manager import ConfigManager # <--- ADD THIS IMPORT

log = get_logger(__name__)

DATABASE_URL = "sqlite+aiosqlite:///./nyxa.db"
engine = create_async_engine(DATABASE_URL, echo=True)

async def create_db_and_tables():
    log.info("Attempting to create database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    log.info("Database tables created or already exist.")

# --- NEW FUNCTION: Populate EspritData from JSON ---
async def populate_static_data():
    log.info("Checking to populate static EspritData...")
    config_manager = ConfigManager() # Instantiate ConfigManager
    esprits_data_from_json = config_manager.get_config('esprits') # Load data from esprits.json

    async with AsyncSessionLocal() as session:
        # Check if EspritData table is empty
        # We need to explicitly cast the count result to a scalar
        count_query = sa.select(sa.func.count()).select_from(EspritData)
        count = (await session.execute(count_query)).scalar_one()

        if count == 0:
            log.info("EspritData table is empty. Populating from esprits.json...")
            for esprit_id, esprit_dict in esprits_data_from_json.items():
                # Create an EspritData instance from each dictionary entry
                new_esprit = EspritData(
                    esprit_id=esprit_id, # Use the dictionary key as the esprit_id
                    name=esprit_dict['name'],
                    description=esprit_dict['description'],
                    rarity=esprit_dict['rarity'],
                    visual_asset_path=esprit_dict['visual_asset_path'],
                    base_hp=esprit_dict['base_hp'],
                    base_attack=esprit_dict['base_attack'],
                    base_defense=esprit_dict['base_defense'],
                    base_speed=esprit_dict['base_speed'],
                    # Use .get() with defaults for optional keys to prevent KeyError if not present
                    base_magic_resist=esprit_dict.get('base_magic_resist', 0),
                    base_crit_rate=esprit_dict.get('base_crit_rate', 0.0),
                    base_block_rate=esprit_dict.get('base_block_rate', 0.0),
                    base_dodge_chance=esprit_dict.get('base_dodge_chance', 0.0),
                    base_mana_regen=esprit_dict.get('base_mana_regen', 0),
                    base_mana=esprit_dict.get('base_mana', 0)
                )
                session.add(new_esprit)
            await session.commit()
            log.info(f"Populated EspritData table with {len(esprits_data_from_json)} entries.")
        else:
            log.info(f"EspritData table already contains {count} entries. Skipping population.")
# --- END NEW FUNCTION ---

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@asynccontextmanager
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
# --- END MODIFICATION ---