# ui_components.py
# Helper functions for creating UI widgets

from PyQt5.QtWidgets import (
    QLabel, QCheckBox, QSpinBox, 
    QDoubleSpinBox, QPushButton, 
    QComboBox, QLineEdit
)

LABEL_STYLE = "font-size: 20pt;"
PADDING_STYLE = "padding: 3px;"
CHECKBOX_STYLE = """
QCheckBox {
    font-size: 20pt;
}
QCheckBox::indicator {
    width: 20px;
    height: 20px;
}
"""

def create_label(label_text):
    label = QLabel(label_text)
    label.setStyleSheet(LABEL_STYLE)
    return label


def set_label_color(label, color="black"):
    label.setStyleSheet(LABEL_STYLE + "color: " + color)


def create_checkbox(label_text, function, checked):
    checkbox = QCheckBox(label_text)
    checkbox.setStyleSheet(CHECKBOX_STYLE + PADDING_STYLE)
    checkbox.setChecked(checked)
    checkbox.stateChanged.connect(function)
    return checkbox


def create_spinbox(min_val, max_val, initial_val, function, 
                   double=False, decimals=0, step=1):
    spinbox = QDoubleSpinBox() if double else QSpinBox()
    if double:
        spinbox.setDecimals(decimals)
    spinbox.setMinimum(min_val)
    spinbox.setMaximum(max_val)
    spinbox.setValue(initial_val)
    spinbox.setStyleSheet(LABEL_STYLE + PADDING_STYLE)
    spinbox.valueChanged.connect(function)
    spinbox.setSingleStep(step)
    return spinbox


def create_pushbutton(label_text, function):
    button = QPushButton(label_text)
    button.setStyleSheet(LABEL_STYLE + PADDING_STYLE)
    button.clicked.connect(function)
    return button


def create_combobox(function, items=[]):
    combobox = QComboBox()
    combobox.addItems(items)
    combobox.setStyleSheet(LABEL_STYLE + PADDING_STYLE)
    combobox.currentIndexChanged.connect(function)
    return combobox


def create_lineedit(initial_text, function):
    line_edit = QLineEdit(initial_text)
    line_edit.setStyleSheet(LABEL_STYLE + PADDING_STYLE)
    line_edit.textChanged.connect(function)
    return line_edit 