import json
import mysql.connector as connector


class Database:
    def __init__(self, hostname, username, password, port=3306, database_name=None):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.database_name = database_name
        self.connection = None

    # def connect(self):
    #     self.connection = connector.connect(
    #         host=self.hostname, username=self.username, password=self.password
    #     )
    #     print(
    #         f"[+] Connected successfully to {self.username}@{self.hostname}:{self.port}"
    #     )

    # def disconnect(self):
    #     if self.connection:
    #         self.connection.close()
    #         print(
    #             f"[+] Disconnected successfully from {self.username}@{self.hostname}:{self.port}"
    #         )

    # def execute(self, query, params=None):
    #     if self.connection:
    #         with self.connection.cursor() as cursor:
    #             if params:
    #                 cursor.execute(query, values=params)
    #             else:
    #                 cursor.execute(query)

    #             result = cursor.fetchall()
    #         if result:
    #             return result


def connect_db(database: Database):
    connection = connector.connect(
        host=database.hostname, username=database.username, password=database.password
    )
    print(
        f"[+] Connected successfully to {database.username}@{database.hostname}:{database.port}"
    )

    return connection


def disconnect_db(connection: connector.MySQLConnection, database: Database):
    connection.close()
    print(
        f"[+] Disconnected successfully from {database.username}@{database.hostname}:{database.port}"
    )


def load_config(config_file="flasktest/config.json"):
    with open(config_file, encoding="utf-8") as f:
        data = json.load(f)

    return data


database = Database(**load_config()["database"])
