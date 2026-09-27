#!/usr/bin/env python3
"""
FPGA UART Troubleshooting Console
=================================

Purpose
-------
This program provides a graphical UART terminal for communicating with an FPGA.

The application can:
    * Discover serial ports.
    * Connect/disconnect from a selected UART port.
    * Transmit ASCII commands to the FPGA.
    * Display received FPGA data as plain text.
    * Display raw TX/RX bytes in hexadecimal.
    * Keep a command history.
    * Save a timestamped communications log.

Learning / safety-oriented coding style
---------------------------------------
This version is intentionally heavily commented so the control flow is easy
to follow.

It follows the *spirit* of the NASA/JPL "Power of Ten" rules where those ideas
make sense in Python:
    * Keep control flow simple.
    * Avoid recursion.
    * Keep functions reasonably small and focused.
    * Validate inputs before using them.
    * Check important return values.
    * Keep side effects explicit.
    * Prefer readable code over compressed one-line statements.

Some original Power-of-Ten rules are specifically about C, pointers, memory
allocation, and the C preprocessor, so they do not map directly to Python.

IMPORTANT
---------
Version 1.1.0 preserves the existing UART behavior and adds graphical TX/RX
activity LEDs.  The LEDs are display-only indicators and do not alter the UART
protocol itself.
"""

# ---------------------------------------------------------------------------
# Standard-library imports
# ---------------------------------------------------------------------------
# sys:
#     Gives access to command-line arguments and the process exit function.
#
# signal:
#     Lets Ctrl+C request that the Qt application shut down cleanly.
import sys
import signal
# datetime:
#     Used to create timestamps for the screen and session log files.
from datetime import datetime

# Path:
#     Provides readable, cross-platform filesystem path handling.
from pathlib import Path
# ---------------------------------------------------------------------------
# Qt / PySide6 imports
# ---------------------------------------------------------------------------
# QIODevice:
#     Supplies the ReadWrite flag used when opening the serial port.
#
# QTimer:
#     Used for two jobs:
#       1. Refreshing the list of serial ports periodically.
#       2. Giving Python periodic control so Ctrl+C can be handled.
from PySide6.QtCore import QIODevice, QTimer
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication,QComboBox,QGridLayout,QGroupBox,QHBoxLayout,QLabel,QLineEdit,QMainWindow,QPushButton,QPlainTextEdit,QSplitter,QVBoxLayout,QWidget,QListWidget
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

# ---------------------------------------------------------------------------
# Application version
# ---------------------------------------------------------------------------
# Version 1.1.0 adds graphical TX/RX activity indicators while preserving the
# existing UART behavior.
APP_VERSION = "1.1.0"

def hex_bytes(data: bytes) -> str:
    """Convert raw bytes into a human-readable hexadecimal string.

    Example:
        b'A\r\n'  ->  '41 0D 0A'

    The UART still uses the original bytes.  This function only creates text
    for display and logging.
    """
    return ' '.join(f'{b:02X}' for b in data)

def printable_text(data: bytes) -> str:
    """Convert UART bytes into text that is safe to display.

    Printable ASCII bytes are converted to characters.

    Carriage return (0x0D) and line feed (0x0A) are preserved because they are
    meaningful line-ending characters.

    Any other non-printable byte is displayed in angle brackets, for example:
        0x01 -> '<01>'
    """
    out=[]
    for b in data:
        if b==0x0D: out.append('\r')
        elif b==0x0A: out.append('\n')
        elif 0x20 <= b <= 0x7E: out.append(chr(b))
        else: out.append(f'<{b:02X}>')
    return ''.join(out)

# ---------------------------------------------------------------------------
# Main application window
# ---------------------------------------------------------------------------
class FPGAConsole(QMainWindow):
    """Main GUI window for the FPGA UART troubleshooting console."""
    def __init__(self):
        """Create the window, serial-port object, timers, and user interface."""

        # Initialize the QMainWindow base class first.
        super().__init__()
        self.setWindowTitle(f'FPGA UART Troubleshooting Console v{APP_VERSION}')
        self.resize(1200,800)
        # Create the Qt serial-port object.
        #
        # The two connect() calls below are Qt's signal/slot mechanism:
        #   readyRead      -> call read_serial() when bytes arrive.
        #   errorOccurred  -> call serial_error() when Qt reports a UART error.
        self.serial = QSerialPort(self)
        self.serial.readyRead.connect(self.read_serial)
        self.serial.errorOccurred.connect(self.serial_error)

        # TX/RX activity LEDs are visual indicators only.
        #
        # They do NOT control the serial port and they do NOT change the bytes
        # being transmitted or received.  They simply flash briefly whenever
        # this program sends or receives data.
        self.tx_led = None
        self.rx_led = None

        self.project_root = Path(__file__).resolve().parent.parent
        self.log_dir = Path.home() / 'Documents' / 'Logs'
        self.log_file = None
        self.log_path = None

        self.build_ui(); self.refresh_ports()
        idx=self.port_combo.findText('/dev/ttyUSB2')
        if idx>=0: self.port_combo.setCurrentIndex(idx)
        self.port_timer=QTimer(self); self.port_timer.timeout.connect(self.refresh_ports); self.port_timer.start(2500)

    def build_ui(self):
        """Create every visible control and place it into Qt layouts.

        Unlike an Xcode storyboard, this application currently creates its
        interface directly in Python code.

        Qt layouts decide the final widget sizes and positions.  We describe
        relationships such as 'put this widget in row 0, column 1' rather than
        assigning fixed screen coordinates.
        """
        central=QWidget(); self.setCentralWidget(central); root=QVBoxLayout(central)
        connection=QGroupBox('Serial Connection'); grid=QGridLayout(connection)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(5, 1)
        self.port_combo=QComboBox(); self.port_combo.setEditable(True)

        self.baud_combo=QComboBox()
        self.baud_combo.addItems(['1200','2400','4800','9600','19200','38400','57600','115200','230400','460800','921600'])
        self.baud_combo.setEditable(True)
        self.baud_combo.setCurrentText('115200')

        self.data_bits_combo=QComboBox()
        self.data_bits_combo.addItem('5', QSerialPort.Data5)
        self.data_bits_combo.addItem('6', QSerialPort.Data6)
        self.data_bits_combo.addItem('7', QSerialPort.Data7)
        self.data_bits_combo.addItem('8', QSerialPort.Data8)
        self.data_bits_combo.setCurrentText('8')

        self.parity_combo=QComboBox()
        self.parity_combo.addItem('None', QSerialPort.NoParity)
        self.parity_combo.addItem('Even', QSerialPort.EvenParity)
        self.parity_combo.addItem('Odd', QSerialPort.OddParity)
        self.parity_combo.addItem('Mark', QSerialPort.MarkParity)
        self.parity_combo.addItem('Space', QSerialPort.SpaceParity)
        self.parity_combo.setCurrentText('None')

        self.stop_bits_combo=QComboBox()
        self.stop_bits_combo.addItem('1', QSerialPort.OneStop)
        self.stop_bits_combo.addItem('1.5', QSerialPort.OneAndHalfStop)
        self.stop_bits_combo.addItem('2', QSerialPort.TwoStop)
        self.stop_bits_combo.setCurrentText('1')

        self.flow_combo=QComboBox()
        self.flow_combo.addItem('None', QSerialPort.NoFlowControl)
        self.flow_combo.addItem('Hardware RTS/CTS', QSerialPort.HardwareControl)
        self.flow_combo.addItem('Software XON/XOFF', QSerialPort.SoftwareControl)
        self.flow_combo.setCurrentText('None')

        self.connect_btn = QPushButton('Connect')
        self.connect_btn.clicked.connect(self.toggle_connection)

        self.refresh_btn = QPushButton('Refresh')
        self.refresh_btn.clicked.connect(self.refresh_ports)

        self.status = QLabel('Disconnected')

        # -------------------------------------------------------------------
        # UART activity indicators
        # -------------------------------------------------------------------
        # A QLabel can be styled to look like a small round LED.
        #
        # We start both indicators in their OFF state.  When data moves across
        # the UART, flash_activity_led() temporarily changes the stylesheet to
        # the ON state and then automatically returns it to OFF.
        self.tx_led = QLabel()
        self.rx_led = QLabel()

        for led in (self.tx_led, self.rx_led):
            led.setFixedSize(16, 16)
            led.setStyleSheet(self.led_style(False))

        self.tx_led.setToolTip('Flashes when the PC transmits data to the FPGA')
        self.rx_led.setToolTip('Flashes when the PC receives data from the FPGA')

        grid.addWidget(QLabel('Port:'),0,0); grid.addWidget(self.port_combo,0,1)
        grid.addWidget(QLabel('Baud:'),0,2); grid.addWidget(self.baud_combo,0,3)
        grid.addWidget(QLabel('Data Bits:'),0,4); grid.addWidget(self.data_bits_combo,0,5)
        grid.addWidget(QLabel('Parity:'),1,0); grid.addWidget(self.parity_combo,1,1)
        grid.addWidget(QLabel('Stop Bits:'),1,2); grid.addWidget(self.stop_bits_combo,1,3)
        grid.addWidget(QLabel('Flow Control:'),1,4); grid.addWidget(self.flow_combo,1,5)
        grid.addWidget(self.connect_btn, 2, 0, 1, 2)
        grid.addWidget(self.refresh_btn, 2, 2, 1, 2)

        # Put the activity indicators beside the connection status.
        #
        # Row 2, column 4 contains a small horizontal layout:
        #     TX [LED]    RX [LED]    connection status text
        activity_widget = QWidget()
        activity_layout = QHBoxLayout(activity_widget)
        activity_layout.setContentsMargins(0, 0, 0, 0)
        activity_layout.setSpacing(6)

        activity_layout.addWidget(QLabel('TX'))
        activity_layout.addWidget(self.tx_led)
        activity_layout.addSpacing(8)
        activity_layout.addWidget(QLabel('RX'))
        activity_layout.addWidget(self.rx_led)
        activity_layout.addSpacing(12)
        activity_layout.addWidget(self.status, 1)

        grid.addWidget(activity_widget, 2, 4, 1, 2)
        root.addWidget(connection)

        session=QGroupBox('Session Logging'); session_layout=QHBoxLayout(session)
        self.start_session_btn=QPushButton('Start Session')
        self.stop_session_btn=QPushButton('Stop Session')
        self.stop_session_btn.setEnabled(False)
        self.session_status=QLabel('No active session')
        self.start_session_btn.clicked.connect(self.start_session)
        self.stop_session_btn.clicked.connect(self.stop_session)
        session_layout.addWidget(self.start_session_btn)
        session_layout.addWidget(self.stop_session_btn)
        session_layout.addWidget(self.session_status,1)
        root.addWidget(session)

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

        history_group=QGroupBox('Command History')
        history_layout=QVBoxLayout(history_group)
        self.command_history=QListWidget()
        history_layout.addWidget(self.command_history)
        root.addWidget(history_group)

    def led_style(self, is_on):
        """Return the stylesheet used to draw an activity LED.

        Parameters
        ----------
        is_on:
            True  -> bright green LED.
            False -> dark gray LED.

        QLabel itself is rectangular, but border-radius: 8px turns the
        16-by-16 label into a circle.
        """
        if is_on:
            return (
                'background-color: #32CD32;'
                'border: 1px solid #1B7A1B;'
                'border-radius: 8px;'
            )

        return (
            'background-color: #3A3A3A;'
            'border: 1px solid #707070;'
            'border-radius: 8px;'
        )

    def flash_activity_led(self, led):
        """Flash one UART activity LED for a short, visible interval.

        The LED turns on immediately.

        QTimer.singleShot() schedules a one-time callback 120 milliseconds
        later.  That callback restores the LED to its OFF style.

        This is non-blocking: the program does NOT sleep or pause while the
        light is on, so serial communication and the GUI remain responsive.
        """
        led.setStyleSheet(self.led_style(True))

        QTimer.singleShot(
            120,
            lambda target_led=led: target_led.setStyleSheet(
                self.led_style(False)
            ),
        )

    def timestamp(self):
        return datetime.now().strftime('%H:%M:%S.%f')[:-3]

    def session_timestamp(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    def log_event(self, kind, text):
        if self.log_file is None:
            return
        safe_text = text.replace('\r', r'\r').replace('\n', r'\n')
        self.log_file.write(f'[{self.session_timestamp()}] {kind:<8} {safe_text}\n')
        self.log_file.flush()

    def start_session(self):
        if self.log_file is not None:
            return
        self.log_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_path = self.log_dir / f'fpga_uart_session_{stamp}.log'
        self.log_file = self.log_path.open('w', encoding='utf-8', buffering=1)
        self.log_event('SESSION', 'START')
        self.log_event(
            'CONFIG',
            f'Port={self.port_combo.currentText().strip() or "(none)"}, '
            f'Baud={self.baud_combo.currentText()}, '
            f'Data={self.data_bits_combo.currentText()}, '
            f'Parity={self.parity_combo.currentText()}, '
            f'Stop={self.stop_bits_combo.currentText()}, '
            f'Flow={self.flow_combo.currentText()}, '
            f'Ending={self.ending_combo.currentText()}'
        )
        self.session_status.setText(f'Logging: {self.log_path.name}')
        self.start_session_btn.setEnabled(False)
        self.stop_session_btn.setEnabled(True)

    def stop_session(self):
        if self.log_file is None:
            return
        self.log_event('SESSION', 'STOP')
        path = self.log_path
        self.log_file.close()
        self.log_file = None
        self.log_path = None
        self.session_status.setText(f'Saved: {path}')
        self.start_session_btn.setEnabled(True)
        self.stop_session_btn.setEnabled(False)

    def refresh_ports(self):
        current=self.port_combo.currentText(); ports=[p.systemLocation() for p in QSerialPortInfo.availablePorts()]
        self.port_combo.blockSignals(True); self.port_combo.clear(); self.port_combo.addItems(ports)
        if current:
            idx=self.port_combo.findText(current)
            if idx>=0: self.port_combo.setCurrentIndex(idx)
            else: self.port_combo.setEditText(current)
        self.port_combo.blockSignals(False)

    def set_serial_controls_enabled(self, enabled):
        self.port_combo.setEnabled(enabled)
        self.baud_combo.setEnabled(enabled)
        self.data_bits_combo.setEnabled(enabled)
        self.parity_combo.setEnabled(enabled)
        self.stop_bits_combo.setEnabled(enabled)
        self.flow_combo.setEnabled(enabled)
        self.refresh_btn.setEnabled(enabled)

    def serial_config_text(self):
        return (
            f'{self.serial.portName()} @ {self.serial.baudRate()} '
            f'{self.data_bits_combo.currentText()}-'
            f'{self.parity_combo.currentText()}-'
            f'{self.stop_bits_combo.currentText()}, '
            f'Flow={self.flow_combo.currentText()}'
        )

    def toggle_connection(self):
        if self.serial.isOpen():
            self.log_event('SERIAL', f'DISCONNECT {self.serial_config_text()}')
            self.serial.close()
            self.connect_btn.setText('Connect')
            self.status.setText('Disconnected')
            self.set_serial_controls_enabled(True)
            return

        port=self.port_combo.currentText().strip()
        if not port:
            self.status.setText('Select a serial port')
            return

        try:
            baud = int(self.baud_combo.currentText())
        except ValueError:
            self.status.setText('Invalid baud rate')
            return

        self.serial.setPortName(port)
        self.serial.setBaudRate(baud)
        self.serial.setDataBits(self.data_bits_combo.currentData())
        self.serial.setParity(self.parity_combo.currentData())
        self.serial.setStopBits(self.stop_bits_combo.currentData())
        self.serial.setFlowControl(self.flow_combo.currentData())

        if self.serial.open(QIODevice.ReadWrite):
            self.connect_btn.setText('Disconnect')
            self.set_serial_controls_enabled(False)
            config = self.serial_config_text()
            self.status.setText(f'Connected: {config}')
            self.log_event('SERIAL', f'CONNECT {config}')
        else:
            self.status.setText(f'Open failed: {self.serial.errorString()}')
            self.log_event('ERROR', f'OPEN FAILED {port}: {self.serial.errorString()}')

    def read_serial(self):
        """Handle bytes that arrive from the FPGA.

        Qt calls this function automatically when QSerialPort emits its
        readyRead signal.
        """
        data = bytes(self.serial.readAll())

        # A readyRead signal can theoretically occur without useful bytes.
        # Guard against that case before doing any display/log work.
        if not data:
            return

        # Visible indication that bytes arrived from the FPGA.
        self.flash_activity_led(self.rx_led)

        raw = hex_bytes(data)
        plain = printable_text(data)
        self.raw_rx.appendPlainText(f'{self.timestamp()}  RX  [{len(data):3d}]  {raw}')
        self.log_event('RX RAW', raw)
        self.log_event('RX TEXT', plain)
        self.text_console.moveCursor(QTextCursor.MoveOperation.End)
        self.text_console.insertPlainText(plain)
        self.text_console.ensureCursorVisible()
    def send_text(self):
        """Transmit the command currently entered by the user to the FPGA."""
        # Do not attempt a write unless the UART is open.
        if not self.serial.isOpen():
            self.status.setText('Not connected')
            return

        # Read the user's command text and selected line ending.
        text = self.send_edit.text()
        ending = self.ending_combo.currentData() or b''

        # UART data is sent as bytes.  Convert the entered ASCII text to bytes,
        # then append the selected CR/LF ending bytes.
        payload = (
            text.encode('ascii', errors='replace')
            + bytes(ending)
        )

        # Ask QSerialPort to queue the bytes for transmission.
        written = self.serial.write(payload)

        # Qt returns a negative value if the write could not be queued.
        if written < 0:
            self.status.setText(
                f'Write failed: {self.serial.errorString()}'
            )
            return

        # The bytes were accepted by QSerialPort for transmission.
        # Flash the TX activity indicator.
        self.flash_activity_led(self.tx_led)

        raw = hex_bytes(payload)
        stamp = self.timestamp()
        self.raw_tx.appendPlainText(f'{stamp}  TX  [{len(payload):3d}]  {raw}')
        self.command_history.addItem(f'{stamp}  {text}')
        self.command_history.scrollToBottom()
        self.log_event('TX RAW', raw)
        self.log_event('TX TEXT', text)
        self.text_console.moveCursor(QTextCursor.MoveOperation.End)
        self.text_console.insertPlainText(f'>> {text}\n')
        self.text_console.ensureCursorVisible()
        self.send_edit.clear(); self.send_edit.setFocus()

    def serial_error(self,error):
        if error!=QSerialPort.NoError and self.serial.isOpen(): self.status.setText(f'Serial error: {self.serial.errorString()}'); self.log_event('ERROR', self.serial.errorString())
    def clear_all(self): self.text_console.clear(); self.raw_rx.clear(); self.raw_tx.clear(); self.command_history.clear(); self.log_event('DISPLAY', 'CLEAR')
    def closeEvent(self,event):
        if self.serial.isOpen():
            self.log_event('SERIAL', f'DISCONNECT {self.serial_config_text()}')
            self.serial.close()
        self.stop_session()
        event.accept()
def handle_sigint(signum, frame):
    QApplication.quit()

# ---------------------------------------------------------------------------
# Program entry point
# ---------------------------------------------------------------------------
# Python sets __name__ to '__main__' when this file is launched directly.
# This block is therefore the Python equivalent of the application's startup
# entry point.
if __name__ == '__main__':
    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, handle_sigint)

    # Let Python periodically regain control so SIGINT (Ctrl+C) is handled.
    sigint_timer = QTimer()
    sigint_timer.start(100)
    sigint_timer.timeout.connect(lambda: None)

    window = FPGAConsole()
    window.show()
    sys.exit(app.exec())
