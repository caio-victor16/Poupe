import mysql.connector

from app.config import Config

def get_connection():

    connection = mysql.connector.connect(

        host=Config.HOST,

        user=Config.USER,

        password=Config.PASSWORD,

        database=Config.DATABASE

    )

    return connection