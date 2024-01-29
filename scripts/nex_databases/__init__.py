from .mongodb_database import MongoDBDatabase
from .sqlite_database import SQLiteDatabase
from .neo4j_database import Neo4jDatabase
from .mysql_database import MySQLDatabase
from .postgres_database import PostgresDatabase


all_database_classes = [
    MongoDBDatabase,
    MySQLDatabase,
    Neo4jDatabase,
    PostgresDatabase,
    SQLiteDatabase,
]
