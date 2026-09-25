#!/usr/bin/env python3
import sys
from datetime import datetime
from PySide6.QtCore import QIODevice, QTimer
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication,QComboBox,QGridLayout,QGroupBox,QHBoxLayout,QLabel,QLineEdit,QMainWindow,QPushButton,QPlainTextEdit,QSplitter,QVBoxLayout,QWidget
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

def hex_bytes(data: bytes) -> str:
    return ' '.join(f'{b:02X}' for b in data)

def printable_text(data: bytes) -> str:
    out=[]
    for b in data:
        if b==0x0D: out.append('\r')
        elif b==0x0A: out.append('\n')
        elif 0x20 <= b <= 0x7E: out.append(chr(b))
        else: out.append(f'<{b:02X}>')
    return ''.join(out)

class FPGAConsole(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('FPGA UART Troubleshooting Console')
        self.resize(1200,800)
        self.serial=QSerialPort(self)
        self.serial.readyRead.connect(self.read_serial)
        self.serial.errorOccurred.connect(self.serial_error)
        self.build_ui(); self.refresh_ports()
        idx=self.port_combo.findText('/dev/ttyUSB2')
        if idx>=0: self.port_combo.setCurrentIndex(idx)
        self.port_timer=QTimer(self); self.port_timer.timeout.connect(self.refresh_ports); self.port_timer.start(2500)

    def build_ui(self):
        central=QWidget(); self.setCentralWidget(central); root=QVBoxLayout(central)
        connection=QGroupBox('Serial Connection'); grid=QGridLayout(connection)
        self.port_combo=QComboBox(); self.port_combo.setEditable(True)
        self.baud_combo=QComboBox(); self.baud_combo.addItems(['9600','19200','38400','57600','115200','230400','460800','921600']); self.baud_combo.setCurrentText('115200')
        self.connect_btn=QPushButton('Connect'); self.connect_btn.clicked.connect(self.toggle_connection)
        self.refresh_btn=QPushButton('Refresh'); self.refresh_btn.clicked.connect(self.refresh_ports)
        self.status=QLabel('Disconnected')
        grid.addWidget(QLabel('Port:'),0,0); grid.addWidget(self.port_combo,0,1); grid.addWidget(QLabel('Baud:'),0,2); grid.addWidget(self.baud_combo,0,3); grid.addWidget(self.connect_btn,0,4); grid.addWidget(self.refresh_btn,0,5); grid.addWidget(self.status,1,0,1,6)
        root.addWidget(connection)

        splitter=QSplitter()
        text_group=QGroupBox('Plain Text'); text_layout=QVBoxLayout(text_group)
        self.text_console=QPlainTextEdit(); self.text_console.setReadOnly(True); self.text_console.setLineWrapMode(QPlainTextEdit.NoWrap); text_layout.addWidget(self.text_console)
        raw_side=QWidget(); raw_layout=QVBoxLayout(raw_side); raw_layout.setContentsMargins(0,0,0,0)
        rx_group=QGroupBox('Raw RX — FPGA → PC'); rx_layout=QVBoxLayout(rx_group); self.raw_rx=QPlainTextEdit(); self.raw_rx.setReadOnly(True); self.raw_rx.setLineWrapMode(QPlainTextEdit.NoWrap); rx_layout.addWidget(self.raw_rx)
        tx_group=QGroupBox('Raw TX — PC → FPGA'); tx_layout=QVBoxLayout(tx_group); self.raw_tx=QPlainTextEdit(); self.raw_tx.setReadOnly(True); self.raw_tx.setLineWrapMode(QPlainTextEdit.NoWrap); tx_layout.addWidget(self.raw_tx)
        raw_layout.addWidget(rx_group); raw_layout.addWidget(tx_group)
        splitter.addWidget(text_group); splitter.addWidget(raw_side); splitter.setSizes([650,550]); root.addWidget(splitter,1)

        send_group=QGroupBox('Transmit'); send_layout=QHBoxLayout(send_group)
        self.send_edit=QLineEdit(); self.send_edit.setPlaceholderText('Example: A500A'); self.send_edit.returnPressed.connect(self.send_text)
        self.ending_combo=QComboBox(); self.ending_combo.addItem('CR/LF',b'\r\n'); self.ending_combo.addItem('CR',b'\r'); self.ending_combo.addItem('LF',b'\n'); self.ending_combo.addItem('None',b'')
        self.send_btn=QPushButton('Send'); self.send_btn.clicked.connect(self.send_text)
        self.clear_btn=QPushButton('Clear'); self.clear_btn.clicked.connect(self.clear_all)
        send_layout.addWidget(self.send_edit,1); send_layout.addWidget(QLabel('Ending:')); send_layout.addWidget(self.ending_combo); send_layout.addWidget(self.send_btn); send_layout.addWidget(self.clear_btn)
        root.addWidget(send_group)

    def timestamp(self): return datetime.now().strftime('%H:%M:%S.%f')[:-3]
    def refresh_ports(self):
        current=self.port_combo.currentText(); ports=[p.systemLocation() for p in QSerialPortInfo.availablePorts()]
        self.port_combo.blockSignals(True); self.port_combo.clear(); self.port_combo.addItems(ports)
        if current:
            idx=self.port_combo.findText(current)
            if idx>=0: self.port_combo.setCurrentIndex(idx)
            else: self.port_combo.setEditText(current)
        self.port_combo.blockSignals(False)

    def toggle_connection(self):
        if self.serial.isOpen():
            self.serial.close(); self.connect_btn.setText('Connect'); self.status.setText('Disconnected'); return
        port=self.port_combo.currentText().strip()
        if not port: self.status.setText('Select a serial port'); return
        self.serial.setPortName(port); self.serial.setBaudRate(int(self.baud_combo.currentText())); self.serial.setDataBits(QSerialPort.Data8); self.serial.setParity(QSerialPort.NoParity); self.serial.setStopBits(QSerialPort.OneStop); self.serial.setFlowControl(QSerialPort.NoFlowControl)
        if self.serial.open(QIODevice.ReadWrite):
            self.connect_btn.setText('Disconnect'); self.status.setText(f'Connected: {port} @ {self.serial.baudRate()} 8-N-1')
        else: self.status.setText(f'Open failed: {self.serial.errorString()}')

    def read_serial(self):
        data=bytes(self.serial.readAll())
        if not data: return
        self.raw_rx.appendPlainText(f'{self.timestamp()}  RX  [{len(data):3d}]  {hex_bytes(data)}')
        self.text_console.moveCursor(QTextCursor.MoveOperation.End)
        self.text_console.insertPlainText(printable_text(data))
        self.text_console.ensureCursorVisible()
    def send_text(self):
        if not self.serial.isOpen(): self.status.setText('Not connected'); return
        text=self.send_edit.text(); ending=self.ending_combo.currentData() or b''; payload=text.encode('ascii',errors='replace')+bytes(ending)
        written=self.serial.write(payload)
        if written<0: self.status.setText(f'Write failed: {self.serial.errorString()}'); return
        self.raw_tx.appendPlainText(f'{self.timestamp()}  TX  [{len(payload):3d}]  {hex_bytes(payload)}')
        self.text_console.moveCursor(QTextCursor.MoveOperation.End)
        self.text_console.insertPlainText(f'>> {text}\n')
        self.text_console.ensureCursorVisible()
        self.send_edit.clear(); self.send_edit.setFocus()

    def serial_error(self,error):
        if error!=QSerialPort.NoError and self.serial.isOpen(): self.status.setText(f'Serial error: {self.serial.errorString()}')
    def clear_all(self): self.text_console.clear(); self.raw_rx.clear(); self.raw_tx.clear()
    def closeEvent(self,event):
        if self.serial.isOpen(): self.serial.close()
        event.accept()

if __name__=='__main__':
    app=QApplication(sys.argv); window=FPGAConsole(); window.show(); sys.exit(app.exec())
