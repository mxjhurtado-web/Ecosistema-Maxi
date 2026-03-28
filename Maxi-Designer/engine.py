from typing import List, Dict, Any, Set
from models import WorkflowModel, WorkflowNode

class LayoutEngine:
    def __init__(self):
        self.spacing_h = 500
        self.spacing_v = 350

    def apply_tree_layout(self, model: WorkflowModel):
        if not model.nodes:
            return

        assigned = set()
        subtree_widths = {}

        def calculate_subtree_width(node):
            if node.id in subtree_widths: return subtree_widths[node.id]
            children = [c for c in node.children if c.id in model.nodes and c.id not in assigned]
            if not children:
                res = self.spacing_h
            else:
                w = sum(calculate_subtree_width(c) for c in children)
                gap_w = (len(children) - 1) * (self.spacing_h * 0.5)
                res = max(w + gap_w, self.spacing_h)
            subtree_widths[node.id] = res
            return res

        def layout_node_recursive(node, x, y):
            if node.id in assigned: return
            assigned.add(node.id)
            node.x, node.y = float(x), float(y)
            children = [c for c in node.children if c.id in model.nodes and c.id not in assigned]
            if not children: return
            total_w = calculate_subtree_width(node)
            current_x = x - total_w / 2
            for child in children:
                child_w = calculate_subtree_width(child)
                layout_node_recursive(child, current_x + child_w / 2, y + self.spacing_v)
                current_x += child_w

        # Identify roots: nodes with no parent in the current set
        all_ids = set(model.nodes.keys())
        has_parent = set()
        for n in model.nodes.values():
            if n.parentId and n.parentId in all_ids:
                has_parent.add(n.id)
        
        roots = [model.nodes[nid] for nid in all_ids if nid not in has_parent]
        roots.sort(key=lambda n: 0 if n.type == "trigger" else 1)

        current_x_cursor = 0.0
        for root in roots:
            if root.id not in assigned:
                w = calculate_subtree_width(root)
                layout_node_recursive(root, current_x_cursor + w / 2, 100.0)
                current_x_cursor += w + 600

        # Fallback grid for unassigned (should be empty if roots worked)
        unassigned = [n for n in model.nodes.values() if n.id not in assigned]
        if unassigned:
            cols = 6
            start_x = current_x_cursor + 400
            for i, n in enumerate(unassigned):
                n.x = start_x + (i % cols) * self.spacing_h
                n.y = 100.0 + (i // cols) * self.spacing_v
                assigned.add(n.id)
