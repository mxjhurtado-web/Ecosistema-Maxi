import json
import os
from typing import List, Dict, Any, Optional

class WorkflowNode:
    def __init__(self, data: Dict[str, Any]):
        self.id: str = str(data.get("id")) if data.get("id") is not None else ""
        self.parentId: Optional[str] = str(data.get("parentId")) if data.get("parentId") is not None else None
        self.type: str = data.get("type", "unknown")
        self.name: str = data.get("name", "")
        # Resilient data capture for different Respond.io versions
        self.data_payload: Dict[str, Any] = data.get("data") or data.get("properties") or data.get("attributes") or data.get("params") or {}
        
        # Position for the UI
        self.x: float = 0.0
        self.y: float = 0.0
        
        # UI metadata
        self.children: List['WorkflowNode'] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "parentId": self.parentId,
            "type": self.type,
            "name": self.name,
            "data": self.data_payload
        }

class WorkflowModel:
    def __init__(self):
        self.id: Optional[str] = None
        self.name: str = "New Workflow"
        self.description: str = ""
        self.nodes: Dict[str, WorkflowNode] = {}
        self.root_node_ids: List[str] = []
        self.root_node_id: Optional[str] = None
        self.raw_data: Dict[str, Any] = {}

    def load_json(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.raw_data = data if isinstance(data, dict) else {}
        self.id = str(data.get("id")) if isinstance(data, dict) and data.get("id") is not None else None
        self.name = str(data.get("name", "Imported Flow")) if isinstance(data, dict) else "Imported Flow"
        
        workflow_data = []
        if isinstance(data, list):
            workflow_data = data
        elif isinstance(data, dict):
            workflow_data = data.get("workflow") or data.get("steps") or data.get("components") or []
            
        self.nodes = {}
        for node_data in workflow_data:
            if not isinstance(node_data, dict): continue
            node = WorkflowNode(node_data)
            if node.id:
                self.nodes[node.id] = node
        
        self.root_node_ids = []
        for node in self.nodes.values():
            node.children = []
            
        for nid, node in self.nodes.items():
            p_id = str(node.parentId) if node.parentId is not None else None
            if p_id and p_id in self.nodes and p_id != nid:
                parent = self.nodes[p_id]
                if node not in parent.children: parent.children.append(node)
            else:
                if nid not in self.root_node_ids: self.root_node_ids.append(nid)

        # Discovery for orphans
        orphan_roots = list(self.root_node_ids)
        for rid in orphan_roots:
            node = self.nodes[rid]
            if node.type == "trigger": continue
            found = False
            for potential_parent in self.nodes.values():
                def find_id_in_data(obj):
                    if isinstance(obj, str): return obj == rid
                    if isinstance(obj, list): return any(find_id_in_data(i) for i in obj)
                    if isinstance(obj, dict): return any(find_id_in_data(v) for v in obj.values())
                    return False
                if find_id_in_data(potential_parent.data_payload):
                    if node not in potential_parent.children: potential_parent.children.append(node)
                    if rid in self.root_node_ids: self.root_node_ids.remove(rid)
                    found = True; break
                    
        reachable = set()
        def mark_reachable(n_id):
            if n_id in reachable: return
            reachable.add(n_id)
            if n_id in self.nodes:
                for child in self.nodes[n_id].children: mark_reachable(child.id)
                
        priority_roots = [rid for rid in self.root_node_ids if self.nodes[rid].type == "trigger"]
        for r_id in priority_roots: mark_reachable(r_id)
        remaining_roots = [rid for rid in self.root_node_ids if rid not in reachable]
        for r_id in remaining_roots: mark_reachable(r_id)
        for nid in self.nodes:
            if nid not in reachable:
                self.root_node_ids.append(nid); mark_reachable(nid)

        self.root_node_ids.sort(key=lambda rid: 0 if self.nodes[rid].type == "trigger" else 1)
        if self.root_node_ids: self.root_node_id = self.root_node_ids[0]

    def save_json(self, file_path: str):
        workflow_list = [node.to_dict() for node in self.nodes.values()]
        output_data = self.raw_data.copy()
        output_data.update({"name": self.name, "workflow": workflow_list})
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
