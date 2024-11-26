import json
import mysql.connector as connector
import asyncssh
import aiomysql


class Database:
    def __init__(self, hostname, username, password, port=3306, database_name=None):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.database_name = database_name

        self.ssh_e_jurnal_host = "94.20.43.43"
        self.ssh_e_jurnal_port = 2002
        self.ssh_e_jurnal_username = "root"
        self.ssh_e_jurnal_password = "G@hjkm001!@#$"

        self.connection = None

    async def open_ssh_tunnel(
        self, ssh_host, ssh_port, ssh_user, ssh_password, remote_host, remote_port
    ):
        conn = await asyncssh.connect(
            ssh_host,
            port=ssh_port,
            username=ssh_user,
            password=ssh_password,
            known_hosts=None,
        )
        listener = await conn.forward_local_port("", 0, remote_host, remote_port)
        return conn, listener

    async def _connect_ejurnal_db(self, port, name=None):
        if name is None:

            conn = await aiomysql.connect(
                host="127.0.0.1", port=port, user="nduict", password="old_school1967!"
            )
        else:
            conn = await aiomysql.connect(
                host="127.0.0.1",
                port=port,
                db=name,
                user="nduict",
                password="old_school1967!",
            )
        return conn

    async def get_faculty_names(self):
        ssh_tunnel, local_listener = await self.open_ssh_tunnel(
            database.ssh_e_jurnal_host,
            database.ssh_e_jurnal_port,
            database.ssh_e_jurnal_username,
            database.ssh_e_jurnal_password,
            "localhost",
            3306,
        )
        conn = await self._connect_ejurnal_db(local_listener.get_port())

        cur = await conn.cursor()
        await cur.execute("SHOW DATABASES;")
        result = await cur.fetchall()
        filter_out = [
            "information_schema",
            "mysql",
            "performance_schema",
            "sys",
            "nduinfo_web",
            "nduinfo_arxiv",
        ]
        result = [(item[0], item[0]) for item in result if item[0] not in filter_out]
        await cur.close()
        conn.close()
        ssh_tunnel.close()
        return result

    async def get_attendance(self, faculty_name, start_date, end_date):
        ssh_tunnel, local_listener = await database.open_ssh_tunnel(
            database.ssh_e_jurnal_host,
            database.ssh_e_jurnal_port,
            database.ssh_e_jurnal_username,
            database.ssh_e_jurnal_password,
            "localhost",
            3306,
        )
        conn = await database._connect_ejurnal_db(
            local_listener.get_port(), faculty_name
        )

        cur = await conn.cursor()

        await cur.execute(
            f"""
            SELECT COUNT(*) 
            FROM information_schema.columns
            WHERE table_schema = '{faculty_name}'
            AND table_name = 'istifadeci'
            AND column_name = 'istifadeci_soyad';
        """
        )
        row = await cur.fetchone()  # Await the coroutine to get the actual result
        if row:  # Check if the result is not None
            column_exists = row[0] > 0
        else:
            column_exists = False  # Handle the case where no rows are returned

        if column_exists:
            query = f"""
            SELECT 
                pr.ixtisas_ad,
                cr.kurs_ad,
                sub.fenn_ad,
                CONCAT(ist.istifadeci_ad, " ", ist.istifadeci_soyad) AS full_name,
                topic.movzu_ad,
                std.telebe_ad_soyad,
                davamiyyet_serbesti_is,
                davamiyyet_kollegiyum,
                davamiyyet_kursis,
                davamiyyet_qiymet,
                davamiyyet_tipi,
                davamiyyet_tarix
            FROM
                `davamiyyet`
            JOIN
                ixtisas AS pr ON pr.ixtisas_id = davamiyyet_ixtisas
            JOIN
                kurs AS cr ON cr.kurs_id = davamiyyet_kurs
            JOIN
                telebe AS std ON std.telebe_id = davamiyyet_telebe
            JOIN
                fenn AS sub ON sub.fenn_id = davamiyyet_fenn
            JOIN
                movzu AS topic ON topic.movzu_id = davamiyyet_movzu
            JOIN
                yonlendirme AS yon ON yon.yonlendirme_fenn_id = sub.fenn_id
            JOIN
                istifadeci AS ist ON ist.istifadeci_mail = yon.yonlendirme_mail
            WHERE
                davamiyyet_tarix BETWEEN '{start_date}' AND '{end_date}';
            """
        else:
            query = f"""
            SELECT 
                pr.ixtisas_ad,
                cr.kurs_ad,
                sub.fenn_ad,
                ist.istifadeci_ad AS full_name,
                topic.movzu_ad,
                std.telebe_ad_soyad,
                davamiyyet_serbesti_is,
                davamiyyet_kollegiyum,
                davamiyyet_kursis,
                davamiyyet_qiymet,
                davamiyyet_tipi,
                davamiyyet_tarix
            FROM
                `davamiyyet`
            JOIN
                ixtisas AS pr ON pr.ixtisas_id = davamiyyet_ixtisas
            JOIN
                kurs AS cr ON cr.kurs_id = davamiyyet_kurs
            JOIN
                telebe AS std ON std.telebe_id = davamiyyet_telebe
            JOIN
                fenn AS sub ON sub.fenn_id = davamiyyet_fenn
            JOIN
                movzu AS topic ON topic.movzu_id = davamiyyet_movzu
            JOIN
                yonlendirme AS yon ON yon.yonlendirme_fenn_id = sub.fenn_id
            JOIN
                istifadeci AS ist ON ist.istifadeci_mail = yon.yonlendirme_mail
            WHERE
                davamiyyet_tarix BETWEEN '{start_date}' AND '{end_date}';
            """

        await cur.execute(query)
        result = await cur.fetchall()
        result = [item for item in result]
        await cur.close()
        conn.close()
        ssh_tunnel.close()
        return result

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
