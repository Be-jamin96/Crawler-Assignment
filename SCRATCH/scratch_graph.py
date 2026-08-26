import queue
import random
import threading
import time
import dearpygui.dearpygui as dpg

# Thread-safe queue for communication between background processing and UI
processing_queue = queue.Queue()


def background_processor():
    """Simulates real-time processing that generates nodes and changes their states."""
    node_counter = 1

    # Create initial nodes
    while node_counter <= 3:
        processing_queue.put({"action": "add", "id": node_counter, "label": f"Task {node_counter}"})
        node_counter += 1
        time.sleep(1)

    # Continuously simulate processing updates (adding/updating nodes)
    while True:
        time.sleep(1.5)
        event_type = random.choice(["add", "update"])

        if event_type == "add":
            processing_queue.put({"action": "add", "id": node_counter, "label": f"Task {node_counter}"})
            node_counter += 1
        else:
            # Update a random existing node's state/color
            target_id = random.randint(1, node_counter - 1)
            new_state = random.choice(["running", "success", "failed"])
            processing_queue.put({"action": "update", "id": target_id, "state": new_state})


def process_queue_items():
    """Polls the queue every frame to update the UI dynamically."""
    while not processing_queue.empty():
        msg = processing_queue.get()

        if msg["action"] == "add":
            nid = msg["id"]
            # Dynamically add a node to the node editor
            with dpg.node(label=msg["label"], tag=f"node_{nid}", parent="node_editor"):
                with dpg.node_attribute(tag=f"attr_{nid}", attribute_type=dpg.mvNode_Attr_Static):
                    dpg.add_text(f"State: Idle", tag=f"text_{nid}")

        elif msg["action"] == "update":
            nid = msg["id"]
            state = msg["state"]

            # Update text description
            if dpg.does_item_exist(f"text_{nid}"):
                dpg.set_value(f"text_{nid}", f"State: {state.upper()}")

            # Change node color based on state using custom themes
            color_map = {
                "running": (255, 165, 0, 255),  # Orange
                "success": (0, 255, 0, 255),  # Green
                "failed": (255, 0, 0, 255)  # Red
            }

            # Apply theme color change dynamically if node exists
            if dpg.does_item_exist(f"node_{nid}"):
                with dpg.theme(tag=f"theme_{nid}_{state}") as theme_id:
                    with dpg.theme_component(dpg.mvAll):
                        dpg.add_theme_color(dpg.mvNodeCol_NodeBackground, color_map[state],
                                            category=dpg.mvThemeCat_Nodes)
                dpg.bind_item_theme(f"node_{nid}", theme_id)


# --- UI Initialization ---
dpg.create_context()
dpg.create_viewport(title="Real-Time Node Graph", width=800, height=600)

with dpg.window(label="Graph Visualizer", width=800, height=600):
    with dpg.node_editor(tag="node_editor", callback=lambda s, a: None):
        pass  # Nodes will be injected here dynamically

# Start background processing thread
t = threading.Thread(target=background_processor, daemon=True)
t.start()

dpg.setup_dearpygui()
dpg.show_viewport()

# Main render loop
while dpg.is_dearpygui_running():
    process_queue_items()  # Pull latest backend updates each frame
    dpg.render_dearpygui_frame()

dpg.destroy_context()