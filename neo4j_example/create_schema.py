from src.db import get_driver, DATABASE
from src.schema import create_schema

if __name__ == "__main__":
    driver = get_driver()
    try:
        create_schema(driver, DATABASE)
    finally:
        driver.close()
