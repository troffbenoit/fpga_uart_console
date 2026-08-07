# This Python file uses the following encoding: utf-8
import sys
# This Python file uses the following encoding: utf-8
import sys
import serial
from serial.tools import list_ports

from PySide6.QtWidgets import QApplication, QWidget

from ui_form import Ui_Widget


class Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Widget()
        self.ui.setupUi(self)

        for port in list_ports.comports():
            self.ui.portComboBox.addItem(port.device)

        self.ui.pushButton.clicked.connect(self.test_fpga)

    def test_fpga(self):
        port_name = self.ui.portComboBox.currentText()

        if not port_name:
            self.ui.label.setText("FPGA: No Port Selected")
            return

        try:
            with serial.Serial(port_name, 115200, timeout=2) as port:
                data = port.read(1)

            if data == b"A":
                self.ui.label.setText("FPGA: Connected")
            else:
                self.ui.label.setText("FPGA: No Response")

        except serial.SerialException:
            self.ui.label.setText("FPGA: Serial Error")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec())
from serial.tools import list_ports

from PySide6.QtWidgets import QApplication, QWidget

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_Widget

class Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Widget()
        self.ui.setupUi(self)
        for port in list_ports.comports():
            self.ui.portComboBox.addItem(port.device)

            def test_fpga(self):
                port_name = self.ui.portComboBox.currentText()

                if not port_name:
                    self.ui.label.setText("FPGA: No Port Selected")
                    return

                try:
                    with serial.Serial(port_name, 115200, timeout=2) as port:
                        data = port.read(1)

                    if data == b"A":
                        self.ui.label.setText("FPGA: Connected")
                    else:
                        self.ui.label.setText("FPGA: No Response")

                except serial.SerialException:
                    self.ui.label.setText("FPGA: Serial Error")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec())
