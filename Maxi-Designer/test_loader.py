import json
import os
from models import WorkflowModel, WorkflowNode
from engine import LayoutEngine

def test_load():
    model = WorkflowModel()
    test_json = "test_flow.json"
    print(f"Loading {test_json}...")
    try:
        model.load_json(test_json)
        print(f"Model loaded. Nodes: {len(model.nodes)}")
        
        engine = LayoutEngine()
        engine.apply_tree_layout(model)
        print("Layout applied.")
        
        for nid, node in model.nodes.items():
            print(f"Node {nid}: ({node.x}, {node.y}) parent={node.parentId}")
            
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_load()
