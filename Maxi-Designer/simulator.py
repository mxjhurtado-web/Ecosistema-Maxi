from typing import Dict, Any, Optional, List
from models import WorkflowNode, WorkflowModel

class FlowSimulator:
    def __init__(self, model: WorkflowModel):
        self.model = model
        self.current_node: Optional[WorkflowNode] = None
        self.variables: Dict[str, Any] = {}
        self.history: List[str] = []
        self.is_running = False

    def start(self):
        try:
            # Prefer the first root in root_node_ids
            rid = getattr(self.model, "root_node_id", None)
            if not rid and getattr(self.model, "root_node_ids", []):
                rid = self.model.root_node_ids[0]
                
            if rid and rid in self.model.nodes:
                self.current_node = self.model.nodes[rid]
                self.is_running = True
                self.history = [f"Started workflow: {self.model.name}"]
                return self.get_current_status()
            
            # Fallback: find any node without parentId if root_node_ids is empty
            if not rid:
                for node in self.model.nodes.values():
                    if not node.parentId or node.parentId == "-1":
                        self.current_node = node
                        self.is_running = True
                        return self.get_current_status()
                        
            return "No root node found."
        except Exception as e:
            import traceback
            err = f"SIMULATOR START ERROR: {e}\n{traceback.format_exc()}"
            with open("crash_log.txt", "a") as f: f.write(err + "\n")
            return f"Error: {e}"

    def step(self, user_input: Optional[str] = None):
        if not self.is_running or not self.current_node:
            return "Simulator not running."

        # Process current node logic
        node = self.current_node
        log = f"Executing {node.type}: {node.name}"
        
        # Simple transition logic: follow first child unless specific type
        next_node = None
        
        if node.type == "askQuestion":
            if user_input is None:
                return f"WAITING_FOR_INPUT: {node.data_payload.get('question', {}).get('text')}"
            # Save response
            var_name = node.data_payload.get("saveResponse", {}).get("variable")
            if var_name:
                self.variables[var_name] = user_input
            
            # Find success connector
            for child in node.children:
                if child.type == "askQuestionConnector" and child.data_payload.get("connectorType") == "success":
                    next_node = child
                    break
        elif node.type == "branch":
            # Very simplified branch logic
            next_node = self.evaluate_branch(node)
        elif node.type == "jumpTo":
            step_id = node.data_payload.get("stepId")
            if step_id and str(step_id) in self.model.nodes:
                next_node = self.model.nodes[str(step_id)]
        else:
            if node.children:
                next_node = node.children[0]

        if next_node:
            self.current_node = next_node
            self.history.append(log)
            return self.get_current_status()
        else:
            self.is_running = False
            return "Workflow finished."

    def evaluate_branch(self, node: WorkflowNode) -> Optional[WorkflowNode]:
        # Simple evaluation logic
        for child in node.children:
            if child.type == "branchConnector":
                # Check conditions (simplified)
                return child
        return None

    def get_choices(self) -> List[Dict[str, str]]:
        if not self.current_node: return []
        choices = []
        for child in self.current_node.children:
            # Try to get a meaningful label from connectorType or name
            # connectorType is often "success", "failure", etc.
            ct = child.data_payload.get("connectorType", "")
            label = ct if ct else (child.name if child.name else "Siguiente")
            choices.append({"label": str(label).capitalize(), "id": str(child.id)})
        return choices

    def get_current_status(self):
        node = self.current_node
        status = f"Current Node: {node.name} ({node.type})\n"
        if node.type == "sendMessage":
            payload = node.data_payload.get("payload", [])
            for p in payload:
                status += f">> Message: {p.get('message', {}).get('text')}\n"
        elif node.type == "askQuestion":
            status += f">> Question: {node.data_payload.get('question', {}).get('text')}\n"
        
        status += f"Variables: {self.variables}"
        return status
