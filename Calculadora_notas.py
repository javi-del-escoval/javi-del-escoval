import sys
import json
import os
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

DATA_FILE = "datos_notas.json"


# ===================== MODELO =====================

class Evaluacion:
    def __init__(self, nombre, nota, ponderacion):
        self.nombre = nombre
        self.nota = nota
        self.ponderacion = ponderacion


class Asignatura:
    def __init__(self, nombre):
        self.nombre = nombre
        self.evaluaciones = []

    def promedio_actual(self):
        total = 0
        total_pond = 0
        for e in self.evaluaciones:
            total += e.nota * e.ponderacion
            total_pond += e.ponderacion
        if total_pond == 0:
            return 0, 0
        return total / total_pond, total_pond

    def promedio_pesimista(self):
        promedio, total_pond = self.promedio_actual()
        restante = 100 - total_pond
        total = promedio * total_pond
        return (total + (1 * restante)) / 100


# ===================== UI =====================

class AsignaturaWidget(QWidget):
    def __init__(self, asignatura, save_callback):
        super().__init__()
        self.asignatura = asignatura
        self.save_callback = save_callback

        layout = QVBoxLayout()

        # Formulario agregar nota
        form = QHBoxLayout()

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre evaluación")

        self.input_nota = QDoubleSpinBox()
        self.input_nota.setRange(1.0, 7.0)
        self.input_nota.setSingleStep(0.1)

        self.input_pond = QSpinBox()
        self.input_pond.setRange(1, 100)

        btn_agregar = QPushButton("Agregar")
        btn_agregar.clicked.connect(self.agregar_evaluacion)

        form.addWidget(self.input_nombre)
        form.addWidget(self.input_nota)
        form.addWidget(self.input_pond)
        form.addWidget(btn_agregar)

        layout.addLayout(form)

        # Lista
        self.lista = QListWidget()
        layout.addWidget(self.lista)

        # Barra progreso
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        # Estado
        self.label_estado = QLabel()
        layout.addWidget(self.label_estado)

        self.setLayout(layout)
        self.actualizar_ui()

    def agregar_evaluacion(self):
        nombre = self.input_nombre.text()
        if not nombre:
            return
        nota = self.input_nota.value()
        pond = self.input_pond.value()

        self.asignatura.evaluaciones.append(
            Evaluacion(nombre, nota, pond)
        )

        self.input_nombre.clear()
        self.actualizar_ui()
        self.save_callback()

    def actualizar_ui(self):
        self.lista.clear()

        for e in self.asignatura.evaluaciones:
            self.lista.addItem(f"{e.nombre} - {e.nota} ({e.ponderacion}%)")

        promedio, total_pond = self.asignatura.promedio_actual()
        pesimista = self.asignatura.promedio_pesimista()

        self.progress.setValue(total_pond)

        estado = ""
        color = ""

        if promedio >= 5.0:
            estado = f"🟢 Eximido | Promedio: {round(promedio,2)}"
            color = "#00c853"
        elif pesimista < 4.0:
            estado = f"🔴 En riesgo | Promedio: {round(promedio,2)}"
            color = "#d50000"
        else:
            estado = f"🟡 En progreso | Promedio: {round(promedio,2)}"
            color = "#ffab00"

        self.label_estado.setText(estado)
        self.label_estado.setStyleSheet(f"color: {color}; font-weight: bold;")


# ===================== MAIN =====================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculadora Universitaria Pro")

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.load_data()

        toolbar = self.addToolBar("Toolbar")
        btn_add = QPushButton("Nueva Asignatura")
        btn_add.clicked.connect(self.nueva_asignatura)
        toolbar.addWidget(btn_add)

    def nueva_asignatura(self):
        nombre, ok = QInputDialog.getText(self, "Nueva Asignatura", "Nombre:")
        if ok and nombre:
            asignatura = Asignatura(nombre)
            self.add_tab(asignatura)
            self.save_data()

    def add_tab(self, asignatura):
        widget = AsignaturaWidget(asignatura, self.save_data)
        self.tabs.addTab(widget, asignatura.nombre)

    def save_data(self):
        data = []
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            asig = widget.asignatura
            data.append({
                "nombre": asig.nombre,
                "evaluaciones": [
                    {
                        "nombre": e.nombre,
                        "nota": e.nota,
                        "ponderacion": e.ponderacion
                    } for e in asig.evaluaciones
                ]
            })

        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return

        with open(DATA_FILE, "r") as f:
            data = json.load(f)

        for asig_data in data:
            asignatura = Asignatura(asig_data["nombre"])
            for e in asig_data["evaluaciones"]:
                asignatura.evaluaciones.append(
                    Evaluacion(e["nombre"], e["nota"], e["ponderacion"])
                )
            self.add_tab(asignatura)


# ===================== APP =====================

app = QApplication(sys.argv)

app.setStyleSheet("""
QMainWindow {
    background-color: #121212;
}
QWidget {
    background-color: #1e1e1e;
    color: white;
    font-size: 11pt;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QListWidget {
    background-color: #2a2a2a;
    border: 1px solid #333;
}
QPushButton {
    background-color: #2962ff;
    padding: 6px;
    border-radius: 6px;
}
QPushButton:hover {
    background-color: #0039cb;
}
QProgressBar {
    background-color: #2a2a2a;
    border: 1px solid #333;
}
QProgressBar::chunk {
    background-color: #00c853;
}
""")

window = MainWindow()
window.resize(900, 600)
window.show()

sys.exit(app.exec())
