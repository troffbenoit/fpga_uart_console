# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_Widget(object):
    def setupUi(self, Widget):
        if not Widget.objectName():
            Widget.setObjectName(u"Widget")
        Widget.resize(800, 600)
        font = QFont()
        font.setPointSize(14)
        Widget.setFont(font)
        self.layoutWidget = QWidget(Widget)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(230, 280, 241, 74))
        self.verticalLayout = QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setSpacing(12)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.pushButton = QPushButton(self.layoutWidget)
        self.pushButton.setObjectName(u"pushButton")

        self.verticalLayout.addWidget(self.pushButton)

        self.label = QLabel(self.layoutWidget)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.addressSectionWidget = QWidget(Widget)
        self.addressSectionWidget.setObjectName(u"addressSectionWidget")
        self.addressSectionWidget.setGeometry(QRect(60, 150, 306, 36))
        self.horizontalLayout = QHBoxLayout(self.addressSectionWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.portLabel = QLabel(self.addressSectionWidget)
        self.portLabel.setObjectName(u"portLabel")

        self.horizontalLayout.addWidget(self.portLabel)

        self.portComboBox = QComboBox(self.addressSectionWidget)
        self.portComboBox.setObjectName(u"portComboBox")
        self.portComboBox.setMinimumSize(QSize(200, 0))

        self.horizontalLayout.addWidget(self.portComboBox)

        self.widget = QWidget(Widget)
        self.widget.setObjectName(u"widget")
        self.widget.setGeometry(QRect(70, 430, 140, 35))
        self.addressLayout = QHBoxLayout(self.widget)
        self.addressLayout.setObjectName(u"addressLayout")
        self.addressLayout.setContentsMargins(0, 0, 0, 0)
        self.AddressLabel = QLabel(self.widget)
        self.AddressLabel.setObjectName(u"AddressLabel")

        self.addressLayout.addWidget(self.AddressLabel)

        self.addressValueLabel = QLabel(self.widget)
        self.addressValueLabel.setObjectName(u"addressValueLabel")
        font1 = QFont()
        font1.setPointSize(18)
        font1.setBold(True)
        self.addressValueLabel.setFont(font1)

        self.addressLayout.addWidget(self.addressValueLabel)


        self.retranslateUi(Widget)

        QMetaObject.connectSlotsByName(Widget)
    # setupUi

    def retranslateUi(self, Widget):
        Widget.setWindowTitle(QCoreApplication.translate("Widget", u"Widget", None))
        self.pushButton.setText(QCoreApplication.translate("Widget", u"Test FPGA", None))
        self.label.setText(QCoreApplication.translate("Widget", u"FPGA: Disconnected", None))
        self.portLabel.setText(QCoreApplication.translate("Widget", u"Serial Port:", None))
        self.AddressLabel.setText(QCoreApplication.translate("Widget", u"Address:", None))
        self.addressValueLabel.setText(QCoreApplication.translate("Widget", u"0000", None))
    # retranslateUi

