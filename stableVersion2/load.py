from PySide6.QtWidgets import QApplication, QMainWindow, QListWidgetItem, QFileDialog, QLineEdit, QComboBox
import json
import sys
import uuid

from tab_widget_2 import secondTabWidget, information_properties
from InformationSaver import InformationSaver


class Load:
    def __init__(self, mainPage):
        self.mainPage = mainPage
        self.data = None
        self.tabWidget = None
        self.line_edit_projectTitle = None
        self.line_edit_company = None
        self.line_edit_designer = None
        self.line_edit_client = None
        self.line_edit_comment = None
        self.unit_combo = None
        # InformationSaver.line_edit_projectTitle, InformationSaver.line_edit_company, InformationSaver.line_edit_designer, InformationSaver.line_edit_client, InformationSaver.line_edit_comment, InformationSaver.unit_combo = self.general_info_items

    def load_control(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        fileName, _ = QFileDialog.getOpenFileName(self.mainPage, "QFileDialog.getOpenFileName()", "",
                                                  'JSON Files (*.json)', options=options)
        if fileName:
            with open(fileName, 'r') as f:
                self.data = json.load(f)

            self.create_main_tab()
            set_toolBar(self.data, self.tabWidget.toolBar)
            drawing(self.data, self.tabWidget.grid)

    def create_main_tab(self):
        # Set Information Properties
        self.line_edit_projectTitle = QLineEdit(self.data["general_information"]["project_name"])
        InformationSaver.line_edit_projectTitle = self.line_edit_projectTitle
        self.line_edit_company = QLineEdit(self.data["general_information"]["company"])
        InformationSaver.line_edit_company = self.line_edit_company
        self.line_edit_designer = QLineEdit(self.data["general_information"]["designer"])
        InformationSaver.line_edit_designer = self.line_edit_designer
        self.line_edit_client = QLineEdit(self.data["general_information"]["client"])
        InformationSaver.line_edit_client = self.line_edit_client
        self.line_edit_comment = QLineEdit(self.data["general_information"]["comment"])
        InformationSaver.line_edit_comment = self.line_edit_comment
        self.unit_combo = QComboBox()
        self.unit_combo.addItem(self.data["general_information"]["unit_system"])
        self.unit_combo.setCurrentText(self.data["general_information"]["unit_system"])
        InformationSaver.unit_combo = self.unit_combo

        # set second tab features.
        general_properties = self.data["general_properties"]
        self.tabWidget = secondTabWidget(general_properties)


class drawing:
    def __init__(self, inputs, grids):
        self.tabData = inputs["tab"]
        self.grid = grids
        for i in range(len(grids)):
            grid = grids[i]
            tabData = self.tabData[str(i)]
            self.draw_post(grid, tabData)
            self.draw_beam(grid, tabData)
            self.draw_joist(grid, tabData)
            self.draw_shearWall(grid, tabData)
            self.draw_studWall(grid, tabData)
            self.draw_loadMap(grid, tabData)

    @staticmethod
    def draw_post(grid, data):
        for post in data["post"]:
            grid.post_instance.draw_post_mousePress(None, None, post)

    @staticmethod
    def draw_beam(grid, data):
        for beam in data["beam"]:
            grid.beam_instance.draw_beam_mousePress(None, None, beam)

    @staticmethod
    def draw_joist(grid, data):
        for joist in data["joist"]:
            grid.joist_instance.draw_joist_mousePress(None, None, joist)

    @staticmethod
    def draw_shearWall(grid, data):
        for shearWall in data["shearWall"]:
            grid.shearWall_instance.draw_shearWall_mousePress(None, None, shearWall)

    @staticmethod
    def draw_studWall(grid, data):
        for studWall in data["studWall"]:
            grid.studWall_instance.draw_studWall_mousePress(None, None, studWall)

    @staticmethod
    def draw_loadMap(grid, data):
        for loadMap in data["loadMap"]:
            grid.load_instance.draw_load_mousePress(None, None, loadMap)


class set_toolBar:
    def __init__(self, inputs, toolBar):
        self.toolBar = toolBar
        self.seismic_parameters = inputs["seismic_parameters"]
        self.load_set = inputs["load_set"]
        self.set_seismic_parameters()
        self.set_load_sets()

    def set_seismic_parameters(self):
        self.toolBar.spin_values = []
        for i, item in enumerate(self.seismic_parameters.values()):
            if i <= 6:
                self.toolBar.spin_values.append(item)
            else:
                self.toolBar.combo_values = [item]

    def set_load_sets(self):
        for Id, properties in self.load_set.items():
            load_data = {"name": list(properties.keys())[0], "properties": list(properties.values())[0]}
            self.toolBar.dialogPage2.all_set_load[Id] = {load_data["name"]: load_data["properties"]}
            item = QListWidgetItem(load_data["name"])
            self.toolBar.dialogPage2.listWidget.addItem(item)
