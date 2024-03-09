import openpyxl
from openpyxl.styles.alignment import Alignment
import json


class Contingent:
    def __init__(self) -> None:
        self.workbook = openpyxl.Workbook()
        self.ws = self.workbook.active
        self.merge_cells("A1:AF1")
        self.merge_cells("A2:AF2")
        self.merge_cells("AD4:AF4")
        self.merge_cells("A6:AF6")

        self.create_headings()
        self.coordinates = self.read_data()

    def merge_cells(self, range: str):
        self.ws.merge_cells(range)

    def create_headings(self):
        for column in self.coordinates["columns"]:
            self.merge_cells(column["range"])
            self.ws[column["key"]].value = column["text"]
            self.ws[column["key"]].alignment = Alignment(
                horizontal="center", vertical="center", **column["kwargs"]
            )
        # ------------------------------------------------------------------------------------
        for column in self.coordinates["sub_columns"]:
            self.merge_cells(column["range"])
            self.ws[column["key"]].value = column["text"]
            self.ws[column["key"]].alignment = Alignment(
                horizontal="center", vertical="center", **column["kwargs"]
            )

    def read_data(self):
        with open("flasktest/modules/coordinates.json") as f:
            data = json.load(f.read())
        return data

    def save(self, name):
        self.workbook.save(f"{name}.xlsx")
