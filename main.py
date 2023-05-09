import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QGraphicsScene, QGraphicsView, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QInputDialog
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPen, QColor, QFont

class Graph:
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, label):
        self.nodes[label] = {}
        self.edges[label] = {}

    def add_edge(self, start_node, end_node, weight):
        if start_node in self.nodes and end_node in self.nodes:
            self.edges[start_node][end_node] = weight
            self.nodes[start_node][end_node] = weight

    def get_node_positions(self, k=5):
        return {
            node: QPointF(100 + 150 * (i % k), 100 + 150 * (i // k))
            for i, node in enumerate(self.nodes)
        }

    def adjacency_matrix(self):
        nodes = list(self.nodes.keys())
        return [
            [
                self.nodes[start][end] if end in self.nodes[start] else 0
                for end in nodes
            ]
            for start in nodes
        ]

    def from_adjacency_dict(self, adjacency_dict):
        self.nodes = {node: {} for node in adjacency_dict.keys()}
        self.edges = {node: {} for node in adjacency_dict.keys()}
        for start_node, neighbors in adjacency_dict.items():
            for end_node, weight in neighbors.items():
                if weight > 0:
                    self.add_edge(start_node, end_node, weight)

class GraphEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.graph = Graph()

        self.init_ui()
        self.resize(800, 600)

    def init_ui(self):
        self.setWindowTitle('Визуальный редактор графов')

        menubar = self.menuBar()
        file_menu = menubar.addMenu('Файл')

        add_node_action = QAction('Добавить вершину', self)
        add_node_action.triggered.connect(self.add_node)
        file_menu.addAction(add_node_action)

        add_edge_action = QAction('Добавить ребро', self)
        add_edge_action.triggered.connect(self.add_edge)
        file_menu.addAction(add_edge_action)

        copy_matrix_action = QAction('Копировать матрицу смежности', self)
        copy_matrix_action.triggered.connect(self.copy_adjacency_matrix)
        file_menu.addAction(copy_matrix_action)

        paste_graph_action = QAction('Вставить граф из JSON', self)
        paste_graph_action.triggered.connect(self.paste_graph_from_json)
        file_menu.addAction(paste_graph_action)

        dijkstra_action = QAction('Алгоритм Дейкстры', self)
        dijkstra_action.triggered.connect(self.run_dijkstra_algorithm)
        file_menu.addAction(dijkstra_action)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setScene(self.scene)
        self.setCentralWidget(self.view)

    def add_node(self):
        label, ok = QInputDialog.getText(self, "Добавить вершину", "Введите метку вершины:")

        if ok and label:
            self.graph.add_node(label)
            self.draw_graph()

    def add_edge(self):
        nodes = list(self.graph.nodes.keys())
        if len(nodes) < 2:
            QMessageBox.warning(self, "Внимание", "Нужно хотя бы 2 вершины для добавления ребра.")
            return

        start_node, ok1 = QInputDialog.getItem(self, "Добавить ребро", "Выберите начальную вершину:", nodes, 0, False)
        if ok1:
            end_node, ok2 = QInputDialog.getItem(self, "Добавить ребро", "Выберите конечную вершину:", nodes, 0, False)
            if ok2:
                weight, ok3 = QInputDialog.getDouble(self, "Добавить ребро", "Введите вес ребра:", 1, 1, 100, 1)
                if ok3:
                    self.graph.add_edge(start_node, end_node, weight)
                    self.draw_graph()

    def draw_graph(self, path_labels=None):
        self.scene.clear()
        node_radius = 20
        pos = self.graph.get_node_positions()

        for node, position in pos.items():
            x, y = position.x(), position.y()
            circle = self.scene.addEllipse(x, y, 2 * node_radius, 2 * node_radius, QPen(Qt.black), QColor("orange"))
            text = self.scene.addText(node, QFont("Arial", node_radius))
            text.setPos(x + node_radius / 2, y + node_radius / 2)
            pos[node] = QPointF(x, y)

        for start, neighbors in self.graph.edges.items():
            for end, weight in neighbors.items():
                start_pos = pos[start] + QPointF(node_radius, node_radius)
                end_pos = pos[end] + QPointF(node_radius, node_radius)
                line = self.scene.addLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y(), QPen(Qt.black, 2))

                weight_text = self.scene.addText(str(weight), QFont("Arial", 10))
                weight_text.setPos((start_pos + end_pos) / 2)
                if path_labels is not None:
                    for node, (distance, prev_node) in path_labels.items():
                        x, y = pos[node].x(), pos[node].y()
                        offset_x, offset_y = -60, -40  # Задаем смещение меток относительно вершины

                        # Изменяем формат метки на [расстояние; пред. вершина]
                        label_text = self.scene.addText(f"[{distance}; {prev_node}]", QFont("Arial", 10))
                        label_text.setPos(x + offset_x, y + offset_y)

    def copy_adjacency_matrix(self):
        adjacency_matrix = self.graph.adjacency_matrix()
        nodes = list(self.graph.nodes.keys())
        adjacency_dict = {nodes[i]: {nodes[j]: adjacency_matrix[i][j] for j in range(len(nodes))} for i in range(len(nodes))}

        json_matrix = json.dumps(adjacency_dict, indent=4)
        clipboard = QApplication.clipboard()
        clipboard.setText(json_matrix)

        QMessageBox.information(self, "Скопировано", "Матрица смежности")
    def paste_graph_from_json(self):
        clipboard = QApplication.clipboard()
        json_str = clipboard.text()

        try:
            self.paste_graph(json_str)
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Ошибка", "Невозможно вставить граф: некорректный JSON-формат.")

    def paste_graph(self, json_str):
        adjacency_dict = json.loads(json_str)
        self.graph.clear()
        self.graph.add_nodes_from(adjacency_dict.keys())

        for node, neighbors in adjacency_dict.items():
            for neighbor, weight in neighbors.items():
                if weight > 0:
                    self.graph.add_edge(node, neighbor, weight)

        self.draw_graph()
        QMessageBox.information(self, "Вставлено", "Граф успешно вставлен из буфера обмена в формате JSON.")

    def dijkstra_algorithm(self, start_node):
        path_labels = {node: (0 if node == start_node else float("inf"), "") for node in self.graph.nodes}

        unvisited_nodes = set(self.graph.nodes.keys())

        current_node = start_node
        while unvisited_nodes:
            # Update labels for neighbors
            for neighbor, weight in self.graph.edges[current_node].items():
                distance = path_labels[current_node][0] + weight
                if distance < path_labels[neighbor][0]:
                    path_labels[neighbor] = (distance, current_node)

            # Mark current node as visited
            unvisited_nodes.remove(current_node)

            if candidates := [
                (node, label[0])
                for node, label in path_labels.items()
                if node in unvisited_nodes
            ]:
                current_node, _ = min(candidates, key=lambda x: x[1])

            else:
                break

        return path_labels

    def run_dijkstra_algorithm(self):
        start_node, ok = QInputDialog.getItem(self, "Алгоритм Дейкстры", "Выберите начальную вершину:", list(self.graph.nodes.keys()), 0, False)

        if ok:
            path_labels = self.dijkstra_algorithm(start_node)
            self.draw_graph(path_labels)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    graph_editor = GraphEditor()
    graph_editor.show()
    sys.exit(app.exec_())
