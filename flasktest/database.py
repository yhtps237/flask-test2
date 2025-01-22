import json
import mysql.connector as connector
import asyncssh
import aiomysql


class EjurnalModel:
    db_name: str
    profession_id: int
    course_id: int
    subject_id: int
    topic_id: int


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
            "nduinfo_eco",
            "nduinfo_sahiltest",
            "nduinfo_testucun",
            "nduinfo_art",
        ]

        converter = {
            "nduinfo_fizika": "Fizika-Riyaziyyat",
            "nduinfo_tebiet": "Təbiətşünaslıq və Kənd təsərrüfatı",
            "nduinfo_memarliq": "Memarlıq və Mühəndislik",
            "nduinfo_xarici_diller": "Xarici dillər",
            "nduinfo_pedaqoji": "Pedaqoji",
            "nduinfo_beynelxalq": "Beynəlxalq Münasibətlər və Hüquq",
            "nduinfo_beynelxalq_mekteb": "Beynəlxalq Məktəb",
            "nduinfo_eco_new": "İqtisadiyyat və İdarəetmə",
            "nduinfo_eco_2cikorpus": "İqtisadiyyat və İdarəetmə (Özəl)",
            "nduinfo_med_new": "Tibb",
            "nduinfo_tibbkolleci": "Tibb Kolleci",
            "nduinfo_texnikikollec": "Texniki Kollec",
            "nduinfo_magistratura": "Magistratura",
            "nduinfo_tarix_filologiya": "Tarix-Filologiya",
            "nduinfo_art": "İncəsənət",
            "nduinfo_incesenet": "İncəsənət",
            "nduinfo_tibbkolleci": "Tibb Kolleci",
            "nduinfo_texnikikollec": "Texniki Kollec",
            "nduinfo_musiqikolleci": "Müsuqi Kolleci",
        }
        result = [
            (item[0], converter.get(item[0], ""))
            for item in result
            if item[0] not in filter_out
        ]
        await cur.close()
        conn.close()
        ssh_tunnel.close()
        return result

    async def get_profession_names(self, db_name):
        ssh_tunnel, local_listener = await self.open_ssh_tunnel(
            database.ssh_e_jurnal_host,
            database.ssh_e_jurnal_port,
            database.ssh_e_jurnal_username,
            database.ssh_e_jurnal_password,
            "localhost",
            3306,
        )
        conn = await self._connect_ejurnal_db(local_listener.get_port(), db_name)

        cur = await conn.cursor()
        await cur.execute("select ixtisas_id, ixtisas_ad from ixtisas;")
        result = await cur.fetchall()
        await cur.close()
        conn.close()
        ssh_tunnel.close()
        return [i for i in result]

    async def get_course_names(self, db_name, profession_id):
        ssh_tunnel, local_listener = await self.open_ssh_tunnel(
            database.ssh_e_jurnal_host,
            database.ssh_e_jurnal_port,
            database.ssh_e_jurnal_username,
            database.ssh_e_jurnal_password,
            "localhost",
            3306,
        )
        conn = await self._connect_ejurnal_db(local_listener.get_port(), db_name)

        cur = await conn.cursor()
        await cur.execute(
            f"select kurs_id, kurs_ad from kurs where kurs_ixtisas={profession_id};"
        )
        result = await cur.fetchall()
        await cur.close()
        conn.close()
        ssh_tunnel.close()
        return [i for i in result]

    async def get_subject_names(self, db_name, course_id):
        ssh_tunnel, local_listener = await self.open_ssh_tunnel(
            database.ssh_e_jurnal_host,
            database.ssh_e_jurnal_port,
            database.ssh_e_jurnal_username,
            database.ssh_e_jurnal_password,
            "localhost",
            3306,
        )
        conn = await self._connect_ejurnal_db(local_listener.get_port(), db_name)

        cur = await conn.cursor()
        await cur.execute(
            f"select fenn_id, concat(fenn_ad, ' - ', fenn_tip) from fenn where fenn_kurs={course_id};"
        )
        result = await cur.fetchall()
        await cur.close()
        conn.close()
        ssh_tunnel.close()
        return [i for i in result]

    async def get_topic_names(self, db_name, subject_id):
        ssh_tunnel, local_listener = await self.open_ssh_tunnel(
            database.ssh_e_jurnal_host,
            database.ssh_e_jurnal_port,
            database.ssh_e_jurnal_username,
            database.ssh_e_jurnal_password,
            "localhost",
            3306,
        )
        conn = await self._connect_ejurnal_db(local_listener.get_port(), db_name)

        cur = await conn.cursor()
        await cur.execute(
            f"select movzu_id, concat(movzu_ad, ' - ', movzu_tarix) from movzu where movzu_fenn={subject_id};"
        )
        result = await cur.fetchall()
        await cur.close()
        conn.close()
        ssh_tunnel.close()
        return [i for i in result]

    async def get_profession_name_by_id(self, db_name, profession_id):
        ssh_tunnel, local_listener = await self.open_ssh_tunnel(
            database.ssh_e_jurnal_host,
            database.ssh_e_jurnal_port,
            database.ssh_e_jurnal_username,
            database.ssh_e_jurnal_password,
            "localhost",
            3306,
        )
        conn = await self._connect_ejurnal_db(local_listener.get_port(), db_name)

        cur = await conn.cursor()
        await cur.execute(
            f"select ixtisas_ad from ixtisas where ixtisas_id={profession_id};"
        )
        result = await cur.fetchone()
        await cur.close()
        conn.close()
        ssh_tunnel.close()
        return result[0]

    async def get_course_name_by_id(self, db_name, course_id):
        ssh_tunnel, local_listener = await self.open_ssh_tunnel(
            database.ssh_e_jurnal_host,
            database.ssh_e_jurnal_port,
            database.ssh_e_jurnal_username,
            database.ssh_e_jurnal_password,
            "localhost",
            3306,
        )
        conn = await self._connect_ejurnal_db(local_listener.get_port(), db_name)

        cur = await conn.cursor()
        await cur.execute(f"select kurs_ad from kurs where kurs_id={course_id};")
        result = await cur.fetchone()
        await cur.close()
        conn.close()
        ssh_tunnel.close()
        return result[0]

    async def get_subject_name_by_id(self, db_name, subject_id):
        ssh_tunnel, local_listener = await self.open_ssh_tunnel(
            database.ssh_e_jurnal_host,
            database.ssh_e_jurnal_port,
            database.ssh_e_jurnal_username,
            database.ssh_e_jurnal_password,
            "localhost",
            3306,
        )
        conn = await self._connect_ejurnal_db(local_listener.get_port(), db_name)

        cur = await conn.cursor()
        await cur.execute(f"select fenn_ad from fenn where fenn_id={subject_id};")
        result = await cur.fetchone()
        await cur.close()
        conn.close()
        ssh_tunnel.close()
        return result[0]

    async def get_topic_name_by_id(self, db_name, topic_id):
        ssh_tunnel, local_listener = await self.open_ssh_tunnel(
            database.ssh_e_jurnal_host,
            database.ssh_e_jurnal_port,
            database.ssh_e_jurnal_username,
            database.ssh_e_jurnal_password,
            "localhost",
            3306,
        )
        conn = await self._connect_ejurnal_db(local_listener.get_port(), db_name)

        cur = await conn.cursor()
        await cur.execute(
            f"""SELECT 
                    CONCAT(movzu_ad, ' - ', movzu_tarix, ' - ', COUNT(davamiyyet_id))
                    
                FROM
                    movzu
                        LEFT JOIN
                    davamiyyet ON davamiyyet_movzu = movzu_id
                WHERE movzu_id={topic_id};
                """
        )
        result = await cur.fetchone()
        await cur.close()
        conn.close()
        ssh_tunnel.close()
        return result[0]

    async def get_ejurnal_fields(self, db_name, ids):
        ssh_tunnel, local_listener = await self.open_ssh_tunnel(
            database.ssh_e_jurnal_host,
            database.ssh_e_jurnal_port,
            database.ssh_e_jurnal_username,
            database.ssh_e_jurnal_password,
            "localhost",
            3306,
        )
        conn = await self._connect_ejurnal_db(local_listener.get_port(), db_name)

        cur = await conn.cursor()
        sql_query = """
        SELECT pr.ixtisas_ad, cr.kurs_ad, sub.fenn_ad, 
        topic.movzu_ad, topic.movzu_id
        FROM ixtisas AS pr
        JOIN kurs AS cr ON cr.kurs_id = %s
        JOIN fenn AS sub ON sub.fenn_id = %s
        JOIN movzu AS topic ON topic.movzu_id = %s
        WHERE pr.ixtisas_id = %s
        """
        results = []
        for id_set in ids:
            await cur.execute(sql_query, id_set[:4])
            # Fetch results for each query execution
            result = await cur.fetchall()
            results.append([i for i in result[0]] + list(id_set[4:]))

        data = [item for item in results]
        await cur.close()
        conn.close()
        ssh_tunnel.close()
        return data

    async def delete_ejurnal_topic(self, db_name, topic_id):
        ssh_tunnel, local_listener = await self.open_ssh_tunnel(
            database.ssh_e_jurnal_host,
            database.ssh_e_jurnal_port,
            database.ssh_e_jurnal_username,
            database.ssh_e_jurnal_password,
            "localhost",
            3306,
        )
        conn = await self._connect_ejurnal_db(local_listener.get_port(), db_name)

        cur = await conn.cursor()
        sql_query = f"""
                    DELETE FROM movzu WHERE movzu_id = {topic_id}
                    """

        await cur.execute(sql_query)
        await conn.commit()

        await cur.close()
        conn.close()
        ssh_tunnel.close()
        return True

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
