import sys
import json
import os
import uuid
import copy
import re
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsPathItem, QGraphicsRectItem, QGraphicsTextItem, QVBoxLayout,
    QHBoxLayout, QWidget, QPushButton, QLineEdit, QTextEdit, QLabel,
    QFileDialog, QDialog, QComboBox, QFormLayout, QMenu, QMessageBox,
    QScrollArea, QFrame, QGridLayout, QDialogButtonBox, QTabWidget,
    QSplitter, QSizePolicy, QGroupBox, QListWidget, QMenuBar, QProgressBar,
    QGraphicsEllipseItem
)
from PyQt6.QtGui import (
    QPainter, QPainterPath, QColor, QPen, QBrush, QFont,
    QLinearGradient, QImage, QKeySequence, QShortcut, QPolygonF, QAction
)
from PyQt6.QtCore import Qt, QPointF, QRectF, QSize, QTimer, QThread, pyqtSignal
try: from PyQt6.QtPrintSupport import QPrinter
except ImportError: QPrinter = None

from constants import NODE_TYPES, DEFAULT_NODE_COLOR
from models import WorkflowNode, WorkflowModel, HistoryManager
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
QSplitter::handle { background: #2a2a3e; width: 2px; }
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
QLabel#sidebar_title { color: #61afef; font-size: 22px; font-weight: bold; letter-spacing: 4px; padding: 15px 0; border-bottom: 2px solid #2a2a3e; margin-bottom: 15px; }
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
    if node.type == "branch" and "conditions" in d and isinstance(d["conditions"], list) and len(d["conditions"]) > 0:
        c = d["conditions"][0]; return f"IF {c.get('variable','v')} {c.get('operator','==')} {c.get('value','val')}"
    if "options" in d and isinstance(d["options"], list):
        opts = [str(o.get("label", "")) for o in d["options"] if isinstance(o, dict)]
        return "OPC: " + ", ".join(opts)[:80]
    return ""

def repair_json(s):
    if not s: return ""
    s = s.strip()
    idx = -1
    for i, c in enumerate(s):
        if c in "{[": idx = i; break
    if idx == -1: return ""
    s = s[idx:]
    stk = []; last_bal = 0
    for i, c in enumerate(s):
        if c in "{[": stk.append(c)
        elif c in "}]":
            if stk:
                pairs = {"}":"{", "]":"["}
                if stk[-1] == pairs[c]: stk.pop(); 
                if not stk: last_bal = i + 1
    if last_bal > 0: s = s[:last_bal]
    # Balance final
    stk = []
    for c in s:
        if c in "{[": stk.append(c)
        elif c in "}]" and stk: stk.pop()
    cl = {"{":"}", "[":"]"}
    while stk: s += cl[stk.pop()]
    return s

class AIWorker(QThread):
    finished = pyqtSignal(str)
    def __init__(self, ai, prompt, current_json, system_override=None):
        super().__init__(); self.ai, self.prompt, self.current_json, self.system_override = ai, prompt, current_json, system_override
    def run(self):
        try: res = self.ai.ask(self.prompt, self.current_json, self.system_override); self.finished.emit(res)
        except Exception as e: self.finished.emit(str(e))

class NodeEditDialog(QDialog):
    def __init__(self, node, parent=None):
        super().__init__(parent); self.setWindowTitle(f"Editar: {node.type}"); self.node = node; lay = QFormLayout(self)
        self.setStyleSheet("background:#1a1a2e; color:white; font-family: Segoe UI;")
        self.name_in = QLineEdit(node.name); lay.addRow("Nombre:", self.name_in)
        self.text_in = QTextEdit(get_node_comment(node)); lay.addRow("Texto:", self.text_in)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); lay.addWidget(bb)
    def save(self):
        self.node.name = self.name_in.text()
        self.node.data_payload["payload"] = [{"message": {"text": self.text_in.toPlainText()}}]

class ConnectionCircle(QGraphicsEllipseItem):
    def __init__(self, parent_node):
        super().__init__(-8, -8, 16, 16, parent_node)
        self.setBrush(QBrush(QColor(80, 250, 123)))
        self.setPen(QPen(Qt.GlobalColor.white, 2))
        self.setPos(0, 50); self.setAcceptHoverEvents(True); self.setCursor(Qt.CursorShape.PointingHandCursor)
    def mousePressEvent(self, e):
        view = self.scene().views()[0] if self.scene().views() else None
        if view: view.start_linking(self.parentItem())

class NodeItem(QGraphicsItem):
    def __init__(self, node: WorkflowNode, on_action=None):
        super().__init__(); self.node = node; self.on_action = on_action; self.width, self.height = 220, 100
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.connections = []; self.setPos(float(node.x), float(node.y))
        self.handle = ConnectionCircle(self); self.handle.setVisible(False)
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
    def boundingRect(self): return QRectF(-self.width/2-10, -self.height/2-10, self.width+20, self.height+20)
    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = {"sendMessage": QColor(97, 175, 239), "askQuestion": QColor(198, 120, 221), "branch": QColor(229, 192, 123), "wait": QColor(209, 154, 102), "trigger": QColor(152, 195, 121), "jumpTo": QColor(224, 108, 117)}
        c = colors.get(self.node.type, QColor(171, 178, 191)); r = QRectF(-self.width/2, -self.height/2, self.width, self.height)
        if self.isSelected(): painter.setPen(QPen(c.lighter(130), 4)); painter.drawRoundedRect(r.adjusted(-3,-3,3,3), 12, 12)
        grad = QLinearGradient(0, -self.height/2, 0, self.height/2); grad.setColorAt(0, QColor(40, 44, 52)); grad.setColorAt(1, QColor(30, 33, 40))
        painter.setBrush(grad); painter.setPen(QPen(c.darker(120), 2)); painter.drawRoundedRect(r, 10, 10)
        painter.setBrush(c.darker(150)); painter.drawRoundedRect(r.adjusted(0,0,0,-75), 10, 10)
        painter.setPen(Qt.GlobalColor.white); painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(r.adjusted(10, 5, -10, -10), Qt.AlignmentFlag.AlignTop, self.node.name or self.node.type)
        painter.setPen(QColor(171, 178, 191)); painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(r.adjusted(10, 35, -10, -10), Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap, get_node_comment(self.node))
    def mouseDoubleClickEvent(self, e):
        dlg = NodeEditDialog(self.node); 
        if dlg.exec(): dlg.save(); self.on_action("REFRESH", self.node)
    def contextMenuEvent(self, e):
        m = QMenu(); del_act = m.addAction("❌ Eliminar"); act = m.exec(e.screenPos())
        if act == del_act: self.on_action("DELETE", self.node)

class ConnectionItem(QGraphicsPathItem):
    def __init__(self, source, target):
        super().__init__(); self.source, self.target = source, target
        self.source.connections.append(self); self.target.connections.append(self); self.setZValue(-1); self.update_path()
    def update_path(self):
        p1 = self.source.mapToScene(QPointF(0, self.source.height/2)); p2 = self.target.mapToScene(QPointF(0, -self.target.height/2))
        path = QPainterPath(); mid_y = p1.y() + (p2.y()-p1.y())/2
        path.moveTo(p1); path.lineTo(p1.x(), mid_y); path.lineTo(p2.x(), mid_y); path.lineTo(p2); self.setPath(path); self.setPen(QPen(QColor(100, 110, 130), 2))

class FlowCanvas(QGraphicsView):
    def __init__(self, on_action=None, parent=None):
        super().__init__(parent); self.scene = QGraphicsScene(self); self.setScene(self.scene)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag); self.setBackgroundBrush(QBrush(QColor(20, 22, 27)))
        self.on_action = on_action; self.linking_from = None; self.temp_line = None
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
            if isinstance(item, NodeItem) and item != self.linking_from:
                item.node.parentId = self.linking_from.node.id; self.on_action("REFRESH", None, None)
            self.scene.removeItem(self.temp_line); self.temp_line = None; self.linking_from = None; self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        super().mouseReleaseEvent(e)
    def wheelEvent(self, e): f = 1.15 if e.angleDelta().y() > 0 else 1/1.15; self.scale(f, f)
    def contextMenuEvent(self, e):
        m = QMenu(); add_m = m.addMenu("➕ Agregar Nodo"); pos = self.mapToScene(e.pos())
        for q in ["sendMessage", "askQuestion", "branch", "wait", "jumpTo"]:
            a = add_m.addAction(q); a.triggered.connect(lambda _, xt=q, xp=pos: self.on_action("ADD", xt, xp))
        m.exec(e.screenPos())

class WorkflowTab(QWidget):
    def __init__(self, main_win, parent=None):
        super().__init__(parent); self.main_win = main_win; self.model = WorkflowModel(); self._file_path = None
        self.canvas = FlowCanvas(on_action=self.on_canvas_action, parent=self); lay = QVBoxLayout(self); lay.addWidget(self.canvas)
    def load(self, path):
        try: self._file_path = path; self.model.load_json(path); LayoutEngine().apply_tree_layout(self.model); self.render()
        except Exception as e: self.main_win.console.append(f"❌ Error: {e}")
    def render(self):
        self.canvas.scene.clear(); self.items = {}
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
    def on_canvas_action(self, action, data=None, pos=None):
        if action == "DELETE":
            if data.id in self.model.nodes: del self.model.nodes[data.id]; self.render()
        elif action == "ADD":
            nid = f"n_{uuid.uuid4().hex[:6]}"; new_n = WorkflowNode({"id": nid, "type": data, "name": f"Nuevo {data}", "x": pos.x(), "y": pos.y()})
            self.model.nodes[nid] = new_n; self.render()
        elif action == "REFRESH": self.render()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Maxi-Designer"); self.resize(1400, 900); self.ai = AIEngine(); self.last_doc_context = ""; self.init_ui(); self.setStyleSheet(GLOBAL_STYLE)
    def init_ui(self):
        mb = self.menuBar(); fm = mb.addMenu("Archivo")
        fm.addAction("Importar JSON", self.import_json); fm.addAction("💾 Guardar", self.save_current)
        self.rmp = fm.addMenu("Recientes"); self.rmp.aboutToShow.connect(self.update_recent)
        root = QWidget(); self.setCentralWidget(root); lay = QHBoxLayout(root); self.sp = QSplitter(Qt.Orientation.Horizontal); lay.addWidget(self.sp)
        sidebar = QFrame(); sidebar.setObjectName("sidebar"); sidebar.setMinimumWidth(320); sb = QVBoxLayout(sidebar); self.sp.addWidget(sidebar)
        lbl = QLabel("MAXI DESIGNER"); lbl.setObjectName("sidebar_title"); sb.addWidget(lbl)
        h1 = QHBoxLayout(); bi = QPushButton("Importar JSON"); bi.clicked.connect(self.import_json); h1.addWidget(bi)
        bs = QPushButton("💾 Guardar"); bs.clicked.connect(self.save_current); h1.addWidget(bs); sb.addLayout(h1)
        h2 = QHBoxLayout(); br = QPushButton("📂 Recientes"); self.rm = QMenu(self); br.setMenu(self.rm); self.rm.aboutToShow.connect(self.update_recent); h2.addWidget(br)
        be = QPushButton("📤 Exportar"); exm = QMenu(self); be.setMenu(exm); exm.addAction("PNG", self.export_png); exm.addAction("PDF", self.export_pdf); h2.addWidget(be); sb.addLayout(h2)
        ba = QPushButton("📄 IA Doc Import"); ba.setObjectName("btn_ai"); ba.clicked.connect(self.import_doc_ai); sb.addWidget(ba)
        brs = QPushButton("🧹 Reset / Borrado"); brs.setObjectName("btn_reset"); brs.clicked.connect(self.reset_flow); sb.addWidget(brs)
        gb = QGroupBox("Docs y Vista"); gbl = QHBoxLayout(gb); self.doc_list = QListWidget(); self.doc_list.setFixedHeight(120); gbl.addWidget(self.doc_list, 1)
        self.mini_map = QGraphicsView(); self.mini_map.setObjectName("minimap"); self.mini_map.setFixedHeight(120); gbl.addWidget(self.mini_map, 1); sb.addWidget(gb)
        self.console = QTextEdit(); self.console.setObjectName("console"); self.console.setReadOnly(True); sb.addWidget(self.console)
        self.progress = QProgressBar(); self.progress.hide(); sb.addWidget(self.progress)
        sb.addWidget(QLabel("<b>ASISTENTE IA</b>")); self.ai_in = QLineEdit(); self.ai_in.setPlaceholderText("Escribe un comando..."); self.ai_in.returnPressed.connect(self.ask_ai); sb.addWidget(self.ai_in)
        bc = QPushButton("⚙ Config Gemini"); bc.clicked.connect(lambda: SettingsDialog(self).exec()); sb.addWidget(bc)
        self.tabs = QTabWidget(); self.tabs.currentChanged.connect(self.update_minimap); self.sp.addWidget(self.tabs); self.new_tab()
        self.sp.setStretchFactor(0, 1); self.sp.setStretchFactor(1, 4)
    def update_minimap(self, idx=None):
        t = self._current_tab()
        if t and t.canvas.scene and t.canvas.scene.sceneRect().isValid(): self.mini_map.setScene(t.canvas.scene); QTimer.singleShot(100, lambda: self.mini_map.fitInView(t.canvas.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio))
    def reset_flow(self):
        t = self._current_tab()
        if t and QMessageBox.question(self, "Reset", "¿Borrar?") == QMessageBox.StandardButton.Yes: t.model = WorkflowModel(); t.render()
    def _current_tab(self): idx = self.tabs.currentIndex(); return self.tabs.widget(idx) if idx >= 0 else None
    def new_tab(self, path=None):
        t = WorkflowTab(self); self.tabs.addTab(t, os.path.basename(path) if path else "Nuevo")
        if path: t.load(path); config.add_recent_file(path)
        self.tabs.setCurrentWidget(t)
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
        for f in config.get_recent_files(): a = QAction(os.path.basename(f), self); a.triggered.connect(lambda _, p=f: self.new_tab(p)); self.rm.addAction(a)
    def export_png(self):
        t = self._current_tab()
        if not t: return
        f, _ = QFileDialog.getSaveFileName(self, "PNG", "", "*.png")
        if f: img = QImage(t.canvas.scene.sceneRect().size().toSize(), QImage.Format.Format_ARGB32); img.fill(QColor(20, 22, 27)); p = QPainter(img); t.canvas.scene.render(p); p.end(); img.save(f)
    def export_pdf(self):
        t = self._current_tab(); f, _ = QFileDialog.getSaveFileName(self, "PDF", "", "*.pdf")
        if t and f and QPrinter: pr = QPrinter(); pr.setOutputFileName(f); p = QPainter(pr); t.canvas.scene.render(p); p.end()
    def run_ai_task(self, p, c, s, cb):
        self.progress.show(); self.worker = AIWorker(self.ai, p, c, s)
        self.worker.finished.connect(lambda r: (self.progress.hide(), cb(r))); self.worker.start()
    def ask_ai(self):
        t = self._current_tab(); p = self.ai_in.text().strip(); self.ai_in.clear()
        if not p or not t: return
        self.console.append(f"👤 Tú: {p}"); ctx = [{"id": n.id, "name": n.name} for n in t.model.nodes.values()]
        self.run_ai_task(p, ctx, None, lambda r: self.console.append(f"🧠 Gemini: {self._process_ai_cmds(r, t)}"))
    def import_doc_ai(self):
        t = self._current_tab(); fs, _ = QFileDialog.getOpenFileNames(self, "Docs", "", "*.pdf *.docx *.txt")
        if fs and t:
            for f in fs: self.doc_list.addItem(os.path.basename(f))
            txt = DocParser.extract_text(fs); self.last_doc_context = txt
            self.run_ai_task(f"Analiza:\n{txt[:12000]}", {}, "Resume narrativamente.", self._on_summary_ready)
    def _on_summary_ready(self, s):
        def _cb(r): self.console.append(f"✅ Gemini: {self._process_ai_cmds(r, self._current_tab())}")
        if AIConfirmationDialog(s, self).exec(): self.run_ai_task("CREA EL FLUJO YA.", {}, None, _cb)
    def _process_ai_cmds(self, text, tab):
        cleaned = re.sub(r"\[\[\s*COMMANDS:\s*", "", text, flags=re.IGNORECASE)
        cleaned = re.sub(r"\]\s*\]", "]", cleaned); found = []
        for m in re.finditer(r"\[.*\]", cleaned, re.DOTALL):
            repaired = repair_json(m.group(0))
            try:
                data = json.loads(repaired); cmds = data if isinstance(data, list) else data.get("workflow", [])
                for c in cmds:
                    if isinstance(c, dict) and (c.get("action") == "ADD_NODE" or "type" in c): found.append(c)
            except: continue
        if found:
            for c in found:
                nid = c.get("id") or f"ia_{uuid.uuid4().hex[:6]}"
                node = WorkflowNode({"id": nid, "parentId": c.get("parentId"), "type": c.get("type", "sendMessage"), "name": c.get("name"), "data": c.get("node_data", c.get("data", {}))})
                tab.model.nodes[nid] = node
            LayoutEngine().apply_tree_layout(tab.model); tab.render(); return "[Flujo aplicado]"
        return text

if __name__ == "__main__":
    app = QApplication(sys.argv); window = MainWindow(); window.show(); sys.exit(app.exec())
