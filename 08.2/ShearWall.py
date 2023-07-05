from PySide6.QtCore import Qt, QPointF, QRect, QSize, QPoint
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtWidgets import QTabWidget, QGraphicsRectItem, QWidget, QPushButton, QDialog, QDialogButtonBox, \
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox

from pointer_control import beam_end_point, pointer_control_shearWall
from post_new import magnification_factor
from DeActivate import deActive
from beam_prop import lineLoad, pointLoad_line

from back.beam_control import beam_line_creator


class ShearWallButton(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.shearWall = QPushButton("SHEAR WALL")


class shearWallDrawing(QGraphicsRectItem):
    def __init__(self, shearWallButton, x, y, grid, scene, snapPoint, snapLine):
        super().__init__()
        self.shearWall = shearWallButton
        self.grid = grid
        self.scene = scene
        self.snapPoint = snapPoint
        self.snapLine = snapLine
        x_list, y_list = edit_spacing(x, y)

        self.x_grid = x_list
        self.y_grid = y_list
        self.current_rect = None
        self.start_pos = None
        self.direction = None
        self.interior_exterior = None
        self.line = None
        self.shearWall_select_status = 0  # 0: neutral, 1: select shearWall, 2: delete shearWall
        self.other_button = None
        self.shearWall_width = magnification_factor  # Set shearWall width, magnification = 1 ft or 1 m
        # self.shearWall_width = min(min(x), min(y)) / 12  # Set shearWall width
        self.post_dimension = min(min(x), min(y)) / 8  # Set post dimension

        # shearWall PROPERTIES
        # START / END
        self.shearWall_rect_prop = {}
        self.shearWall_number = 1
        self.shearWall_post_number = 1
        self.shearWall_loc = []  # for every single shearWall

    def draw_shearWall_mousePress(self, main_self, event):
        if event.button() == Qt.LeftButton:
            pos = main_self.mapToScene(event.position().toPoint())
            # snapped_pos = self.snap_to_grid(pos)
            snapped_pos = self.snapPoint.snap(pos)
            # if snap to some point we don't need to check with snap line
            if pos == snapped_pos:
                snapped_pos = self.snapLine.snap(pos)
            if self.shearWall_select_status == 2:
                item = main_self.itemAt(event.position().toPoint())

                # Check if the clicked item is a start or end rectangle
                main_rect = None
                for rect, rect_props in self.shearWall_rect_prop.items():
                    if item == rect_props["post"]["start_rect_item"] or item == rect_props["post"]["end_rect_item"]:
                        main_rect = rect
                        break

                # If the clicked item is a start or end rectangle, set the item to the main rectangle
                if main_rect is not None:
                    item = main_rect

                if isinstance(item, Rectangle):  # Finding shearWall
                    # Delete the coordinates of the rectangle
                    if item in self.shearWall_rect_prop:
                        # delete snap points (start & end)
                        self.snapPoint.remove_point(self.shearWall_rect_prop[item]["post"]["start_center"])
                        self.snapPoint.remove_point(self.shearWall_rect_prop[item]["post"]["end_center"])

                        # delete start and end rectangles
                        self.scene.removeItem(self.shearWall_rect_prop[item]["post"]["start_rect_item"])
                        self.scene.removeItem(self.shearWall_rect_prop[item]["post"]["end_rect_item"])

                        # delete item
                        del self.shearWall_rect_prop[item]

                    self.scene.removeItem(item)


            else:
                if self.current_rect:
                    snapped_pos = self.snapPoint.snap(pos)
                    # if snap to some point we don't need to check with snap line
                    if pos == snapped_pos:
                        snapped_pos = self.snapLine.snap(pos)
                    self.finalize_rectangle(pos, self.direction)
                    # Create a new rectangle instance
                    self.start_pos = snapped_pos
                    if self.shearWall_loc:  # Add this condition
                        end_point = snapped_pos.toTuple()
                        start_point = self.shearWall_loc[0]
                        final_end_point = beam_end_point(start_point, end_point)
                        self.shearWall_loc.append(final_end_point)
                        # self.shearWall_rect_prop[self.current_rect] = {"label": f"B{self.shearWall_number}",
                        #                                                "coordinate": [start_point, final_end_point]}

                        # Add Start and End shearWall point to Snap Point
                        self.snapPoint.add_point(self.shearWall_rect_prop[self.current_rect]["post"]["start_center"][0],
                                                 self.shearWall_rect_prop[self.current_rect]["post"]["start_center"][1])
                        self.snapPoint.add_point(self.shearWall_rect_prop[self.current_rect]["post"]["end_center"][0],
                                                 self.shearWall_rect_prop[self.current_rect]["post"]["end_center"][1])

                        self.current_rect = None
                        self.shearWall_loc.clear()

                else:
                    snapped_pos = self.snapPoint.snap(pos)
                    # if snap to some point we don't need to check with snap line
                    if pos == snapped_pos:
                        snapped_pos = self.snapLine.snap(pos)
                        # Start point just snap to point not line.
                    point = snapped_pos.toTuple()
                    x, y = point[0], point[1]
                    status, self.direction, self.interior_exterior, self.line = pointer_control_shearWall(x, y,
                                                                                                          self.grid)
                    if status:
                        self.start_pos = QPointF(x, y)

                        self.shearWall_loc.append(self.start_pos.toTuple())
                        if self.direction == "E-W":
                            y_rect = y - self.shearWall_width / 2
                            x_rect = x
                        else:
                            y_rect = y
                            x_rect = x - self.shearWall_width / 2

                        self.current_rect = Rectangle(x,
                                                      y, self.shearWall_rect_prop)
                        self.scene.addItem(self.current_rect)

    def draw_shearWall_mouseMove(self, main_self, event):
        if self.current_rect and (self.start_pos or self.start_pos == QPointF(0.000000, 0.000000)):
            pos = main_self.mapToScene(event.pos())
            # snapped_pos = self.snap_to_grid(pos)
            snapped_pos = self.snapPoint.snap(pos)
            # if snap to some point we don't need to check with snap line
            if pos == snapped_pos:
                snapped_pos = self.snapLine.snap(pos)
            width = snapped_pos.x() - self.start_pos.x()
            height = snapped_pos.y() - self.start_pos.y()

            if self.direction == "E-W":
                # Move horizontally, keep vertical dimension constant
                self.current_rect.setRect(min(self.start_pos.x(), snapped_pos.x()),
                                          self.start_pos.y() - self.shearWall_width / 2, abs(width),
                                          self.shearWall_width)
            else:
                # Move vertically, keep horizontal dimension constant
                self.current_rect.setRect(self.start_pos.x() - self.shearWall_width / 2,
                                          min(self.start_pos.y(), snapped_pos.y()), self.shearWall_width,
                                          abs(height))

    def finalize_rectangle(self, pos, direction):
        snapped_pos = self.snapPoint.snap(pos)
        # if snap to some point we don't need to check with snap line
        if pos == snapped_pos:
            snapped_pos = self.snapLine.snap(pos)
        width = snapped_pos.x() - self.start_pos.x()
        height = snapped_pos.y() - self.start_pos.y()

        if direction == "E-W":
            self.current_rect.setRect(min(self.start_pos.x(), snapped_pos.x()),
                                      self.start_pos.y() - self.shearWall_width / 2, abs(width), self.shearWall_width)
        else:
            self.current_rect.setRect(self.start_pos.x() - self.shearWall_width / 2,
                                      min(self.start_pos.y(), snapped_pos.y()), self.shearWall_width,
                                      abs(height))

        center_left = QPoint(self.current_rect.boundingRect().left(),
                             self.current_rect.boundingRect().top() + self.current_rect.boundingRect().height() // 2)
        center_right = QPoint(self.current_rect.boundingRect().right(),
                              self.current_rect.boundingRect().top() + self.current_rect.boundingRect().height() // 2)
        center_top = QPoint(self.current_rect.boundingRect().left() + self.current_rect.boundingRect().width() // 2,
                            self.current_rect.boundingRect().top())
        center_bottom = QPoint(self.current_rect.boundingRect().left() + self.current_rect.boundingRect().width() // 2,
                               self.current_rect.boundingRect().bottom())

        # Calculate the positions and sizes for the start and end rectangles
        if direction == "E-W":
            start_rect_pos = QPoint(center_left.x(), center_left.y() - self.current_rect.boundingRect().height() // 2)
            end_rect_pos = QPoint(center_right.x() - (magnification_factor / 2),
                                  center_right.y() - self.current_rect.boundingRect().height() // 2)
            rect_size = QSize((magnification_factor / 2), self.current_rect.boundingRect().height())

            # post points
            start_x = min(self.start_pos.toTuple()[0], snapped_pos.toTuple()[0])
            end_x = max(self.start_pos.toTuple()[0], snapped_pos.toTuple()[0])
            start = (start_x, self.start_pos.toTuple()[1])
            end = (end_x, self.start_pos.toTuple()[1])
            # magnification_factor / 4 : 1 ft / 4 = 3 in or 1 m / 4 = 25 cm
            post_start = (start_x + magnification_factor / 4, self.start_pos.toTuple()[1])
            post_end = (end_x - magnification_factor / 4, self.start_pos.toTuple()[1])

        else:
            start_rect_pos = QPoint(center_top.x() - self.current_rect.boundingRect().width() // 2, center_top.y())
            end_rect_pos = QPoint(center_bottom.x() - self.current_rect.boundingRect().width() // 2,
                                  center_bottom.y() - (magnification_factor / 2))
            rect_size = QSize(self.current_rect.boundingRect().width(), (magnification_factor / 2))

            # post points
            start_y = min(self.start_pos.toTuple()[1], snapped_pos.toTuple()[1])
            end_y = max(self.start_pos.toTuple()[1], snapped_pos.toTuple()[1])
            start = (self.start_pos.toTuple()[0], start_y)
            end = (self.start_pos.toTuple()[0], end_y)
            # magnification_factor / 4 : 1 ft / 4 = 3 in or 1 m / 4 = 25 cm
            post_start = (self.start_pos.toTuple()[0], start_y + magnification_factor / 4)
            post_end = (self.start_pos.toTuple()[0], end_y - magnification_factor / 4)

        # Create the start and end rectangles
        start_rect = QRect(start_rect_pos, rect_size)
        end_rect = QRect(end_rect_pos, rect_size)

        start_rect_item = QGraphicsRectItem(start_rect)
        end_rect_item = QGraphicsRectItem(end_rect)
        self.scene.addItem(start_rect_item)
        self.scene.addItem(end_rect_item)

        self.current_rect.setPen(QPen(QColor.fromRgb(245, 80, 80, 100), 2))
        self.current_rect.setBrush(QBrush(QColor.fromRgb(255, 133, 81, 100), Qt.SolidPattern))
        l = self.length(start, end)

        # After adding start_rect_item and end_rect_item to the scene
        self.shearWall_rect_prop[self.current_rect] = {"label": f"SW{self.shearWall_number}",
                                                       "coordinate": [start, end],
                                                       "length": l,
                                                       "post": {
                                                           "label_start": f"SWP{self.shearWall_post_number}",
                                                           "label_end": f"SWP{self.shearWall_post_number + 1}",
                                                           "start_rect_item": start_rect_item,
                                                           "end_rect_item": end_rect_item,
                                                           "start_center": post_start,
                                                           "end_center": post_end},
                                                       "direction": self.direction,
                                                       "interior_exterior": self.interior_exterior,
                                                       "line_label": self.line,
                                                       "thickness": "4 in",  # in
                                                       "load": {"point": [], "line": []}

                                                       }
        beam_line_creator(self.shearWall_rect_prop[self.current_rect])
        print(self.shearWall_rect_prop.values())
        self.shearWall_number += 1
        self.shearWall_post_number += 2

        # self.current_rect = None
        self.start_pos = None

    @staticmethod
    def length(start, end):
        x1 = start[0]
        x2 = end[0]
        y1 = start[1]
        y2 = end[1]
        l = (((y2 - y1) ** 2) + ((x2 - x1) ** 2)) ** 0.5
        return round(l, 2)

    # SLOT
    def shearWall_selector(self):
        if self.other_button:
            post, beam, joist, studWall = self.other_button
        if self.shearWall_select_status == 0:
            self.shearWall_select_status = 1
            self.shearWall.shearWall.setText("Draw Shear Wall")
            self.setCursor(Qt.CursorShape.UpArrowCursor)

            # DE ACTIVE OTHER BUTTONS
            if self.other_button:
                deActive(self, post, beam, joist, self, studWall)
        elif self.shearWall_select_status == 1:
            self.shearWall_select_status = 2
            self.shearWall.shearWall.setText("Delete Shear Wall")
            self.setCursor(Qt.CursorShape.ArrowCursor)

            # DE ACTIVE OTHER BUTTONS
            if self.other_button:
                deActive(self, post, beam, joist, self, studWall)
        elif self.shearWall_select_status == 2:
            self.shearWall_select_status = 0
            self.shearWall.shearWall.setText("SHEAR WALL")
            self.setCursor(Qt.CursorShape.ArrowCursor)

    # @staticmethod
    # def post_slot2():
    #     print("self.a")
    #     print(post_position)
    #     # print(self.postObject.Post_Position)


class Rectangle(QGraphicsRectItem):
    def __init__(self, x, y, rect_prop):
        super().__init__(x, y, 0, 0)
        self.setPen(QPen(Qt.blue, 2))  # Set the border color to blue
        self.setBrush(QBrush(Qt.transparent, Qt.SolidPattern))  # Set the fill color to transparent

        self.rect_prop = rect_prop
        self.shearWall_properties_page = None

    # CONTROL ON shearWall
    def mousePressEvent(self, event):
        center = self.boundingRect().center().toTuple()
        # properties page open
        if event.button() == Qt.RightButton:  # shearWall Properties page
            height = self.boundingRect().height() - 1  # ATTENTION: I don't know why but this method return height + 1
            width = self.boundingRect().width() - 1  # ATTENTION: I don't know why but this method return width + 1
            self.shearWall_properties_page = ShearWallProperties(self, self.rect_prop,
                                                                 self.scene())
            self.shearWall_properties_page.show()


class ShearWallProperties(QDialog):
    def __init__(self, rectItem, rect_prop, scene, parent=None):
        super().__init__(parent)
        self.direction = None
        self.rectItem = rectItem
        self.rect_prop = rect_prop
        self.thickness = None
        self.thickness_default = rect_prop[rectItem]["thickness"]
        print(rect_prop)

        # IMAGE
        self.scene = scene

        self.setWindowTitle("Shear Wall Properties")
        self.setMinimumSize(200, 400)

        v_layout = QVBoxLayout()

        self.tab_widget = QTabWidget()
        self.tab_widget.setWindowTitle("Object Data")
        self.button_box = button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept_control)  # Change from dialog.accept to self.accept
        self.button_box.rejected.connect(self.reject)  # Change from dialog.reject to self.reject

        self.create_geometry_tab()
        self.create_assignment_tab()
        self.lineLoad = lineLoad(self.tab_widget, self.rect_prop[self.rectItem])
        # self.pointLoad = pointLoad_line(self.tab_widget, self.rect_prop[self.rectItem])

        v_layout.addWidget(self.tab_widget)
        v_layout.addWidget(button_box)
        self.setLayout(v_layout)  # Change from dialog.setLayout to self.setLayout

    # Rest of the code remains the same

    # dialog.show()

    def accept_control(self):
        self.lineLoad.print_values()
        # self.pointLoad.print_values()
        self.accept()

    def create_geometry_tab(self):
        start = tuple([i / magnification_factor for i in self.rect_prop[self.rectItem]["coordinate"][0]])
        end = tuple([i / magnification_factor for i in self.rect_prop[self.rectItem]["coordinate"][1]])
        Post_start = tuple([i / magnification_factor for i in self.rect_prop[self.rectItem]["post"]["start_center"]])
        Post_end = tuple([i / magnification_factor for i in self.rect_prop[self.rectItem]["post"]["end_center"]])
        tab = QWidget()
        self.tab_widget.addTab(tab, f"Geometry")
        label0 = QLabel("Label")
        joistLabel = QLabel(self.rect_prop[self.rectItem]["label"])
        label1 = QLabel("Start")
        start_point = QLabel(f"{start}")
        label2 = QLabel("End")
        end_point = QLabel(f"{end}")

        post_start_label = QLabel("Post Start")
        post_start = QLabel(f'{Post_start}')
        post_start_name_label = QLabel("Post Start Label")
        post_start_name = QLabel(f'{self.rect_prop[self.rectItem]["post"]["label_start"]}')

        post_end_label = QLabel("Post End")
        post_end = QLabel(f'{Post_end}')
        post_end_name_label = QLabel("Post End Label")
        post_end_name = QLabel(f'{self.rect_prop[self.rectItem]["post"]["label_end"]}')

        # calc length
        l = self.length(start, end)
        label3 = QLabel("Length")
        length = QLabel(f"{l}")

        direction_label = QLabel("Direction")
        direction = QLabel(self.rect_prop[self.rectItem]["direction"])

        interior_exterior_label = QLabel("Interior/Exterior")
        interior_exterior = QLabel(self.rect_prop[self.rectItem]["interior_exterior"].upper())

        # LAYOUT
        h_layout0 = QHBoxLayout()
        h_layout0.addWidget(label0)
        h_layout0.addWidget(joistLabel)
        h_layout1 = QHBoxLayout()
        h_layout1.addWidget(label1)
        h_layout1.addWidget(start_point)
        h_layout1_1 = QHBoxLayout()
        h_layout1_1.addWidget(post_start_label)
        h_layout1_1.addWidget(post_start)
        h_layout1_1_1 = QHBoxLayout()
        h_layout1_1_1.addWidget(post_start_name_label)
        h_layout1_1_1.addWidget(post_start_name)
        h_layout2 = QHBoxLayout()
        h_layout2.addWidget(label2)
        h_layout2.addWidget(end_point)
        h_layout2_2 = QHBoxLayout()
        h_layout2_2.addWidget(post_end_label)
        h_layout2_2.addWidget(post_end)
        h_layout2_2_2 = QHBoxLayout()
        h_layout2_2_2.addWidget(post_end_name_label)
        h_layout2_2_2.addWidget(post_end_name)
        h_layout3 = QHBoxLayout()
        h_layout3.addWidget(label3)
        h_layout3.addWidget(length)
        h_layout4 = QHBoxLayout()
        h_layout4.addWidget(direction_label)
        h_layout4.addWidget(direction)
        h_layout5 = QHBoxLayout()
        h_layout5.addWidget(interior_exterior_label)
        h_layout5.addWidget(interior_exterior)

        v_layout = QVBoxLayout()
        v_layout.addLayout(h_layout0)
        v_layout.addLayout(h_layout1)
        v_layout.addLayout(h_layout2)
        v_layout.addLayout(h_layout1_1)
        v_layout.addLayout(h_layout1_1_1)
        v_layout.addLayout(h_layout2_2)
        v_layout.addLayout(h_layout2_2_2)
        v_layout.addLayout(h_layout3)
        v_layout.addLayout(h_layout4)
        v_layout.addLayout(h_layout5)
        tab.setLayout(v_layout)

    @staticmethod
    def length(start, end):
        x1 = start[0]
        x2 = end[0]
        y1 = start[1]
        y2 = end[1]
        l = (((y2 - y1) ** 2) + ((x2 - x1) ** 2)) ** 0.5
        return round(l, 2)

    def create_assignment_tab(self):
        tab = QWidget()
        self.tab_widget.addTab(tab, f"Assignments")
        label1 = QLabel("Shear Wall Thickness")
        self.thickness = thickness = QComboBox()
        thickness.addItems(["4 in", "6 in", "8 in"])
        self.thickness.setCurrentText(self.rect_prop[self.rectItem]["thickness"])
        self.button_box.accepted.connect(self.accept_control)  # Change from dialog.accept to self.accept
        self.button_box.rejected.connect(self.reject)  # Change from dialog.reject to self.reject
        self.thickness.currentTextChanged.connect(self.thickness_control)

        # LAYOUT
        h_layout1 = QHBoxLayout()
        h_layout1.addWidget(label1)
        h_layout1.addWidget(thickness)

        v_layout = QVBoxLayout()
        v_layout.addLayout(h_layout1)

        tab.setLayout(v_layout)
        # return self.direction
        # SLOT

    def thickness_control(self):
        self.thickness_default = self.thickness.currentText()
        self.rect_prop[self.rectItem]["thickness"] = self.thickness_default


def edit_spacing(x, y):
    x_list = [0]
    y_list = [0]
    for i in range(len(x)):
        x_list.append(sum(x[:i + 1]))
    for i in range(len(y)):
        y_list.append(sum(y[:i + 1]))
    return x_list, y_list
