import sys
import json
import os
import uuid
import copy
import re
import math
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsPathItem, QGraphicsRectItem, QGraphicsTextItem, QVBoxLayout,
    QHBoxLayout, QWidget, QPushButton, QLineEdit, QTextEdit, QLabel,
    QFileDialog, QDialog, QComboBox, QFormLayout, QMenu, QMessageBox,
    QScrollArea, QFrame, QGridLayout, QDialogButtonBox, QTabWidget,
    QSplitter, QSizePolicy, QGroupBox, QListWidget, QMenuBar, QProgressBar,
    QGraphicsEllipseItem, QDockWidget, QPlainTextEdit, QStackedWidget,
    QToolBar, QStatusBar
)
from PyQt6.QtGui import (
    QPainter, QPainterPath, QColor, QPen, QBrush, QFont,
    QLinearGradient, QImage, QKeySequence, QShortcut, QPolygonF, QAction
)
from PyQt6.QtCore import Qt, QPointF, QRectF, QSize, QTimer, QThread, pyqtSignal
try: from PyQt6.QtPrintSupport import QPrinter
except ImportError: QPrinter = None

from constants import NODE_TYPES, DEFAULT_NODE_COLOR
from models import WorkflowNode, WorkflowModel
from engine import LayoutEngine
import config
from ai_engine import AIEngine
from importers import DocParser

GRID = 20

GLOBAL_STYLE = """
QMainWindow, QFrame#sidebar { background: #13131a; }
QMenuBar { background: #1a1a2e; color: #61afef; border-bottom: 2px solid #2a2a3e; padding: 4px; }
QMenuBar::item:selected { background: #2a2a3e; border-radius: 4px; }
QMenu { background: #1a1a2e; color: white; border: 1px solid #2a2a3e; padding: 5px; }
QMenu::item:selected { background: #61afef; color: black; border-radius: 4px; }
QSplitter::handle { background: #2a2a3e; height: 2px; width: 2px; }
QTabWidget::pane { border: 0; background: #0d0d12; }
QTabBar::tab { background: #1e1e2e; color: #999; padding: 10px 22px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; border: 1px solid #2a2a3e; }
QTabBar::tab:selected { background: #0d0d12; color: #61afef; border-color: #3e4451; font-weight: bold; }
QLineEdit, QTextEdit, QListWidget { background: #1e1e2e; color: #eee; border: 1px solid #3e4451; border-radius: 6px; padding: 8px; }
QLineEdit:focus, QTextEdit:focus { border: 1px solid #61afef; background: #242730; }
QPushButton { background: #1e1e2e; color: white; border-radius: 6px; padding: 10px; border: 1px solid #3e4451; font-weight: bold; }
QPushButton:hover { background: #282c34; border-color: #c678dd; color: #c678dd; }
QPushButton#btn_save { background: #2d4f39; border-color: #50fa7b; color: #50fa7b; }
QPushButton#btn_import { background: #2d4554; border-color: #61afef; color: #61afef; }
QPushButton#btn_ai { background: #443c5e; border-color: #c678dd; color: #c678dd; }
QPushButton#btn_reset { background: #3d2b2b; border-color: #ff5555; color: #ff5555; }
QGroupBox { color: #61afef; font-weight: bold; border: 1px solid #2a2a3e; margin-top: 10px; padding-top: 10px; border-radius: 8px; }
QTextEdit#console { background: #0d0d12; color: #98c379; font-family: 'Consolas', monospace; font-size: 11px; border: 1px solid #2a2a3e; }
QGraphicsView#minimap { background: #0d0d12; border: 1px solid #2a2a3e; border-radius: 8px; }
QLabel#sidebar_title { color: #61afef; font-size: 20px; font-weight: bold; letter-spacing: 2px; padding: 10px 0; border-bottom: 2px solid #2a2a3e; margin-bottom: 10px; }
QDockWidget { border: 1px solid #2a2a3e; color: #61afef; }
QDockWidget::title { background: #1a1a2e; padding: 8px; font-weight: bold; }
"""

def get_node_comment(node: WorkflowNode) -> str:
    d = node.data_payload or {}
    def find_text(obj):
        if not isinstance(obj, dict): return None
        if "text" in obj and isinstance(obj["text"], str): return obj["text"]
        if "message" in obj and isinstance(obj["message"], dict): return find_text(obj["message"])
        if "payload" in obj and isinstance(obj["payload"], list) and len(obj["payload"]) > 0: return find_text(obj["payload"][0])
        for k in ["content", "msg", "params"]:
            if k in obj:
                res = find_text(obj[k])
                if res: return res
        return None
    txt = find_text(d)
    if txt: return str(txt)[:90]
    return ""

def repair_json(s):
    if not s: return ""
    # 1. Clean JS comments
    s = re.sub(r"//.*?\n", "\n", s)
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
    # 2. Extract strictly from First '[' to Last ']' or '{' to '}'
    s = s.strip()
    # If it contains "COMMANDS:", skip it
    if "COMMANDS:" in s: s = s.split("COMMANDS:", 1)[1]
    
    idx_a = s.find("["); idx_b = s.find("{")
    idx = -1
    if idx_a != -1 and (idx_b == -1 or idx_a < idx_b): idx = idx_a
    elif idx_b != -1: idx = idx_b
    if idx == -1: return ""
    
    s = s[idx:]
    stk = []; last_bal = 0; cl = {"}":"{", "]":"["}
    for i, c in enumerate(s):
        if c in "{[": stk.append(c)
        elif c in "}]" and stk:
            if stk[-1] == cl[c]: stk.pop()
            if not stk: last_bal = i + 1; break
    if last_bal > 0: s = s[:last_bal]
    # Balance if truncated
    stk = []; cl_s = {"{":"}", "[":"]"}
    for c in s:
        if c in "{[": stk.append(c)
        elif c in "}]" and stk: stk.pop()
    while stk: s += cl_s[stk.pop()]
    return s

class AIWorker(QThread):
    finished = pyqtSignal(str)
    def __init__(self, method, *args):
        super().__init__(); self.method, self.args = method, args
    def run(self):
        try: res = self.method(*self.args); self.finished.emit(res)
        except Exception as e: self.finished.emit(f"ERROR: {str(e)}")

class NodeEditDialog(QDialog):
    def __init__(self, node, parent=None):
        super().__init__(parent); self.setWindowTitle(f"Editar: {node.type}"); self.node = node; lay = QFormLayout(self)
        self.setStyleSheet("background:#1a1a2e; color:white; font-family: Segoe UI;")
        self.name_in = QLineEdit(node.name or ""); lay.addRow("Nombre:", self.name_in)
        self.branch_in = QLineEdit(node.branchLabel or ""); lay.addRow("Etiqueta Rama (Si/No):", self.branch_in)
        self.text_in = QTextEdit(get_node_comment(node)); lay.addRow("Texto:", self.text_in)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); lay.addWidget(bb)
    def save(self):
        self.node.name = self.name_in.text(); self.node.branchLabel = self.branch_in.text()
        if not isinstance(self.node.data_payload, dict): self.node.data_payload = {}
        self.node.data_payload["payload"] = [{"message": {"text": self.text_in.toPlainText()}}]

class FlowTitleItem(QGraphicsTextItem):
    def __init__(self, text, on_rename):
        super().__init__(text); self.on_rename = on_rename
        self.setDefaultTextColor(QColor(97, 175, 239)); self.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.setPos(50, 50); self.setToolTip("Doble clic para renombrar proyecto")
    def mouseDoubleClickEvent(self, e):
        from PyQt6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(None, "Renombrar Flujo", "Nuevo nombre:", text=self.toPlainText())
        if ok and new_name: self.on_rename(new_name)

class ConnectionCircle(QGraphicsEllipseItem):
    def __init__(self, parent_node):
        super().__init__(-8, -8, 16, 16, parent_node)
        self.setBrush(QBrush(QColor(80, 250, 123))); self.setPen(QPen(Qt.GlobalColor.white, 2))
        self.setPos(0, 50); self.setAcceptHoverEvents(True); self.setCursor(Qt.CursorShape.PointingHandCursor)
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect); painter.setPen(QPen(QColor(40, 40, 60), 1))
        l, r, t, b = int(rect.left()), int(rect.right()), int(rect.top()), int(rect.bottom())
        for x in range(l - (l%GRID), r, GRID):
            for y in range(t - (t%GRID), b, GRID): painter.drawPoint(x, y)

    def mousePressEvent(self, e):
        view = self.scene().views()[0] if self.scene().views() else None
        if view: view.start_linking(self.parentItem())

class NodeItem(QGraphicsItem):
    def __init__(self, node: WorkflowNode, on_action=None):
        super().__init__(); self.node = node; self.on_action = on_action; self.width, self.height = 220, 100
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.connections = []; self.setPos(float(node.x or 0), float(node.y or 0))
        self.handle = ConnectionCircle(self); self.handle.setVisible(False)
        self.setAcceptHoverEvents(True); self.is_hovered = False
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            nx = round(value.x()/GRID)*GRID; ny = round(value.y()/GRID)*GRID
            return QPointF(nx, ny)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for c in self.connections: c.update_path()
            self.node.x, self.node.y = self.pos().x(), self.pos().y()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self.handle.setVisible(value)
        return super().itemChange(change, value)

    def mousePressEvent(self, e):
        # 🛡️ Quick Actions Check
        if self.is_hovered:
            p = e.pos()
            if QRectF(self.width/2-15, -self.height/2-10, 24, 24).contains(p): # [+] Add child
                self.on_action("ADD_CHILD", self.node); return
            if QRectF(-self.width/2-10, -self.height/2-10, 24, 24).contains(p): # [x] Delete
                self.on_action("DELETE", self.node); return
        
        super().mousePressEvent(e)
        # 🎯 Update main window dock with node properties
        try:
            view = self.scene().views()[0] if self.scene().views() else None
            if view:
                tab = view.parent(); mw = tab.main_win
                if hasattr(mw, "prop_panel"): mw.prop_panel.load_node(self.node, tab)
        except: pass
    
    def boundingRect(self): return QRectF(-self.width/2-10, -self.height/2-10, self.width+20, self.height+20)
    
    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 🎨 Advanced Color Mapping (Strict + Aliases)
        t = self.node.type.lower() if self.node.type else ""
        colors = {
            "sendmessage": QColor(97, 175, 239), "message": QColor(97, 175, 239),
            "askquestion": QColor(198, 120, 221), "question": QColor(198, 120, 221),
            "branch": QColor(229, 192, 123), "option": QColor(229, 192, 123), "boton": QColor(229, 192, 123),
            "wait": QColor(209, 154, 102), "delay": QColor(209, 154, 102), "esperar": QColor(209, 154, 102),
            "trigger": QColor(152, 195, 121), "start": QColor(152, 195, 121), "disparador": QColor(152, 195, 121),
            "jumpto": QColor(224, 108, 117), "jump": QColor(224, 108, 117), "salto": QColor(224, 108, 117), "goto": QColor(224, 108, 117)
        }
        
        c = colors.get(t, QColor(171, 178, 191)); r = QRectF(-self.width/2, -self.height/2, self.width, self.height)
        if self.isSelected(): painter.setPen(QPen(c.lighter(130), 4)); painter.drawRoundedRect(r.adjusted(-3,-3,3,3), 12, 12)
        grad = QLinearGradient(0, -self.height/2, 0, self.height/2); grad.setColorAt(0, QColor(40, 44, 52)); grad.setColorAt(1, QColor(30, 33, 40))
        painter.setBrush(grad); painter.setPen(QPen(c.darker(120), 2)); painter.drawRoundedRect(r, 10, 10)
        painter.setBrush(c.darker(150)); painter.drawRoundedRect(r.adjusted(0,0,0,-75), 10, 10)
        painter.setPen(Qt.GlobalColor.white); painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(r.adjusted(10, 5, -10, -10), Qt.AlignmentFlag.AlignTop, self.node.name or self.node.type)
        painter.setPen(QColor(171, 178, 191)); painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(r.adjusted(10, 35, -10, -10), Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap, get_node_comment(self.node))
        
        # 🔗 Hover Buttons (Quick Actions)
        if self.is_hovered:
            painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QColor(80, 250, 123))
            painter.drawEllipse(int(self.width/2-15), int(-self.height/2-10), 24, 24) # [+]
            painter.setBrush(QColor(255, 85, 85))
            painter.drawEllipse(int(-self.width/2-10), int(-self.height/2-10), 24, 24) # [x]
            painter.setPen(Qt.GlobalColor.black); painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            painter.drawText(QRectF(self.width/2-15, -self.height/2-10, 24, 24), Qt.AlignmentFlag.AlignCenter, "+")
            painter.drawText(QRectF(-self.width/2-10, -self.height/2-10, 24, 24), Qt.AlignmentFlag.AlignCenter, "x")
    
    def hoverEnterEvent(self, e): self.is_hovered = True; self.update(); super().hoverEnterEvent(e)
    def hoverLeaveEvent(self, e): self.is_hovered = False; self.update(); super().hoverLeaveEvent(e)
    def mouseDoubleClickEvent(self, e):
        dlg = NodeEditDialog(self.node)
        if dlg.exec(): dlg.save(); self.on_action("REFRESH", self.node)
    def contextMenuEvent(self, e):
        if not self.scene().views(): return
        m = QMenu(); m.setStyleSheet("background: #1a1a2e; color: white; border: 1px solid #3e4451;")
        
        # Action: Delete
        del_act = m.addAction("❌ Eliminar")
        
        # Action: Change Type
        ct_m = m.addMenu("🔄 Cambiar Tipo a...")
        types = [("Mensaje", "sendMessage"), ("Pregunta", "askQuestion"), ("Rama/Botón", "branch"), ("Esperar", "wait"), ("Saltar a", "jumpTo")]
        for label, t_id in types:
            a = ct_m.addAction(label)
            a.triggered.connect(lambda _, tid=t_id: self.on_action("CHANGE_TYPE", (self.node, tid)))
        
        act = m.exec(self.scene().views()[0].viewport().mapToGlobal(e.pos().toPoint()))
        if act == del_act: self.on_action("DELETE", self.node)

class ConnectionItem(QGraphicsPathItem):
    def __init__(self, source, target):
        super().__init__(); self.source, self.target = source, target
        self.source.connections.append(self); self.target.connections.append(self); self.setZValue(-1)
        self.label = QGraphicsTextItem(self.target.node.branchLabel or "", self)
        self.label.setDefaultTextColor(QColor(171, 178, 191)); self.label.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.update_path()
    def update_path(self):
        try:
            p1 = self.source.mapToScene(QPointF(0, self.source.height/2))
            p2 = self.target.mapToScene(QPointF(0, -self.target.height/2))
            
            # --- Orthogonal Logic (Elbow) ---
            path = QPainterPath(); path.moveTo(p1)
            mid_y = (p1.y() + p2.y()) / 2
            path.lineTo(p1.x(), mid_y)
            path.lineTo(p2.x(), mid_y)
            path.lineTo(p2.x(), p2.y())
            
            self.setPath(path); self.setPen(QPen(QColor(144, 156, 178), 2)); self.setBrush(Qt.BrushStyle.NoBrush)
            mid_p = path.pointAtPercent(0.5)
            self.label.setPos(mid_p.x() + 5, mid_p.y() - 10)
            self.label.setPlainText(self.target.node.branchLabel or "")
            self.label.setVisible(bool(self.target.node.branchLabel))
        except: pass
    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        try:
            p2 = self.target.mapToScene(QPointF(0, -self.target.height/2))
            painter.setBrush(QBrush(QColor(144, 156, 178))); painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(QPolygonF([QPointF(p2.x(), p2.y()), QPointF(p2.x()-6, p2.y()-10), QPointF(p2.x()+6, p2.y()-10)]))
        except: pass

class FlowCanvas(QGraphicsView):
    def __init__(self, on_action=None, parent=None):
        super().__init__(parent); self.scene = QGraphicsScene(self); self.setScene(self.scene)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag); self.setBackgroundBrush(QBrush(QColor(18, 18, 24)))
        self.on_action = on_action; self.linking_from = None; self.temp_line = None; self._is_panning = False

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect); painter.setPen(QPen(QColor(45, 45, 65), 1))
        l, r, t, b = int(rect.left()), int(rect.right()), int(rect.top()), int(rect.bottom())
        grid = 30
        for x in range(l - (l%grid), r, grid):
            for y in range(t - (t%grid), b, grid): painter.drawPoint(x, y)
    def start_linking(self, node_item):
        self.linking_from = node_item; self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.temp_line = self.scene.addLine(0,0,0,0, QPen(QColor(80, 250, 123), 2, Qt.PenStyle.DashLine))
    def mouseMoveEvent(self, e):
        if self.linking_from:
            p1 = self.linking_from.mapToScene(QPointF(0, self.linking_from.height/2)); p2 = self.mapToScene(e.pos())
            self.temp_line.setLine(p1.x(), p1.y(), p2.x(), p2.y())
        super().mouseMoveEvent(e)
    def mouseReleaseEvent(self, e):
        if self.linking_from:
            item = self.itemAt(e.pos())
            while item and not isinstance(item, NodeItem): item = item.parentItem()
            if item and item != self.linking_from:
                item.node.parentId = self.linking_from.node.id; self.on_action("REFRESH", None, None)
            if self.temp_line: self.scene.removeItem(self.temp_line); self.temp_line = None
            self.linking_from = None; self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        if e.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = False; self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True; self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(e)

    def wheelEvent(self, e):
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        f = 1.15 if e.angleDelta().y() > 0 else 1/1.15; self.scale(f, f)
    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Delete or e.key() == Qt.Key.Key_Backspace:
            if self.scene.selectedItems():
                for item in self.scene.selectedItems():
                    if isinstance(item, NodeItem): self.on_action("DELETE", item.node)
        super().keyPressEvent(e)
    def contextMenuEvent(self, e):
        m = QMenu(); add_m = m.addMenu("➕ Agregar Nodo"); pos = self.mapToScene(e.pos())
        for q in ["sendMessage", "askQuestion", "branch", "wait", "jumpTo"]:
            a = add_m.addAction(q); a.triggered.connect(lambda _, xt=q, xp=pos: self.on_action("ADD", xt, xp))
        m.exec(self.viewport().mapToGlobal(e.pos()))

class WorkflowTab(QWidget):
    def __init__(self, main_win, parent=None):
        super().__init__(parent); self.main_win = main_win; self.model = WorkflowModel(); self._file_path = None
        self.undo_stack = []
        lay = QVBoxLayout(self); self.sp = QSplitter(Qt.Orientation.Vertical)
        self.canvas = FlowCanvas(on_action=self.on_canvas_action, parent=self); self.sp.addWidget(self.canvas)
        
        # --- Classic Console & Chat ---
        console_widget = QWidget(); cw_lay = QVBoxLayout(console_widget); cw_lay.setContentsMargins(0,0,0,0); cw_lay.setSpacing(2)
        self.console = QPlainTextEdit(); self.console.setReadOnly(True); self.console.setObjectName("console")
        self.console.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0d0d1a; 
                color: #00ffcc; 
                border: 1px solid #1a1a2e; 
                font-family: 'Consolas', 'Monaco', monospace; 
                font-size: 10pt; 
                padding: 5px;
            }
        """)
        cw_lay.addWidget(self.console)
        
        self.ai_in = QLineEdit(); self.ai_in.setPlaceholderText("Consulta al MAXI AI ARCHITECT sobre este flujo..."); self.ai_in.returnPressed.connect(self.main_win.ask_ai)
        self.ai_in.setStyleSheet("""
            QLineEdit {
                background-color: #161625; 
                color: white; 
                border: 1px solid #1a1a2e; 
                padding: 10px; 
                border-radius: 4px;
                font-size: 11pt;
            }
            QLineEdit:focus { border: 1px solid #61afef; }
        """)
        cw_lay.addWidget(self.ai_in)
        
        self.sp.addWidget(console_widget)
        lay.addWidget(self.sp); self.sp.setStretchFactor(0, 1); self.sp.setStretchFactor(1, 0)
        QShortcut(QKeySequence("Ctrl+Z"), self, self.undo)
        self.title_item = None

    def log(self, msg):
        self.console.appendPlainText(msg); self.console.ensureCursorVisible()

    def push_undo(self):
        self.undo_stack.append(copy.deepcopy(self.model.to_dict()))
        if len(self.undo_stack) > 30: self.undo_stack.pop(0)

    def undo(self):
        if self.undo_stack:
            data = self.undo_stack.pop()
            self.model.from_dict(data)
            self.render(); self.log("⏪ Deshacer realizado.")
    def load(self, path):
        try: self._file_path = path; self.model.load_json(path); LayoutEngine().apply_tree_layout(self.model); self.render()
        except Exception as e: self.log(f"❌ Error al cargar: {e}")
    def render(self):
        try:
            self.canvas.scene.clear(); self.items = {}
            # Add Flow Title
            def _rename(n): 
                self.model.name = n; self.render()
                idx = self.main_win.tabs.indexOf(self)
                if idx >= 0: self.main_win.tabs.setTabText(idx, n[:15] + "..." if len(n)>15 else n)
            
            self.title_item = FlowTitleItem(self.model.name or "Nuevo Flujo", _rename)
            self.title_item.setPos(-500, -200) # Move title out of the way of the main flow origin
            self.canvas.scene.addItem(self.title_item)
            
            for n in self.model.nodes.values(): n.children = []
            for n in self.model.nodes.values():
                p_id = str(n.parentId) if n.parentId else None
                if p_id and p_id in self.model.nodes: self.model.nodes[p_id].children.append(n)
            for n in self.model.nodes.values():
                item = NodeItem(n, on_action=self.on_canvas_action); self.canvas.scene.addItem(item); self.items[str(n.id)] = item
            for n in self.model.nodes.values():
                p_id = str(n.parentId) if n.parentId else None
                if p_id and p_id in self.items: self.canvas.scene.addItem(ConnectionItem(self.items[p_id], self.items[str(n.id)]))
            self.main_win.update_minimap()
        except Exception as e: print(f"Render Error: {e}")
    def on_canvas_action(self, action, data=None, pos=None):
        if action in ["DELETE", "ADD", "ADD_CENTER", "CHANGE_TYPE"]: self.push_undo()
        
        if action == "DELETE":
            if data.id in self.model.nodes: del self.model.nodes[data.id]; self.render()
        elif action == "ADD":
            nid = str(uuid.uuid4().hex[:6]); new_n = WorkflowNode({"id": nid, "type": data, "name": f"Nuevo {data}", "x": pos.x(), "y": pos.y()})
            self.model.nodes[nid] = new_n; self.render()
        elif action == "ADD_CENTER":
            rect = self.canvas.mapToScene(self.canvas.viewport().rect()).boundingRect()
            cx, cy = rect.center().x(), rect.center().y()
            nid = str(uuid.uuid4().hex[:6]); new_n = WorkflowNode({"id": nid, "type": data, "name": f"Nuevo {data}", "x": cx, "y": cy})
            self.model.nodes[nid] = new_n; self.render()
        elif action == "CHANGE_TYPE":
            node, new_type = data
            node.type = new_type; self.render()
        elif action == "ADD_CHILD":
            self.push_undo()
            nid = str(uuid.uuid4().hex[:6])
            # Position child slightly below parent
            new_n = WorkflowNode({
                "id": nid, "parentId": data.id, "type": "sendMessage",
                "name": "Nuevo Nodo", "x": data.x, "y": data.y + 150
            })
            self.model.nodes[nid] = new_n; self.render()
        elif action == "REFRESH": self.render()

class AIConfirmationDialog(QDialog):
    def __init__(self, summary, parent=None):
        super().__init__(parent); self.setWindowTitle("Análisis de Documento"); self.setMinimumWidth(600); self.setStyleSheet("background:#1a1a2e; color:white;")
        lay = QVBoxLayout(self); lay.addWidget(QLabel("<b>¿Procedemos a generar el diagrama con este análisis?</b>"))
        self.view = QTextEdit(); self.view.setReadOnly(True); self.view.setPlainText(summary); lay.addWidget(self.view)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject); lay.addWidget(btns)

class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent); self.setWindowTitle("Configuración de Inteligencia"); self.setMinimumWidth(500); lay = QVBoxLayout(self)
        self.setStyleSheet("background:#1a1a2e; color:white;")
        tabs = QTabWidget(); lay.addWidget(tabs)
        
        # Tab 1: API
        t1 = QWidget(); t1l = QFormLayout(t1); self.key = QLineEdit(); self.key.setText(config.get_config().get("gemini_api_key",""))
        t1l.addRow("Gemini API Key:", self.key); tabs.addTab(t1, "🔑 API")
        
        # Tab 2: Glosario
        t2 = QWidget(); t2l = QVBoxLayout(t2); self.g_text = QTextEdit(); self.g_text.setPlaceholderText("Escribe reglas rápidas aquí...")
        self.g_text.setPlainText(config.get_config().get("glossary_text", ""))
        self.g_path = QLineEdit(); self.g_path.setReadOnly(True); self.g_path.setText(config.get_config().get("glossary_path", ""))
        btn_g = QPushButton("📁 Cargar Glosario (PDF/Docx/TXT)"); btn_g.clicked.connect(self.load_g)
        t2l.addWidget(QLabel("Notas de Glosario:")); t2l.addWidget(self.g_text); t2l.addWidget(QLabel("Archivo de Referencia:")); t2l.addWidget(self.g_path); t2l.addWidget(btn_g)
        tabs.addTab(t2, "📖 Glosario")
        
        # Tab 3: Ejemplo
        t3 = QWidget(); t3l = QVBoxLayout(t3); self.e_path = QLineEdit(); self.e_path.setReadOnly(True)
        self.e_path.setText(config.get_config().get("example_path", ""))
        btn_e = QPushButton("📁 Cargar Flujo de Ejemplo (JSON/PDF/Docx)"); btn_e.clicked.connect(self.load_e)
        t3l.addWidget(QLabel("Este archivo servirá como molde de diseño para la IA:")); t3l.addWidget(self.e_path); t3l.addWidget(btn_e); t3l.addStretch()
        tabs.addTab(t3, "🎨 Ejemplo")
        
        btn_save = QPushButton("💾 Guardar Configuración"); btn_save.setObjectName("btn_save"); btn_save.clicked.connect(self.save); lay.addWidget(btn_save)

    def load_g(self):
        f, _ = QFileDialog.getOpenFileName(self, "Glosario", "", "Archivos Soportados (*.pdf *.docx *.json *.txt)")
        if f: self.g_path.setText(f)
    def load_e(self):
        f, _ = QFileDialog.getOpenFileName(self, "Ejemplo", "", "Archivos Soportados (*.json *.pdf *.docx *.txt)")
        if f: self.e_path.setText(f)
    def save(self):
        msg = QMessageBox(self); msg.setWindowTitle("Procesando"); msg.setText("Agregando fuente y comprendiendo, un momento por favor..."); msg.setStandardButtons(QMessageBox.StandardButton.NoButton); msg.show()
        QApplication.processEvents()
        c = config.get_config(); c["gemini_api_key"] = self.key.text().strip(); c["glossary_text"] = self.g_text.toPlainText()
        c["glossary_path"] = self.g_path.text(); c["example_path"] = self.e_path.text(); config.save_config(c)
        if hasattr(self.parent(), "ai"): self.parent().ai.reconfigure()
        if hasattr(self.parent(), "update_ai_status"): self.parent().update_ai_status()
        msg.close(); self.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Maxi-Designer"); self.resize(1400, 900); self.ai = AIEngine(); self.last_doc_context = ""; self.init_ui(); self.setStyleSheet(GLOBAL_STYLE)
    def init_ui(self):
        mb = self.menuBar(); fm = mb.addMenu("Archivo")
        fm.addAction("✨ Nuevo Flujo", self.handle_new_flow)
        fm.addAction("Importar JSON", self.import_json); fm.addAction("📂 Importar Lucidchart (CSV)", self.import_lucid_csv)
        fm.addAction("💾 Guardar", self.save_current)
        self.rmp = fm.addMenu("Recientes"); self.rmp.aboutToShow.connect(self.update_recent)
        root = QWidget(); self.setCentralWidget(root); lay = QHBoxLayout(root); self.sp = QSplitter(Qt.Orientation.Horizontal); lay.addWidget(self.sp)
        sidebar = QFrame(); sidebar.setObjectName("sidebar"); sidebar.setMinimumWidth(380); sb = QVBoxLayout(sidebar); self.sp.addWidget(sidebar)
        lbl = QLabel("MAXI DESIGNER"); lbl.setObjectName("sidebar_title"); sb.addWidget(lbl)
        
        bn = QPushButton("✨ Nuevo Flujo"); bn.setObjectName("btn_ai"); bn.clicked.connect(self.handle_new_flow); sb.addWidget(bn)
        
        # AI Status Indicator
        self.ai_status_lbl = QLabel("🤖 IA ESTÁNDAR"); self.ai_status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ai_status_lbl.setStyleSheet("background: #2a2a3e; color: #61afef; border-radius: 4px; padding: 5px; font-weight: bold; border: 1px solid #3e4451;")
        sb.addWidget(self.ai_status_lbl); self.update_ai_status()

        h1 = QHBoxLayout(); bi = QPushButton("Importar JSON"); bi.clicked.connect(self.import_json); h1.addWidget(bi)
        bs = QPushButton("💾 Guardar"); bs.clicked.connect(self.save_current); h1.addWidget(bs); sb.addLayout(h1)
        
        h2 = QHBoxLayout(); br = QPushButton("📂 Recientes"); self.rm = QMenu(self); br.setMenu(self.rm); self.rm.aboutToShow.connect(self.update_recent); h2.addWidget(br)
        be = QPushButton("📤 Exportar"); exm = QMenu(self); be.setMenu(exm); 
        exm.addAction("PNG", self.export_png); exm.addAction("PDF", self.export_pdf); exm.addAction("CSV (Lucidchart)", self.export_csv)
        h2.addWidget(be); sb.addLayout(h2)

        # Node Palette
        np = QGroupBox("📚 Librería de Nodos (Insertar)")
        npl = QGridLayout(np)
        node_btns = [("💬 Mensaje", "sendMessage"), ("❓ Pregunta", "askQuestion"), ("🌿 Rama", "branch"), ("⏳ Esperar", "wait"), ("🚩 Salto", "jumpTo")]
        for i, (txt, tid) in enumerate(node_btns):
            b = QPushButton(txt)
            b.setStyleSheet("font-size: 11px; padding: 6px; background: #2a2a3e; border: 1px solid #3e4451;")
            b.clicked.connect(lambda _, t=tid: self._add_node_to_current(t))
            npl.addWidget(b, i // 2, i % 2)
        sb.addWidget(np)

        ba = QPushButton("📄 IA Doc Import"); ba.setObjectName("btn_ai"); ba.clicked.connect(self.import_doc_ai); sb.addWidget(ba)
        brs = QPushButton("🧹 Reset / Borrado"); brs.setObjectName("btn_reset"); brs.clicked.connect(self.reset_flow); sb.addWidget(brs)
        gb = QGroupBox("Docs y Vista"); gbl = QHBoxLayout(gb); self.doc_list = QListWidget(); self.doc_list.setFixedHeight(120); gbl.addWidget(self.doc_list, 1)
        self.mini_map = QGraphicsView(); self.mini_map.setObjectName("minimap"); self.mini_map.setFixedHeight(120); gbl.addWidget(self.mini_map, 1); sb.addWidget(gb)
        self.progress = QProgressBar(); self.progress.hide(); sb.addWidget(self.progress); sb.addStretch()
        bc = QPushButton("⚙ Config Gemini"); bc.clicked.connect(lambda: SettingsDialog(self).exec()); sb.addWidget(bc)
        self.tabs = QTabWidget(); self.tabs.setTabsClosable(True); self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_minimap); self.sp.addWidget(self.tabs); self.new_tab()
        self.sp.setStretchFactor(0, 1); self.sp.setStretchFactor(1, 4)

    def setup_docks(self): pass
    def _add_node_to_current(self, tid):
        t = self._current_tab()
        if t: t.on_canvas_action("ADD_CENTER", tid)
    def update_ai_status(self):
        c = config.get_config()
        has_k = bool(c.get("glossary_path") or c.get("glossary_text") or c.get("example_path"))
        if has_k: self.ai_status_lbl.setText("💡 IA EXPERTA"); self.ai_status_lbl.setStyleSheet("background: #443c5e; color: #51fa7b; border-radius: 4px; padding: 5px; font-weight: bold; border: 1px solid #50fa7b;")
        else: self.ai_status_lbl.setText("🤖 IA ESTÁNDAR"); self.ai_status_lbl.setStyleSheet("background: #2a2a3e; color: #61afef; border-radius: 4px; padding: 5px; font-weight: bold; border: 1px solid #3e4451;")
    def close_tab(self, idx):
        if self.tabs.count() > 1: self.tabs.removeTab(idx)
    def update_minimap(self, idx=None):
        t = self._current_tab()
        if t and hasattr(t, "canvas") and t.canvas.scene and t.canvas.scene.sceneRect().isValid():
            self.mini_map.setScene(t.canvas.scene)
            QTimer.singleShot(100, lambda: self.mini_map.fitInView(t.canvas.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio))
    def reset_flow(self):
        t = self._current_tab()
        if t and QMessageBox.question(self, "Reset", "¿Borrar?") == QMessageBox.StandardButton.Yes: t.model = WorkflowModel(); t.render()
    def _current_tab(self): idx = self.tabs.currentIndex(); return self.tabs.widget(idx) if idx >= 0 else None
    
    def import_lucid_csv(self):
        f, _ = QFileDialog.getOpenFileName(self, "Excel/Lucid CSV", "", "*.csv")
        if f:
            self.new_tab(f); t = self._current_tab(); 
            from importers import LucidImporter
            t.model = LucidImporter.import_csv(f, t.model)
            LayoutEngine().apply_tree_layout(t.model); t.render()
            t.log(f"✅ Importado correctamente desde Lucidchart: {os.path.basename(f)}")

    def align_sel(self, mode): pass # Funcionalidad delegada a futuro

    def export_csv(self):
        t = self._current_tab()
        if not t: return
        f, _ = QFileDialog.getSaveFileName(self, "Exportar CSV", "", "*.csv")
        if f:
            import csv
            with open(f, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Id", "Name", "Shape Library", "Page ID", "Contained By", "Text Area 1", "Line Source", "Line Destination"])
                # Nodes
                for nid, n in t.model.nodes.items():
                    # Extract text content
                    txt = str(n.data_payload.get("payload", [{}])[0].get("message", {}).get("text", n.name))
                    writer.writerow([nid, n.type, "Flowchart Shapes", "1", "", txt, "", ""])
                # Lines
                for nid, n in t.model.nodes.items():
                    if n.parentId:
                        writer.writerow([f"line_{nid}", "Line", "", "1", "", "", n.parentId, nid])
            t.log(f"✅ Exportación CSV completa: {os.path.basename(f)}")

    def new_tab(self, path=None):
        t = WorkflowTab(self); self.tabs.addTab(t, os.path.basename(path) if path else "Nuevo")
        if path: t.load(path); config.add_recent_file(path)
        else: t.render()
        self.tabs.setCurrentWidget(t)

    def _ask_destination(self, title):
        m = QMessageBox(self); m.setWindowTitle(title); m.setText("¿Dónde quieres aplicar esta acción?"); m.setIcon(QMessageBox.Icon.Question)
        bn = m.addButton("Lienzo Nuevo", QMessageBox.ButtonRole.ActionRole)
        bc = m.addButton("Lienzo Actual", QMessageBox.ButtonRole.ActionRole)
        m.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole); m.exec()
        if m.clickedButton() == bn: return "NEW"
        if m.clickedButton() == bc: return "CURRENT"
        return None

    def handle_new_flow(self):
        dest = self._ask_destination("Nuevo Flujo")
        if dest == "NEW": self.new_tab()
        elif dest == "CURRENT":
            t = self._current_tab()
            if t: t.push_undo(); t.model._add_default_trigger(); t.render()

    def import_json(self):
        f, _ = QFileDialog.getOpenFileName(self, "Abrir", "", "JSON (*.json)")
        if f: self.new_tab(f)
    def save_current(self):
        tab = self._current_tab()
        if not tab: return
        path = tab._file_path or QFileDialog.getSaveFileName(self, "Guardar", "", "JSON (*.json)")[0]
        if path: tab.model.save_json(path); tab._file_path = path; config.add_recent_file(path)
    def update_recent(self):
        self.rm.clear()
        for f in config.get_recent_files(): self.rm.addAction(os.path.basename(f)).triggered.connect(lambda _, p=f: self.new_tab(p))
    def export_png(self):
        t = self._current_tab()
        if not t: return
        f, _ = QFileDialog.getSaveFileName(self, "PNG", "", "*.png")
        if f: img = QImage(t.canvas.scene.sceneRect().size().toSize(), QImage.Format.Format_ARGB32); img.fill(QColor(20, 22, 27)); p = QPainter(img); t.canvas.scene.render(p); p.end(); img.save(f)
    def export_pdf(self):
        t = self._current_tab(); f, _ = QFileDialog.getSaveFileName(self, "PDF", "", "*.pdf")
        if t and f and QPrinter: pr = QPrinter(); pr.setOutputFileName(f); p = QPainter(pr); t.canvas.scene.render(p); p.end()
    
    def run_ai_task(self, target_tab, cb, method, *args):
        if target_tab: target_tab.log("⏳ Procesando... Por favor espera.")
        self.progress.show(); self.progress.setRange(0, 0)
        self.worker = AIWorker(method, *args)
        def _on_finish(r):
            self.progress.hide()
            if r.startswith("ERROR:"):
                if target_tab: target_tab.log(f"🧠 Gemini: {r}")
                return
            if cb: cb(r)
        self.worker.finished.connect(_on_finish); self.worker.start()

    def ask_ai(self):
        t = self._current_tab()
        if not t: return
        p = t.ai_in.text().strip(); t.ai_in.clear()
        if not p: return
        t.log(f"👤 Tú: {p}"); ctx = [{"id": n.id, "name": n.name} for n in t.model.nodes.values()]
        self.run_ai_task(t, lambda r: t.log(f"🏗️ MAXI AI ARCHITECT: {self._process_ai_cmds(r, t)}"), self.ai.ask, p, ctx)

    def import_doc_ai(self):
        dest = self._ask_destination("IA Doc Import")
        if not dest: return
        target_tab = self._current_tab() if dest == "CURRENT" else None
        
        fs, _ = QFileDialog.getOpenFileNames(self, "Docs", "", "*.pdf *.docx *.txt")
        if fs:
            if not target_tab:
                name = os.path.basename(fs[0]) if len(fs)==1 else "Importación AI"
                self.new_tab() # Standard new
                target_tab = self._current_tab()
                idx = self.tabs.indexOf(target_tab)
                if idx>=0: self.tabs.setTabText(idx, name)
                target_tab.model.name = name
                # Ensure we have a trigger and clear others
                target_tab.model.nodes = {}
                target_tab.model._add_default_trigger()
            
            target_tab.log("🔍 MAXI AI ARCHITECT está analizando el documento..."); self.doc_list.clear()
            for f in fs: self.doc_list.addItem(os.path.basename(f))
            txt = DocParser.extract_text(fs); self.last_doc_context = txt
            target_tab.log("📝 Generando resumen lógico del proceso...")
            self.run_ai_task(target_tab, self._on_summary_ready, self.ai.prepare_summary, txt)

    def _on_summary_ready(self, s):
        t = self._current_tab()
        if not t: return
        def _cb(r):
            if t: t.log(f"✅ MAXI AI ARCHITECT: {self._process_ai_cmds(r, t)}")
        if AIConfirmationDialog(s, self).exec():
            ctx = [{"id": n.id, "name": n.name} for n in t.model.nodes.values()]
            t.log("🏗️ MAXI AI ARCHITECT está trazando el mapa de nodos técnicos...")
            self.run_ai_task(t, _cb, self.ai.generate_from_summary, s, self.last_doc_context, ctx)

    def _process_ai_cmds(self, text, tab):
        if not tab: return text
        try:
            # 🛡️ STRICT SCANNER: Only look for [[COMMANDS: [...] ]]
            found_json = ""
            match = re.search(r"\[\[COMMANDS:\s*(.*?)\]\]", text, re.DOTALL)
            if match: found_json = match.group(1)
            else:
                # Fallback to the first list if strictly no metadata
                match_list = re.search(r"(\[.*?\])", text, re.DOTALL)
                if match_list: found_json = match_list.group(1)
            
            if not found_json: return text
            
            repaired = repair_json(found_json)
            if not repaired: return text
            obj = json.loads(repaired)
            clean_blocks = obj if isinstance(obj, list) else []
            if isinstance(obj, dict):
                clean_blocks = obj.get("workflow", obj.get("commands", []))
            
            if clean_blocks:
                # Normalizing name map for fuzzy matching (fallback)
                def norm(s): return str(s).strip().lower().replace("_","").replace("-","")
                
                # First pass: map AI IDs to real IDs or keep them if they are clean
                ai_to_real_id = {}
                for c in clean_blocks:
                    ai_id = str(c.get("id")) if c.get("id") else None
                    if ai_id:
                        # Create a unique but traceable ID
                        real_id = f"ia_{ai_id}" if not ai_id.startswith("ia_") else ai_id
                        ai_to_real_id[ai_id] = real_id
                
                # Second pass: Create nodes
                added_count = 0
                for c in clean_blocks:
                    ai_id = str(c.get("id")) if c.get("id") else None
                    if not ai_id: ai_id = f"gen_{uuid.uuid4().hex[:4]}"
                    
                    nid = ai_to_real_id.get(ai_id, ai_id)
                    p_ref = str(c.get("parentId")) if c.get("parentId") else None
                    
                    # Resolve parentId using the map
                    p_id = ai_to_real_id.get(p_ref, p_ref)
                    
                    # 🛡️ ANTI-ORPHAN: If no parent, connect to trigger_start
                    if not p_id: p_id = "trigger_start"
                    
                    # Fuzzy match if parentId is not in our new set (maybe it refers to an existing node)
                    if p_ref and p_id not in tab.model.nodes and not p_id.startswith("ia_"):
                        # Try to find by name in existing model
                        for ex_n in tab.model.nodes.values():
                            if norm(ex_n.name) == norm(p_ref):
                                p_id = ex_n.id; break
                    
                    added_count += 1
                    tab.model.nodes[nid] = WorkflowNode({
                        "id": nid, "parentId": p_id,
                        "branchLabel": c.get("branchLabel"),
                        "type": c.get("type", "sendMessage"), "name": c.get("name", f"Nodo {ai_id}"),
                        "data": c.get("node_data", c.get("data", {}))
                    })
                
                LayoutEngine().apply_tree_layout(tab.model); tab.render()
                return f"[Éxito: {added_count} nodos procesados correctamente]"
        except Exception as e: print(f"Deep Scan Error: {e}")
        return text

class PropertyPanelWidget(QWidget):
    def __init__(self, main_win):
        super().__init__(); self.mw = main_win; self.node = None; self.tab = None; l = QVBoxLayout(self); f = QFormLayout()
        self.id_in = QLineEdit(); self.id_in.setReadOnly(True); f.addRow("ID:", self.id_in)
        self.name_in = QLineEdit(); f.addRow("Nombre:", self.name_in)
        self.type_sel = QComboBox(); self.type_sel.addItems(NODE_TYPES.keys()); f.addRow("Tipo:", self.type_sel)
        self.text_in = QTextEdit(); self.text_in.setFixedHeight(120); f.addRow("Texto:", self.text_in)
        self.parent_in = QLineEdit(); f.addRow("Padre ID:", self.parent_in)
        self.branch_in = QLineEdit(); f.addRow("Etiqueta Rama:", self.branch_in)
        l.addLayout(f); btn = QPushButton("✅ Aplicar Cambios"); btn.setObjectName("btn_save"); btn.clicked.connect(self.apply); l.addWidget(btn); l.addStretch(); self.setEnabled(False)
    def load_node(self, node, tab):
        self.node = node; self.tab = tab; self.id_in.setText(node.id or ""); self.name_in.setText(node.name or "")
        self.type_sel.setCurrentText(node.type or "sendMessage"); self.parent_in.setText(str(node.parentId or ""))
        self.branch_in.setText(node.branchLabel or "")
        def find_text(obj):
            if not isinstance(obj, dict): return ""
            if "text" in obj: return str(obj["text"])
            for v in obj.values():
                if isinstance(v, list) and v: res = find_text(v[0]); return res
                if isinstance(v, dict): res = find_text(v); return res
            return ""
        self.text_in.setPlainText(find_text(node.data_payload or {})); self.setEnabled(True)
    def apply(self):
        if not self.node or not self.tab: return
        self.tab.push_undo()
        self.node.name = self.name_in.text(); self.node.type = self.type_sel.currentText()
        self.node.parentId = self.parent_in.text() if self.parent_in.text() else None
        self.node.branchLabel = self.branch_in.text()
        self.node.data_payload = {"payload": [{"message": {"text": self.text_in.toPlainText()}}]}
        self.tab.render()

class AIArchitectWidget(QWidget):
    def __init__(self, main_win):
        super().__init__(); self.mw = main_win; l = QVBoxLayout(self)
        self.log = QTextEdit(); self.log.setReadOnly(True); self.log.setObjectName("console"); l.addWidget(self.log)
        self.inp = QPlainTextEdit(); self.inp.setPlaceholderText("Pregunta a Jarvis sobre este flujo..."); self.inp.setFixedHeight(100); l.addWidget(self.inp)
        btn = QPushButton("🧠 Consultar a Jarvis"); btn.setObjectName("btn_ai"); btn.clicked.connect(self.send); l.addWidget(btn)
    def send(self):
        t = self.mw._current_tab(); p = self.inp.toPlainText().strip()
        if not t or not p: return
        self.log.append(f"<b>👤 Tú:</b> {p}"); self.inp.clear()
        ctx = [{"id": n.id, "name": n.name} for n in t.model.nodes.values()]
        self.mw.run_ai_task(t, lambda r: self.log.append(f"<b>🧠 Jarvis:</b> {self.mw._process_ai_cmds(r, t)}"), self.mw.ai.ask, p, ctx)

if __name__ == "__main__":
    app = QApplication(sys.argv); window = MainWindow(); window.show(); sys.exit(app.exec())
