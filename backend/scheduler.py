import json
from sqlalchemy.orm import Session
from backend.models import Task, TaskChain, TaskChainEdge
from backend.crud import update_task_status

class MockExecutor:
    def execute(self, input_json: dict) -> dict:
        return {"ok": True, "result": "mock result", "echo": input_json}

class MinimalScheduler:
    def __init__(self, db: Session):
        self.db = db
        self.executor = MockExecutor()

    def submit_task(self, task_id: int):
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False
        
        # Check if parent tasks are completed successfully
        if task.parent_task_id:
            parent = self.db.query(Task).filter(Task.id == task.parent_task_id).first()
            if not parent or parent.status != "success":
                # Cannot run if parent is not success
                return False
        
        if task.status != "pending":
            return False
        
        # For simplicity, we just mark it as running immediately and then run it
        return self.run_task_once(task_id)

    def run_task_once(self, task_id: int):
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task or task.status != "pending":
            return False
            
        try:
            update_task_status(self.db, task.id, "running")
            # Execute mock
            result = self.executor.execute(task.input_json or {})
            self.mark_task_success(task.id, result)
            return True
        except Exception as e:
            self.mark_task_failed(task.id, str(e))
            return False

    def mark_task_success(self, task_id: int, output_json: dict):
        update_task_status(self.db, task_id, "success", output_json=output_json)

    def mark_task_failed(self, task_id: int, error_message: str):
        update_task_status(self.db, task_id, "failed", error_message=error_message)

    def run_chain_once(self, chain_id: int):
        # Very minimal chain run: find pending tasks with no parents OR with completed parents
        tasks = self.db.query(Task).filter(Task.chain_id == chain_id, Task.status == "pending").all()
        ran_any = False
        for task in tasks:
            can_run = True
            
            # Check edge dependencies (this task is 'to_task_id')
            edges = self.db.query(TaskChainEdge).filter(TaskChainEdge.to_task_id == task.id).all()
            for edge in edges:
                parent = self.db.query(Task).filter(Task.id == edge.from_task_id).first()
                if not parent or parent.status != "success":
                    can_run = False
                    break
                    
            if can_run:
                self.run_task_once(task.id)
                ran_any = True
                
        # Update chain status if all tasks are success
        all_tasks = self.db.query(Task).filter(Task.chain_id == chain_id).all()
        if all_tasks and all(t.status == "success" for t in all_tasks):
            chain = self.db.query(TaskChain).filter(TaskChain.id == chain_id).first()
            if chain:
                chain.status = "completed"
                self.db.commit()
                
        return ran_any
