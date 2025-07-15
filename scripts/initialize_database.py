import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import initialize_database

if __name__ == '__main__':
    initialize_database()
    print('Database initialized successfully at data/nexus.db') 